"""Listing scraper service using Playwright for browser automation.

Replaces the apartment-finder agent. Scrapes rental and purchase listing sites
headlessly, extracting structured listing data.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from pathlib import Path
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import Browser, Page, async_playwright

import config
from services.deduplication import deduplicate_listings
from utils.schemas import (
    AlsoListedOn,
    LeaseTerms,
    Listing,
    PriceEvent,
    SaleTerms,
    save_listings,
)

logger = logging.getLogger(__name__)


class ListingScraper:
    """Headless browser scraper for Portland listing sites."""

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

    # ── Craigslist ──────────────────────────────────────────────────────

    async def scrape_craigslist_rentals(
        self, bedrooms: int = 2, max_price: Optional[float] = None, zips: Optional[list[str]] = None
    ) -> list[Listing]:
        """Scrape Craigslist Portland apartments."""
        listings: list[Listing] = []
        page = await self._new_page()
        try:
            params = f"min_bedrooms={bedrooms}&availabilityMode=0&sale_date=all+dates"
            if max_price:
                params += f"&max_price={int(max_price)}"
            for zip_code in (zips or config.PORTLAND_ZIPS[:4]):
                url = f"https://portland.craigslist.org/search/apa?postal={zip_code}&{params}"
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)

                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")

                for card in soup.select(".cl-static-search-result, .result-row, li.cl-search-result"):
                    try:
                        link = card.select_one("a[href]")
                        if not link:
                            continue
                        href = link.get("href", "")
                        if not href.startswith("http"):
                            href = f"https://portland.craigslist.org{href}"

                        title_el = card.select_one(".titlestring, .result-title, .title")
                        title = title_el.get_text(strip=True) if title_el else ""

                        price_el = card.select_one(".priceinfo, .result-price, .price")
                        price_text = price_el.get_text(strip=True) if price_el else ""
                        price_match = re.search(r"\$[\d,]+", price_text)
                        price = float(price_match.group().replace("$", "").replace(",", "")) if price_match else 0

                        lid = f"craigslist-{hashlib.md5(href.encode()).hexdigest()[:8]}"
                        listings.append(Listing(
                            id=lid,
                            source="craigslist",
                            url=href,
                            address=title,
                            price=price,
                            bedrooms=bedrooms,
                            listing_type="residential",
                        ))
                    except Exception as e:
                        logger.warning(f"Error parsing CL card: {e}")

        except Exception as e:
            logger.error(f"Craigslist scrape error: {e}")
        finally:
            await page.close()

        return listings

    async def scrape_craigslist_purchases(self, max_price: float = 700000) -> list[Listing]:
        """Scrape Craigslist Portland real estate for sale."""
        listings: list[Listing] = []
        page = await self._new_page()
        try:
            for zip_code in config.PORTLAND_ZIPS[:4]:
                url = f"https://portland.craigslist.org/search/rea?postal={zip_code}&max_price={int(max_price)}"
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)

                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")

                for card in soup.select(".cl-static-search-result, .result-row, li.cl-search-result"):
                    try:
                        link = card.select_one("a[href]")
                        if not link:
                            continue
                        href = link.get("href", "")
                        if not href.startswith("http"):
                            href = f"https://portland.craigslist.org{href}"

                        title_el = card.select_one(".titlestring, .result-title, .title")
                        title = title_el.get_text(strip=True) if title_el else ""

                        price_el = card.select_one(".priceinfo, .result-price, .price")
                        price_text = price_el.get_text(strip=True) if price_el else ""
                        price_match = re.search(r"\$[\d,]+", price_text)
                        price = float(price_match.group().replace("$", "").replace(",", "")) if price_match else 0

                        if price > max_price:
                            continue

                        lid = f"craigslist-{hashlib.md5(href.encode()).hexdigest()[:8]}"
                        listings.append(Listing(
                            id=lid,
                            source="craigslist",
                            url=href,
                            address=title,
                            price=price,
                            listing_type="residential",
                        ))
                    except Exception as e:
                        logger.warning(f"Error parsing CL purchase card: {e}")

        except Exception as e:
            logger.error(f"Craigslist purchase scrape error: {e}")
        finally:
            await page.close()

        return listings

    # ── Detail page enrichment ──────────────────────────────────────────

    async def enrich_listing(self, listing: Listing) -> Listing:
        """Visit a listing's detail page and extract additional data."""
        page = await self._new_page()
        try:
            await page.goto(listing.url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")

            # Extract full text for keyword matching
            text = soup.get_text(" ", strip=True).lower()

            # Address refinement
            addr_el = soup.select_one(".mapaddress, [data-testid='address'], .property-address")
            if addr_el:
                listing.address = addr_el.get_text(strip=True)

            # Bedrooms/bathrooms
            for pattern in [r"(\d+)\s*(?:bed|br|bedroom)", r"(\d+)bd"]:
                m = re.search(pattern, text)
                if m and not listing.bedrooms:
                    listing.bedrooms = int(m.group(1))
            for pattern in [r"(\d+)\s*(?:bath|ba|bathroom)", r"(\d+)ba"]:
                m = re.search(pattern, text)
                if m and not listing.bathrooms:
                    listing.bathrooms = int(m.group(1))

            # Square footage
            for pattern in [r"(\d{3,5})\s*(?:sq\s*ft|sqft|square feet)"]:
                m = re.search(pattern, text)
                if m and not listing.sqft:
                    listing.sqft = int(m.group(1))

            # Kitchen detection
            if "full kitchen" in text or "kitchen with" in text:
                listing.has_kitchen = True
            elif "kitchenette" in text:
                listing.has_kitchenette = True

            # Mixed-use keywords
            mixed_keywords = ["live/work", "live-work", "mixed use", "mixed-use", "commercial", "office space", "retail"]
            if any(kw in text for kw in mixed_keywords):
                listing.listing_type = "mixed-use"

            # Amenities
            amenity_keywords = [
                "dishwasher", "laundry in unit", "washer/dryer", "parking", "garage",
                "balcony", "patio", "hardwood", "ac", "air conditioning", "fireplace",
                "storage", "elevator", "gym", "pool", "rooftop", "ev charging",
            ]
            listing.amenities = [a for a in amenity_keywords if a in text]

            # Description excerpt
            desc_el = soup.select_one("#postingbody, .listing-description, [data-testid='description']")
            if desc_el:
                listing.description_excerpt = desc_el.get_text(strip=True)[:300]

            # Extract photo URLs and download
            listing.photo_paths = await self._extract_photos(page, soup, listing.id)

        except Exception as e:
            logger.warning(f"Error enriching {listing.id}: {e}")
        finally:
            await page.close()

        return listing

    async def _extract_photos(self, page: Page, soup: BeautifulSoup, listing_id: str) -> list[str]:
        """Extract and download listing photos."""
        photo_paths: list[str] = []
        max_photos = config.load_config()["report_settings"]["max_photos_per_listing"]

        # Try to find image URLs via various selectors
        img_urls: list[str] = []

        # JavaScript extraction for gallery images
        try:
            urls = await page.evaluate("""
                () => {
                    const imgs = document.querySelectorAll(
                        '.gallery img, .swipe img, .carousel img, [data-testid="photo"] img, .slider img, .lightbox img'
                    );
                    return Array.from(imgs).map(i => i.src || i.dataset.src || '').filter(Boolean);
                }
            """)
            img_urls.extend(urls)
        except Exception:
            pass

        # Fallback: BeautifulSoup img tags
        if not img_urls:
            for img in soup.select("img[src]"):
                src = img.get("src", "")
                if src and ("images" in src or "photos" in src or "pic" in src) and not ("logo" in src or "icon" in src):
                    img_urls.append(src)

        # Deduplicate and limit
        seen = set()
        unique_urls = []
        for url in img_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        img_urls = unique_urls[:max_photos]

        # Download
        async with aiohttp.ClientSession() as session:
            for i, url in enumerate(img_urls, 1):
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                        if resp.status == 200:
                            path = config.SCREENSHOTS_DIR / f"{listing_id}-{i}.jpg"
                            path.write_bytes(await resp.read())
                            photo_paths.append(str(path))
                except Exception as e:
                    logger.warning(f"Photo download failed for {listing_id}-{i}: {e}")

        return photo_paths

    # ── Full search pipelines ───────────────────────────────────────────

    async def search_rentals(
        self,
        bedrooms: int = 2,
        max_price: Optional[float] = None,
        progress_callback=None,
    ) -> list[Listing]:
        """Run full rental search across all configured sites."""
        all_listings: list[Listing] = []

        if progress_callback:
            await progress_callback("Searching Craigslist rentals...")
        cl_listings = await self.scrape_craigslist_rentals(bedrooms, max_price)
        all_listings.extend(cl_listings)
        if progress_callback:
            await progress_callback(f"Found {len(cl_listings)} on Craigslist")

        # Enrich top listings with detail data
        if progress_callback:
            await progress_callback(f"Enriching {len(all_listings)} listings...")
        for i, listing in enumerate(all_listings):
            try:
                all_listings[i] = await self.enrich_listing(listing)
            except Exception as e:
                logger.warning(f"Enrich failed for {listing.id}: {e}")
            if progress_callback and (i + 1) % 5 == 0:
                await progress_callback(f"Enriched {i + 1}/{len(all_listings)}")

        # Deduplicate
        all_listings = deduplicate_listings(all_listings)

        # Save
        save_listings(all_listings, config.DATA_DIR / "listings.json")
        return all_listings

    async def search_purchases(
        self,
        max_price: float = 700000,
        progress_callback=None,
    ) -> list[Listing]:
        """Run full purchase search across all configured sites."""
        all_listings: list[Listing] = []

        if progress_callback:
            await progress_callback("Searching Craigslist for-sale listings...")
        cl_listings = await self.scrape_craigslist_purchases(max_price)
        all_listings.extend(cl_listings)
        if progress_callback:
            await progress_callback(f"Found {len(cl_listings)} on Craigslist")

        # Enrich
        if progress_callback:
            await progress_callback(f"Enriching {len(all_listings)} listings...")
        for i, listing in enumerate(all_listings):
            try:
                all_listings[i] = await self.enrich_listing(listing)
            except Exception as e:
                logger.warning(f"Enrich failed for {listing.id}: {e}")
            if progress_callback and (i + 1) % 5 == 0:
                await progress_callback(f"Enriched {i + 1}/{len(all_listings)}")

        # Deduplicate
        all_listings = deduplicate_listings(all_listings)

        # Save
        save_listings(all_listings, config.DATA_DIR / "purchase-listings.json")
        return all_listings
