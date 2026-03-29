"""Paginated listing views using Discord UI components."""

from __future__ import annotations

import discord

from utils.embeds import listing_embed
from utils.schemas import Listing


class ListingPaginator(discord.ui.View):
    """A paginated view for browsing listings one at a time."""

    def __init__(self, listings: list[Listing], mode: str = "rental", timeout: float = 300):
        super().__init__(timeout=timeout)
        self.listings = listings
        self.mode = mode
        self.page = 0
        self._update_buttons()

    def _update_buttons(self):
        self.prev_btn.disabled = self.page <= 0
        self.next_btn.disabled = self.page >= len(self.listings) - 1

    def _current_embed(self) -> discord.Embed:
        embed = listing_embed(self.listings[self.page], self.mode)
        embed.set_author(name=f"Listing {self.page + 1} of {len(self.listings)}")
        return embed

    @discord.ui.button(label="\u25c0 Prev", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(0, self.page - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self._current_embed(), view=self)

    @discord.ui.button(label="Next \u25b6", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = min(len(self.listings) - 1, self.page + 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self._current_embed(), view=self)

    @discord.ui.button(label="\u2b50 Favorite", style=discord.ButtonStyle.success)
    async def fav_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        listing = self.listings[self.page]
        # Import here to avoid circular
        from services.favorites import FavoritesManager
        mgr = FavoritesManager()
        mgr.add_favorite(listing.id)
        await interaction.response.send_message(f"Added **{listing.address}** to favorites.", ephemeral=True)

    @discord.ui.button(label="\u274c Reject", style=discord.ButtonStyle.danger)
    async def reject_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        listing = self.listings[self.page]
        from services.favorites import FavoritesManager
        mgr = FavoritesManager()
        mgr.reject(listing.id)
        await interaction.response.send_message(f"Rejected **{listing.address}**.", ephemeral=True)


class ListingSelect(discord.ui.View):
    """A select menu for choosing listings (used by /compare, etc.)."""

    def __init__(self, listings: list[Listing], max_select: int = 3, timeout: float = 120):
        super().__init__(timeout=timeout)
        self.selected_ids: list[str] = []
        options = [
            discord.SelectOption(
                label=f"${l.price:,.0f} - {l.address[:50]}",
                value=l.id,
                description=f"{l.bedrooms}bd/{l.bathrooms}ba | {l.neighborhood}"[:100],
            )
            for l in listings[:25]  # Discord max 25 options
        ]
        self.select = discord.ui.Select(
            placeholder=f"Select up to {max_select} listings to compare...",
            min_values=2,
            max_values=min(max_select, len(options)),
            options=options,
        )
        self.select.callback = self._on_select
        self.add_item(self.select)

    async def _on_select(self, interaction: discord.Interaction):
        self.selected_ids = self.select.values
        self.stop()
        await interaction.response.defer()
