"""Rental search commands — /rental search, check-internet, report."""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

import config
from services.favorites import FavoritesManager
from services.hipness import score_hipness
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


class RentalCog(commands.Cog, name="Rental"):
    """Rental search pipeline commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    rental_group = app_commands.Group(name="rental", description="Rental search commands")

    @rental_group.command(name="search", description="Search Portland rental listings")
    @app_commands.describe(
        bedrooms="Minimum bedrooms (default: 2)",
        max_price="Maximum monthly rent (no cap if omitted)",
        mixed_use="Prefer mixed-use/live-work spaces",
    )
    async def search_listings(
        self,
        interaction: discord.Interaction,
        bedrooms: int = 2,
        max_price: int | None = None,
        mixed_use: bool = True,
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
            listings = await scraper.search_rentals(
                bedrooms=bedrooms,
                max_price=max_price,
                progress_callback=progress,
            )
        finally:
            await scraper.close()

        if not listings:
            await status_msg.edit(embed=error_embed("No listings found. Try adjusting your search criteria."))
            return

        # Score listings
        for l in listings:
            score_safety(l)
        listings = score_listings(listings, mode="rental")

        # Save search criteria for /watch
        save_search_criteria({
            "mode": "rental",
            "bedrooms": bedrooms,
            "max_price": max_price,
            "mixed_use": mixed_use,
        })

        save_listings(listings, config.DATA_DIR / "listings.json")

        # Show summary + paginator
        summary = listing_summary_embed(listings, mode="rental")
        paginator = ListingPaginator(listings, mode="rental")
        await status_msg.edit(embed=summary, view=paginator)

    @rental_group.command(name="check-internet", description="Check fiber internet for rental listings")
    async def check_internet(self, interaction: discord.Interaction):
        await interaction.response.defer()

        listings = load_listings(config.DATA_DIR / "listings.json")
        if not listings:
            await interaction.followup.send(embed=error_embed("No listings found. Run `/rental search` first."))
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

        # Re-score with internet data
        listings = score_listings(listings, mode="rental")
        save_listings(listings, config.DATA_DIR / "listings.json")

        excellent = sum(1 for l in listings if l.internet and l.internet.classification == "Excellent")
        good = sum(1 for l in listings if l.internet and l.internet.classification == "Good")
        failed = sum(1 for l in listings if l.internet and l.internet.classification == "check_failed")

        embed = discord.Embed(
            title="Internet Check Complete",
            description=f"Checked {len(listings)} listings",
            color=0x27AE60,
        )
        embed.add_field(name="Excellent (Fiber)", value=str(excellent), inline=True)
        embed.add_field(name="Good", value=str(good), inline=True)
        embed.add_field(name="Failed", value=str(failed), inline=True)

        await status_msg.edit(embed=embed)

    @rental_group.command(name="report", description="Generate HTML report for rental listings")
    async def generate_report(self, interaction: discord.Interaction):
        await interaction.response.defer()

        listings = load_listings(config.DATA_DIR / "listings.json")
        if not listings:
            await interaction.followup.send(embed=error_embed("No listings found. Run `/rental search` first."))
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

        report_path = await build_report(listings, mode="rental", progress_callback=progress)

        embed = discord.Embed(
            title="Rental Report Generated",
            description=f"Report saved to `{report_path.name}`",
            color=0x27AE60,
        )
        embed.add_field(name="Listings", value=str(len(listings)), inline=True)

        # Send the HTML file
        await status_msg.edit(embed=embed)
        await interaction.followup.send(file=discord.File(str(report_path), filename=report_path.name))


async def setup(bot: commands.Bot):
    await bot.add_cog(RentalCog(bot))
