"""Portland Office Search Discord Bot.

Main entry point. Loads all cogs and starts the bot.

Usage:
    python bot.py

Requires DISCORD_TOKEN in .env (see .env.example).
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import discord
from discord.ext import commands

# Add discord/ dir to path so services/utils imports work
sys.path.insert(0, str(Path(__file__).parent))

import config

# ── Logging ────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.DATA_DIR / "bot.log"),
    ],
)
logger = logging.getLogger("officesearch")

# ── Bot Setup ──────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    description="Portland Office Search Bot — Find live/work spaces with fiber internet in Portland, OR",
)

# Cog extensions to load
EXTENSIONS = [
    "cogs.rental",
    "cogs.purchase",
    "cogs.watch_cmd",
    "cogs.compare_cmd",
    "cogs.favorites_cmd",
]


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info(f"Connected to {len(bot.guilds)} guild(s)")

    # Sync slash commands
    if config.DISCORD_GUILD_ID:
        guild = discord.Object(id=int(config.DISCORD_GUILD_ID))
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        logger.info(f"Synced {len(synced)} commands to guild {config.DISCORD_GUILD_ID}")
    else:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} commands globally")


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    logger.error(f"Command error: {error}", exc_info=error)
    await ctx.send(f"Error: {error}")


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    logger.error(f"App command error: {error}", exc_info=error)
    msg = f"An error occurred: {error}"
    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)


# ── Prefix commands (quick access) ────────────────────────────────────

@bot.command(name="status")
async def status_cmd(ctx: commands.Context):
    """Show current data status."""
    rental_path = config.DATA_DIR / "listings.json"
    purchase_path = config.DATA_DIR / "purchase-listings.json"

    from utils.schemas import load_listings

    rentals = load_listings(rental_path)
    purchases = load_listings(purchase_path)

    from services.favorites import FavoritesManager
    fav_mgr = FavoritesManager()

    embed = discord.Embed(title="Office Search Status", color=0x9B59B6)
    embed.add_field(name="Rental Listings", value=str(len(rentals)), inline=True)
    embed.add_field(name="Purchase Listings", value=str(len(purchases)), inline=True)
    embed.add_field(name="Favorites", value=str(len(fav_mgr.favorites)), inline=True)
    embed.add_field(name="Rejected", value=str(len(fav_mgr.rejected)), inline=True)
    embed.add_field(name="Data Directory", value=f"`{config.DATA_DIR}`", inline=False)

    # Key locations
    cfg = config.load_config()
    locs = cfg.get("key_locations", [])
    if locs:
        embed.add_field(
            name="Key Locations",
            value="\n".join(f"**{l['name']}**: {l['address']}" for l in locs),
            inline=False,
        )

    await ctx.send(embed=embed)


@bot.command(name="browse")
async def browse_cmd(ctx: commands.Context, mode: str = "rental"):
    """Browse listings interactively. Usage: !browse [rental|purchase]"""
    from utils.schemas import load_listings
    from utils.pagination import ListingPaginator
    from utils.embeds import error_embed

    listings_file = config.DATA_DIR / ("listings.json" if mode == "rental" else "purchase-listings.json")
    listings = load_listings(listings_file)

    if not listings:
        await ctx.send(embed=error_embed(f"No {mode} listings. Run `/{'rental' if mode == 'rental' else 'purchase'} search` first."))
        return

    paginator = ListingPaginator(listings, mode=mode)
    from utils.embeds import listing_embed
    embed = listing_embed(listings[0], mode)
    embed.set_author(name=f"Listing 1 of {len(listings)}")
    await ctx.send(embed=embed, view=paginator)


# ── Main ───────────────────────────────────────────────────────────────

async def main():
    if not config.DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN not set. Copy .env.example to .env and add your bot token.")
        sys.exit(1)

    async with bot:
        for ext in EXTENSIONS:
            try:
                await bot.load_extension(ext)
                logger.info(f"Loaded extension: {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}", exc_info=e)

        await bot.start(config.DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
