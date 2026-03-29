"""Discord embed builders for listings, reports, and status messages."""

from __future__ import annotations

import discord

from utils.schemas import Listing


# Color constants
COLOR_RENTAL = 0x3498DB  # Blue
COLOR_PURCHASE = 0x2ECC71  # Green
COLOR_INFO = 0x9B59B6  # Purple
COLOR_WARNING = 0xF39C12  # Orange
COLOR_ERROR = 0xE74C3C  # Red
COLOR_SUCCESS = 0x27AE60  # Dark green


def score_color(score: float) -> int:
    """Return an embed color based on listing score."""
    if score >= 80:
        return 0x27AE60
    if score >= 65:
        return 0x2ECC71
    if score >= 50:
        return 0xF39C12
    return 0xE74C3C


def score_bar(score: float, length: int = 10) -> str:
    """Render a text-based score bar."""
    filled = round(score / 100 * length)
    return "\u2588" * filled + "\u2591" * (length - filled)


def listing_embed(listing: Listing, mode: str = "rental") -> discord.Embed:
    """Build a Discord embed for a single listing."""
    title = f"{'NEW ' if listing.is_new else ''}{listing.address}"
    color = score_color(listing.total_score) if listing.total_score else (COLOR_RENTAL if mode == "rental" else COLOR_PURCHASE)

    embed = discord.Embed(
        title=title,
        url=listing.url,
        color=color,
    )

    # Price and basics
    price_str = f"${listing.price:,.0f}" + ("/mo" if mode == "rental" else "")
    basics = f"**{price_str}** | {listing.bedrooms}bd/{listing.bathrooms}ba"
    if listing.sqft:
        basics += f" | {listing.sqft:,} sqft"
    if listing.neighborhood:
        basics += f"\n{listing.neighborhood}"
    if listing.listing_type != "residential":
        basics += f" ({listing.listing_type})"
    embed.description = basics

    # Score
    if listing.total_score:
        embed.add_field(
            name="Score",
            value=f"{score_bar(listing.total_score)} **{listing.total_score:.0f}/100**",
            inline=True,
        )

    # Price trend
    if listing.price_trend:
        arrow = {"dropping": "\u2193", "rising": "\u2191", "stable": "\u2192"}.get(listing.price_trend, "")
        dom = f" ({listing.days_on_market}d)" if listing.days_on_market else ""
        embed.add_field(name="Trend", value=f"{arrow} {listing.price_trend}{dom}", inline=True)

    # Internet
    if listing.internet:
        inet = listing.internet
        embed.add_field(name="Internet", value=f"{inet.classification} ({inet.providers_found} providers)", inline=True)

    # Hipness & Safety
    if listing.hipness_score:
        embed.add_field(name="Hipness", value=f"{score_bar(listing.hipness_score, 5)} {listing.hipness_tier}", inline=True)
    if listing.safety_score:
        embed.add_field(name="Safety", value=f"{score_bar(listing.safety_score, 5)} {listing.safety_tier}", inline=True)

    # Source
    sources = listing.source
    if listing.also_listed_on:
        sources += " + " + ", ".join(a.source for a in listing.also_listed_on)
    embed.set_footer(text=f"Source: {sources} | ID: {listing.id}")

    # Thumbnail from first photo
    if listing.photo_paths:
        # Photos are local paths; we'll attach them separately when sending
        pass

    return embed


def listing_summary_embed(listings: list[Listing], mode: str = "rental", title: str = "") -> discord.Embed:
    """Build a summary embed for multiple listings."""
    if not title:
        title = f"{'Rental' if mode == 'rental' else 'Purchase'} Search Results"

    embed = discord.Embed(title=title, color=COLOR_RENTAL if mode == "rental" else COLOR_PURCHASE)
    embed.description = f"Found **{len(listings)}** listings"

    if listings:
        prices = [l.price for l in listings]
        embed.add_field(name="Price Range", value=f"${min(prices):,.0f} - ${max(prices):,.0f}", inline=True)

        scored = [l for l in listings if l.total_score]
        if scored:
            best = max(scored, key=lambda l: l.total_score)
            embed.add_field(name="Top Scored", value=f"{best.address}\n{best.total_score:.0f}/100", inline=True)

        neighborhoods = set(l.neighborhood for l in listings if l.neighborhood)
        if neighborhoods:
            embed.add_field(name="Neighborhoods", value=", ".join(sorted(neighborhoods)[:8]), inline=False)

    return embed


def search_status_embed(stage: str, detail: str, progress: str = "") -> discord.Embed:
    """Build a status/progress embed."""
    embed = discord.Embed(title=f"Search: {stage}", description=detail, color=COLOR_INFO)
    if progress:
        embed.add_field(name="Progress", value=progress, inline=False)
    return embed


def internet_status_embed(checked: int, total: int, current: str = "") -> discord.Embed:
    """Build an internet check progress embed."""
    pct = (checked / total * 100) if total else 0
    bar = score_bar(pct)
    embed = discord.Embed(
        title="Checking Internet Availability",
        description=f"{bar} {checked}/{total} addresses",
        color=COLOR_INFO,
    )
    if current:
        embed.add_field(name="Current", value=current, inline=False)
    return embed


def error_embed(message: str) -> discord.Embed:
    """Build an error embed."""
    return discord.Embed(title="Error", description=message, color=COLOR_ERROR)


def favorites_embed(favorites: list[Listing], rejected_count: int = 0) -> discord.Embed:
    """Build a favorites summary embed."""
    embed = discord.Embed(title="Favorites", color=COLOR_INFO)
    if not favorites:
        embed.description = "No favorites yet. Use `/favorites add <id>` to add listings."
        return embed

    lines = []
    for l in favorites[:15]:
        lines.append(f"**{l.address}** - ${l.price:,.0f} ({l.total_score:.0f}/100)" if l.total_score else f"**{l.address}** - ${l.price:,.0f}")
    embed.description = "\n".join(lines)
    if len(favorites) > 15:
        embed.set_footer(text=f"...and {len(favorites) - 15} more")
    if rejected_count:
        embed.add_field(name="Rejected", value=str(rejected_count), inline=True)
    return embed


def comparison_embed(listings: list[Listing], mode: str = "rental") -> list[discord.Embed]:
    """Build comparison embeds for 2-3 listings side by side."""
    embeds = []
    header = discord.Embed(title="Listing Comparison", color=COLOR_INFO)
    header.description = " vs ".join(f"**{l.address}**" for l in listings)
    embeds.append(header)

    for l in listings:
        embed = listing_embed(l, mode)
        # Add extra detail fields for comparison
        if l.lease_terms and mode == "rental":
            terms = l.lease_terms
            parts = []
            if terms.deposit:
                parts.append(f"Deposit: ${terms.deposit:,.0f}")
            if terms.pet_policy:
                parts.append(f"Pets: {terms.pet_policy}")
            if terms.parking:
                parts.append(f"Parking: {terms.parking}")
            if parts:
                embed.add_field(name="Terms", value="\n".join(parts), inline=False)
        if l.sale_terms and mode == "purchase":
            terms = l.sale_terms
            parts = []
            if terms.property_tax_annual:
                parts.append(f"Tax: ${terms.property_tax_annual:,.0f}/yr")
            if terms.hoa_monthly:
                parts.append(f"HOA: ${terms.hoa_monthly:,.0f}/mo")
            if terms.zoning:
                parts.append(f"Zoning: {terms.zoning}")
            if parts:
                embed.add_field(name="Terms", value="\n".join(parts), inline=False)
        embeds.append(embed)

    return embeds
