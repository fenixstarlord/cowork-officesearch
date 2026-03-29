"""Favorites command — manage favorite and rejected listings."""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

import config
from services.favorites import FavoritesManager
from utils.embeds import error_embed, favorites_embed, listing_embed
from utils.schemas import Listing, load_listings

logger = logging.getLogger(__name__)


class FavoritesCog(commands.Cog, name="Favorites"):
    """Track favorites, rejected, and reviewed listings."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    favorites_group = app_commands.Group(name="favorites", description="Manage favorite listings")

    @favorites_group.command(name="list", description="Show all favorited listings")
    @app_commands.describe(mode="Search mode: rental or purchase")
    async def list_favorites(self, interaction: discord.Interaction, mode: str = "rental"):
        mgr = FavoritesManager()
        fav_ids = mgr.favorites

        if not fav_ids:
            await interaction.response.send_message(
                embed=favorites_embed([], 0), ephemeral=True
            )
            return

        listings_file = config.DATA_DIR / ("listings.json" if mode == "rental" else "purchase-listings.json")
        all_listings = load_listings(listings_file)
        fav_listings = [l for l in all_listings if l.id in fav_ids]

        embed = favorites_embed(fav_listings, len(mgr.rejected))
        await interaction.response.send_message(embed=embed)

    @favorites_group.command(name="add", description="Add a listing to favorites")
    @app_commands.describe(listing_id="The listing ID to favorite")
    async def add_favorite(self, interaction: discord.Interaction, listing_id: str):
        mgr = FavoritesManager()
        added = mgr.add_favorite(listing_id)
        if added:
            await interaction.response.send_message(f"Added `{listing_id}` to favorites.", ephemeral=True)
        else:
            await interaction.response.send_message(f"`{listing_id}` is already a favorite.", ephemeral=True)

    @favorites_group.command(name="remove", description="Remove a listing from favorites")
    @app_commands.describe(listing_id="The listing ID to unfavorite")
    async def remove_favorite(self, interaction: discord.Interaction, listing_id: str):
        mgr = FavoritesManager()
        removed = mgr.remove_favorite(listing_id)
        if removed:
            await interaction.response.send_message(f"Removed `{listing_id}` from favorites.", ephemeral=True)
        else:
            await interaction.response.send_message(f"`{listing_id}` is not in favorites.", ephemeral=True)

    @favorites_group.command(name="reject", description="Mark a listing as rejected")
    @app_commands.describe(listing_id="The listing ID to reject")
    async def reject_listing(self, interaction: discord.Interaction, listing_id: str):
        mgr = FavoritesManager()
        rejected = mgr.reject(listing_id)
        if rejected:
            await interaction.response.send_message(f"Rejected `{listing_id}`.", ephemeral=True)
        else:
            await interaction.response.send_message(f"`{listing_id}` is already rejected.", ephemeral=True)

    @favorites_group.command(name="clear", description="Clear all favorites and rejected listings")
    async def clear_favorites(self, interaction: discord.Interaction):
        mgr = FavoritesManager()
        mgr.clear_all()
        await interaction.response.send_message("Cleared all favorites and rejected listings.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(FavoritesCog(bot))
