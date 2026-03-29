"""Watch command — monitor for new or price-changed listings."""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

import config
from services.scraper import ListingScraper
from services.scoring import score_listings
from services.safety import score_safety
from services.watch import diff_listings, load_search_criteria, save_diff
from utils.embeds import error_embed, listing_embed, search_status_embed
from utils.schemas import load_listings, save_listings

logger = logging.getLogger(__name__)


class WatchCog(commands.Cog, name="Watch"):
    """Monitor for new and changed listings."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="watch", description="Check for new, removed, or price-changed listings since last search")
    async def watch(self, interaction: discord.Interaction):
        await interaction.response.defer()

        criteria = load_search_criteria()
        if not criteria:
            await interaction.followup.send(embed=error_embed(
                "No previous search found. Run `/rental search` or `/purchase search` first."
            ))
            return

        mode = criteria.get("mode", "rental")
        listings_file = config.DATA_DIR / ("listings.json" if mode == "rental" else "purchase-listings.json")
        old_listings = load_listings(listings_file)

        if not old_listings:
            await interaction.followup.send(embed=error_embed(
                f"No previous {mode} listings found. Run a search first."
            ))
            return

        status_msg = await interaction.followup.send(
            embed=search_status_embed("Watch", f"Re-running {mode} search with saved criteria..."),
            wait=True,
        )

        async def progress(msg: str):
            try:
                await status_msg.edit(embed=search_status_embed("Watch", msg))
            except Exception:
                pass

        # Re-run search
        scraper = ListingScraper()
        try:
            await scraper.start()
            if mode == "rental":
                new_listings = await scraper.search_rentals(
                    bedrooms=criteria.get("bedrooms", 2),
                    max_price=criteria.get("max_price"),
                    progress_callback=progress,
                )
            else:
                new_listings = await scraper.search_purchases(
                    max_price=criteria.get("max_price", 700000),
                    progress_callback=progress,
                )
        finally:
            await scraper.close()

        for l in new_listings:
            score_safety(l)
        new_listings = score_listings(new_listings, mode=mode)

        # Diff
        diff = diff_listings(old_listings, new_listings)
        diff_path = save_diff(diff, mode)

        # Save new listings as current
        save_listings(new_listings, listings_file)

        # Build results embed
        embed = discord.Embed(
            title=f"Watch Results — {mode.title()}",
            color=0x3498DB,
        )
        embed.add_field(name="Previous", value=str(diff["total_old"]), inline=True)
        embed.add_field(name="Current", value=str(diff["total_new"]), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="New Listings", value=str(len(diff["added"])), inline=True)
        embed.add_field(name="Removed", value=str(len(diff["removed"])), inline=True)
        embed.add_field(name="Price Changed", value=str(len(diff["price_changed"])), inline=True)

        await status_msg.edit(embed=embed)

        # Show new listings
        if diff["added"]:
            embeds = [listing_embed(l, mode) for l in diff["added"][:5]]
            await interaction.followup.send(content="**New Listings:**", embeds=embeds[:5])

        # Show price changes
        if diff["price_changed"]:
            lines = []
            for pc in diff["price_changed"][:10]:
                arrow = "\u2193" if pc["change"] < 0 else "\u2191"
                lines.append(
                    f"{arrow} **{pc['listing'].address}**: "
                    f"${pc['old_price']:,.0f} -> ${pc['new_price']:,.0f} "
                    f"({'+' if pc['change'] > 0 else ''}{pc['change']:,.0f})"
                )
            price_embed = discord.Embed(
                title="Price Changes",
                description="\n".join(lines),
                color=0xF39C12,
            )
            await interaction.followup.send(embed=price_embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(WatchCog(bot))
