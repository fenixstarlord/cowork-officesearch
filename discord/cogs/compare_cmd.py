"""Compare command — side-by-side comparison of 2-3 listings."""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

import config
from utils.embeds import comparison_embed, error_embed
from utils.pagination import ListingSelect
from utils.schemas import load_listings

logger = logging.getLogger(__name__)


class CompareCog(commands.Cog, name="Compare"):
    """Side-by-side listing comparison."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="compare", description="Compare 2-3 listings side by side")
    @app_commands.describe(
        mode="Search mode: rental or purchase",
        ids="Comma-separated listing IDs (optional — shows select menu if omitted)",
    )
    async def compare(
        self,
        interaction: discord.Interaction,
        mode: str = "rental",
        ids: str | None = None,
    ):
        listings_file = config.DATA_DIR / ("listings.json" if mode == "rental" else "purchase-listings.json")
        all_listings = load_listings(listings_file)

        if not all_listings:
            await interaction.response.send_message(
                embed=error_embed(f"No {mode} listings found. Run a search first."),
                ephemeral=True,
            )
            return

        if ids:
            # Direct IDs provided
            id_list = [i.strip() for i in ids.split(",")]
            selected = [l for l in all_listings if l.id in id_list]
            if len(selected) < 2:
                await interaction.response.send_message(
                    embed=error_embed(f"Need at least 2 valid IDs. Found {len(selected)}."),
                    ephemeral=True,
                )
                return
            selected = selected[:3]
            await interaction.response.defer()
            embeds = comparison_embed(selected, mode)
            await interaction.followup.send(embeds=embeds[:10])
        else:
            # Show select menu
            view = ListingSelect(all_listings, max_select=3)
            await interaction.response.send_message(
                "Select 2-3 listings to compare:", view=view, ephemeral=True
            )
            timed_out = await view.wait()
            if timed_out or not view.selected_ids:
                return

            selected = [l for l in all_listings if l.id in view.selected_ids]
            if len(selected) < 2:
                await interaction.followup.send(embed=error_embed("Need at least 2 listings."), ephemeral=True)
                return

            embeds = comparison_embed(selected, mode)
            await interaction.followup.send(embeds=embeds[:10])


async def setup(bot: commands.Bot):
    await bot.add_cog(CompareCog(bot))
