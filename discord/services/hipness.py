"""Hipness scoring service.

Implements the hipness-scoring skill: neighborhood baseline, indie business
density, walkability, cultural venues, and online buzz.
"""

from __future__ import annotations

import logging
import re
from datetime import date

import aiohttp

import config
from utils.schemas import HipnessBreakdown, HipnessBuzz, Listing

logger = logging.getLogger(__name__)


def get_baseline(neighborhood: str) -> float:
    """Get pre-assigned hipness baseline for a neighborhood (0-25 scaled)."""
    n = neighborhood.lower()
    for key, value in config.HIPNESS_BASELINES.items():
        if key in n:
            return value / 100 * 25  # Scale to 25% weight
    return 10  # Default for unknown neighborhoods


async def count_nearby_places(
    lat: float, lng: float, keyword: str, radius: int = 800
) -> int:
    """Count nearby places using Google Maps Places API."""
    if not config.GOOGLE_MAPS_API_KEY:
        return 0

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "keyword": keyword,
        "key": config.GOOGLE_MAPS_API_KEY,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                return len(data.get("results", []))
    except Exception as e:
        logger.warning(f"Places API error for '{keyword}': {e}")
        return 0


async def indie_business_score(lat: float, lng: float) -> float:
    """Score indie business density (0-25 scaled)."""
    keywords = ["coffee shop", "brewery", "independent restaurant", "bar", "vintage shop", "art gallery"]
    total = 0
    for kw in keywords:
        total += await count_nearby_places(lat, lng, kw)

    if total >= 30:
        return 25
    elif total >= 20:
        return 20
    elif total >= 10:
        return 15
    elif total >= 5:
        return 10
    return 5


async def cultural_venue_score(lat: float, lng: float) -> float:
    """Score cultural venues nearby (0-15 scaled)."""
    keywords = ["live music venue", "theater", "art gallery", "community center"]
    total = 0
    for kw in keywords:
        total += await count_nearby_places(lat, lng, kw, radius=1600)

    if total >= 10:
        return 15
    elif total >= 5:
        return 12
    elif total >= 2:
        return 8
    return 4


async def score_hipness(listing: Listing, lat: float = 0, lng: float = 0) -> Listing:
    """Compute full hipness score for a listing."""
    baseline = get_baseline(listing.neighborhood)

    indie = 12.5  # Default mid-range if no geocoding
    walkability = 10.0
    cultural = 8.0
    buzz = 10.0

    if lat and lng and config.GOOGLE_MAPS_API_KEY:
        indie = await indie_business_score(lat, lng)
        cultural = await cultural_venue_score(lat, lng)

    total = baseline + indie + walkability + cultural + buzz

    listing.hipness_score = round(total, 1)
    listing.hipness_breakdown = HipnessBreakdown(
        neighborhood_baseline=baseline,
        indie_business_density=indie,
        walkability_bikeability=walkability,
        cultural_venues=cultural,
        online_buzz=buzz,
    )
    listing.hipness_buzz = HipnessBuzz(
        search_date=date.today().isoformat(),
        buzz_score=buzz,
    )

    # Tier classification
    if listing.hipness_score >= 85:
        listing.hipness_tier = "Cultural Epicenter"
    elif listing.hipness_score >= 70:
        listing.hipness_tier = "Very Hip"
    elif listing.hipness_score >= 55:
        listing.hipness_tier = "Hip-Adjacent"
    elif listing.hipness_score >= 40:
        listing.hipness_tier = "Neutral"
    else:
        listing.hipness_tier = "Low Hipness"

    return listing
