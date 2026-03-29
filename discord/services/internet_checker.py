"""Internet availability checker using BroadbandNow.

Replaces the internet-checker agent. Uses Playwright to automate
BroadbandNow's address lookup with Google Places autocomplete.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Optional

from playwright.async_api import Browser, Page, async_playwright

import config
from utils.schemas import InternetData, InternetProvider, Listing, save_listings

logger = logging.getLogger(__name__)


class InternetChecker:
    """Check fiber/broadband availability for listing addresses."""

    def __init__(self):
        self._browser: Optional[Browser] = None
        self._playwright = None

    async def start(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)

    async def close(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def _new_page(self) -> Page:
        assert self._browser
        context = await self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        return await context.new_page()

    async def check_address(self, address: str) -> InternetData:
        """Check internet availability at a single address using BroadbandNow."""
        page = await self._new_page()
        try:
            await page.goto(config.BROADBANDNOW_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            # Find the address search input
            search_input = page.locator("input[type='text'], input[placeholder*='address'], input[name*='address']").first
            await search_input.click()
            await asyncio.sleep(0.5)

            # Type a short version of the address for autocomplete
            short_addr = self._shorten_address(address)
            await search_input.type(short_addr, delay=50)
            await asyncio.sleep(2)

            # Wait for and click autocomplete suggestion
            try:
                suggestion = page.locator(".pac-item, .autocomplete-item, [role='option']").first
                await suggestion.click(timeout=5000)
                await asyncio.sleep(3)
            except Exception:
                # If no autocomplete, press Enter
                await search_input.press("Enter")
                await asyncio.sleep(3)

            # Parse results page
            content = await page.content()
            return self._parse_results(content)

        except Exception as e:
            logger.error(f"BroadbandNow check failed for {address}: {e}")
            return InternetData(classification="check_failed")
        finally:
            await page.close()

    def _shorten_address(self, address: str) -> str:
        """Shorten address for BroadbandNow's autocomplete (Google Places API)."""
        # Remove state/zip suffix, keep street + city
        parts = address.split(",")
        if len(parts) >= 2:
            return f"{parts[0].strip()}, {parts[1].strip()}"
        return address[:40]

    def _parse_results(self, html: str) -> InternetData:
        """Parse BroadbandNow results page for provider data."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True).lower()

        data = InternetData()
        providers: list[dict] = []

        # Look for provider cards/rows
        for row in soup.select(".provider-card, .provider-row, tr, .isp-row"):
            row_text = row.get_text(" ", strip=True)
            name = ""
            speed = 0
            conn_type = ""
            price = None

            # Provider name
            name_el = row.select_one(".provider-name, .isp-name, td:first-child, strong")
            if name_el:
                name = name_el.get_text(strip=True)

            # Speed
            speed_match = re.search(r"(\d[\d,]*)\s*(?:mbps|gbps)", row_text, re.IGNORECASE)
            if speed_match:
                speed_val = float(speed_match.group(1).replace(",", ""))
                if "gbps" in speed_match.group().lower():
                    speed_val *= 1000
                speed = speed_val

            # Connection type
            for ct in ["fiber", "cable", "dsl", "5g", "fixed wireless", "satellite"]:
                if ct in row_text.lower():
                    conn_type = ct.capitalize()
                    break

            # Price
            price_match = re.search(r"\$(\d+(?:\.\d{2})?)", row_text)
            if price_match:
                price = float(price_match.group(1))

            if name and (speed or conn_type):
                providers.append({"name": name, "speed": speed, "type": conn_type, "price": price})

        data.providers_found = len(providers)

        # Map to known providers
        for p in providers:
            pname = p["name"].lower()
            provider = InternetProvider(
                available=True,
                fiber="fiber" in p["type"].lower() if p["type"] else False,
                max_down=p["speed"],
                connection=p["type"],
                price_from=p["price"],
            )
            if "quantum" in pname or ("centurylink" in pname and p.get("type", "").lower() == "fiber"):
                data.quantum_fiber = provider
                data.quantum_fiber.fiber = True
            elif "xfinity" in pname or "comcast" in pname:
                data.xfinity = provider
            elif "at&t" in pname or "att" in pname:
                data.att = provider
            elif "t-mobile" in pname or "tmobile" in pname:
                data.tmobile = provider
            elif "centurylink" in pname or "lumen" in pname:
                data.centurylink = provider

        # Build summary
        parts = []
        if data.providers_found:
            parts.append(f"{data.providers_found} providers.")
            fiber_providers = [p["name"] for p in providers if "fiber" in (p.get("type") or "").lower()]
            if fiber_providers:
                parts.append(f"Fiber: {', '.join(fiber_providers)}.")
        data.broadbandnow_summary = " ".join(parts) if parts else "No data available."

        # Classify
        data.classification = self._classify(data, providers)
        return data

    def _classify(self, data: InternetData, providers: list[dict]) -> str:
        """Classify internet quality: Excellent, Good, Adequate, Poor."""
        max_speed = max((p["speed"] for p in providers), default=0)
        has_fiber = any("fiber" in (p.get("type") or "").lower() for p in providers)

        if has_fiber and max_speed >= 940:
            return "Excellent"
        if max_speed >= 1000:
            return "Good"
        if max_speed >= 300:
            return "Adequate"
        return "Poor"

    async def check_listings(
        self,
        listings: list[Listing],
        progress_callback=None,
    ) -> list[Listing]:
        """Check internet for all listings. Parallel if 6+ listings."""
        total = len(listings)
        concurrency = 1 if total <= 5 else (2 if total <= 15 else 3)

        semaphore = asyncio.Semaphore(concurrency)
        checked = 0

        async def check_one(listing: Listing) -> Listing:
            nonlocal checked
            async with semaphore:
                if listing.address:
                    listing.internet = await self.check_address(listing.address)
                checked += 1
                if progress_callback:
                    await progress_callback(checked, total, listing.address)
                return listing

        tasks = [check_one(l) for l in listings]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        updated = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Internet check failed for {listings[i].id}: {result}")
                listings[i].internet = InternetData(classification="check_failed")
                updated.append(listings[i])
            else:
                updated.append(result)

        return updated
