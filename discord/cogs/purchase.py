"""Purchase search commands — /purchase search, check-internet, report."""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

import config
from services.internet_checker import InternetChecker
from services.report_builder import build_report
from services.safety import score_safety
from services.scoring import score_listings
from services.scraper import ListingScraper
from services.watch import save_search_criteria
from utils.embeds import (
    error_embed,
    internet_status_embed,
    listing_summary_embed,
    search_status_embed,
)
from utils.pagination import ListingPaginator
from utils.schemas import load_listings, save_listings

logger = logging.getLogger(__name__)


class PurchaseCog(commands.Cog, name="Purchase"):
    """Purchase search pipeline commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    purchase_group = app_commands.Group(name="purchase", description="Purchase search commands")

    @purchase_group.command(name="search", description="Search Portland for-sale properties under $700k")
    @app_commands.describe(
        max_price="Maximum purchase price (default: $700,000)",
        property_type="Property type filter: house, duplex, multi-family, mixed-use, commercial, any",
    )
    async def search_listings(
        self,
        interaction: discord.Interaction,
        max_price: int = 700000,
        property_type: str = "any",
    ):
        await interaction.response.defer()

        status_msg = await interaction.followup.send(
            embed=search_status_embed("Starting", "Initializing browser..."),
            wait=True,
        )

        async def progress(msg: str):
            try:
                await status_msg.edit(embed=search_status_embed("Searching", msg))
            except Exception:
                pass

        scraper = ListingScraper()
        try:
            await scraper.start()
            listings = await scraper.search_purchases(
                max_price=max_price,
                progress_callback=progress,
            )
        finally:
            await scraper.close()

        if not listings:
            await status_msg.edit(embed=error_embed("No properties found. Try adjusting your criteria."))
            return

        # Filter by property type if specified
        if property_type != "any":
            listings = [l for l in listings if property_type.lower() in (l.property_type or "").lower()
                        or property_type.lower() in l.listing_type.lower()]

        # Score listings
        for l in listings:
            score_safety(l)
        listings = score_listings(listings, mode="purchase")

        # Save search criteria for /watch
        save_search_criteria({
            "mode": "purchase",
            "max_price": max_price,
            "property_type": property_type,
        })

        save_listings(listings, config.DATA_DIR / "purchase-listings.json")

        summary = listing_summary_embed(listings, mode="purchase")
        paginator = ListingPaginator(listings, mode="purchase")
        await status_msg.edit(embed=summary, view=paginator)

    @purchase_group.command(name="check-internet", description="Check fiber internet for purchase listings")
    async def check_internet(self, interaction: discord.Interaction):
        await interaction.response.defer()

        listings = load_listings(config.DATA_DIR / "purchase-listings.json")
        if not listings:
            await interaction.followup.send(embed=error_embed("No listings found. Run `/purchase search` first."))
            return

        status_msg = await interaction.followup.send(
            embed=internet_status_embed(0, len(listings)),
            wait=True,
        )

        async def progress(checked: int, total: int, current: str):
            try:
                await status_msg.edit(embed=internet_status_embed(checked, total, current))
            except Exception:
                pass

        checker = InternetChecker()
        try:
            await checker.start()
            listings = await checker.check_listings(listings, progress_callback=progress)
        finally:
            await checker.close()

        listings = score_listings(listings, mode="purchase")
        save_listings(listings, config.DATA_DIR / "purchase-listings.json")

        excellent = sum(1 for l in listings if l.internet and l.internet.classification == "Excellent")
        good = sum(1 for l in listings if l.internet and l.internet.classification == "Good")
        failed = sum(1 for l in listings if l.internet and l.internet.classification == "check_failed")

        embed = discord.Embed(
            title="Internet Check Complete",
            description=f"Checked {len(listings)} properties",
            color=0x27AE60,
        )
        embed.add_field(name="Excellent (Fiber)", value=str(excellent), inline=True)
        embed.add_field(name="Good", value=str(good), inline=True)
        embed.add_field(name="Failed", value=str(failed), inline=True)

        await status_msg.edit(embed=embed)

    @purchase_group.command(name="report", description="Generate HTML report for purchase listings")
    async def generate_report(self, interaction: discord.Interaction):
        await interaction.response.defer()

        listings = load_listings(config.DATA_DIR / "purchase-listings.json")
        if not listings:
            await interaction.followup.send(embed=error_embed("No listings found. Run `/purchase search` first."))
            return

        status_msg = await interaction.followup.send(
            embed=search_status_embed("Generating Report", f"Processing {len(listings)} listings..."),
            wait=True,
        )

        async def progress(msg: str):
            try:
                await status_msg.edit(embed=search_status_embed("Generating Report", msg))
            except Exception:
                pass

        report_path = await build_report(listings, mode="purchase", progress_callback=progress)

        embed = discord.Embed(
            title="Purchase Report Generated",
            description=f"Report saved to `{report_path.name}`",
            color=0x27AE60,
        )
        embed.add_field(name="Properties", value=str(len(listings)), inline=True)

        await status_msg.edit(embed=embed)
        await interaction.followup.send(file=discord.File(str(report_path), filename=report_path.name))


async def setup(bot: commands.Bot):
    await bot.add_cog(PurchaseCog(bot))
