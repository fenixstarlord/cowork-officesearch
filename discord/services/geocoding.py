"""Geocoding and distance calculations using Google Maps API."""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Optional

import aiohttp

import config

logger = logging.getLogger(__name__)

# Cache geocoding results to avoid repeat API calls
_cache: dict[str, tuple[float, float]] = {}
_cache_file = config.DATA_DIR / "geocode_cache.json"


def _load_cache():
    global _cache
    if _cache_file.exists():
        with open(_cache_file) as f:
            raw = json.load(f)
            _cache = {k: tuple(v) for k, v in raw.items()}


def _save_cache():
    with open(_cache_file, "w") as f:
        json.dump({k: list(v) for k, v in _cache.items()}, f)


_load_cache()


async def geocode(address: str) -> Optional[tuple[float, float]]:
    """Geocode an address to (lat, lng). Returns None on failure."""
    if address in _cache:
        return _cache[address]

    if not config.GOOGLE_MAPS_API_KEY:
        return None

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": config.GOOGLE_MAPS_API_KEY}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                if data.get("results"):
                    loc = data["results"][0]["geometry"]["location"]
                    result = (loc["lat"], loc["lng"])
                    _cache[address] = result
                    _save_cache()
                    return result
    except Exception as e:
        logger.warning(f"Geocoding failed for '{address}': {e}")

    return None


def haversine_miles(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance in miles between two lat/lng points."""
    R = 3958.8  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


async def distances_to_key_locations(address: str) -> dict[str, float]:
    """Calculate distances from an address to all key locations in config."""
    coords = await geocode(address)
    if not coords:
        return {}

    cfg = config.load_config()
    distances = {}
    for loc in cfg.get("key_locations", []):
        loc_coords = await geocode(loc["address"])
        if loc_coords:
            dist = haversine_miles(coords[0], coords[1], loc_coords[0], loc_coords[1])
            distances[loc["name"]] = round(dist, 1)

    return distances


async def get_google_maps_image_url(
    lat: float, lng: float, zoom: int = 15, size: str = "600x400"
) -> str:
    """Generate a Google Maps Static API URL."""
    if not config.GOOGLE_MAPS_API_KEY:
        return ""
    return (
        f"https://maps.googleapis.com/maps/api/staticmap"
        f"?center={lat},{lng}&zoom={zoom}&size={size}"
        f"&markers=color:red|{lat},{lng}"
        f"&key={config.GOOGLE_MAPS_API_KEY}"
    )


async def get_street_view_url(
    lat: float, lng: float, size: str = "600x400"
) -> str:
    """Generate a Google Street View Static API URL."""
    if not config.GOOGLE_MAPS_API_KEY:
        return ""
    return (
        f"https://maps.googleapis.com/maps/api/streetview"
        f"?size={size}&location={lat},{lng}"
        f"&key={config.GOOGLE_MAPS_API_KEY}"
    )
