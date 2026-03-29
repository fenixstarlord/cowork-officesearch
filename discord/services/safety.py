"""Safety and noise scoring service.

Implements the safety-scoring skill: crime data proximity, noise sources,
and online reputation.
"""

from __future__ import annotations

import logging
import re

import config
from utils.schemas import Listing, SafetyBreakdown, SafetyDetails

logger = logging.getLogger(__name__)


def noise_score(address: str, neighborhood: str) -> tuple[float, list[str]]:
    """Estimate noise level from address proximity to arterials/freeways.

    Returns (score 0-25, list of noise sources).
    """
    addr = address.lower()
    sources: list[str] = []
    penalty = 0

    # Check freeways (high noise)
    for fw in config.FREEWAYS:
        if fw.lower().replace("-", "") in addr.replace("-", ""):
            sources.append(f"Near {fw}")
            penalty += 8

    # Check major arterials
    for art in config.MAJOR_ARTERIALS:
        if art.lower().split()[0] in addr:
            sources.append(f"On/near {art}")
            penalty += 4

    # Powell Blvd is especially loud
    if "powell" in addr:
        penalty += 3

    score = max(0, 25 - penalty)
    return score, sources


def estimate_crime_score(neighborhood: str) -> tuple[float, str]:
    """Estimate crime score from neighborhood.

    Without live API data, use neighborhood-based estimates.
    Returns (score 0-60, trend string).
    """
    n = neighborhood.lower()

    # Lower crime areas
    safe = ["laurelhurst", "eastmoreland", "sellwood", "irvington", "grant park", "alameda"]
    moderate = ["hawthorne", "buckman", "sunnyside", "richmond", "belmont", "division",
                "hosford-abernethy", "brooklyn", "hollywood"]
    higher = ["old town", "chinatown", "downtown", "pearl district"]

    if any(s in n for s in safe):
        return 52, "stable"
    elif any(s in n for s in moderate):
        return 40, "stable"
    elif any(s in n for s in higher):
        return 25, "elevated"
    return 35, "unknown"


def score_safety(listing: Listing) -> Listing:
    """Compute full safety score for a listing."""
    crime, trend = estimate_crime_score(listing.neighborhood)
    noise, noise_sources = noise_score(listing.address, listing.neighborhood)
    reputation = 10  # Default mid-range without live web search

    total = crime + noise + reputation

    listing.safety_score = round(total, 1)
    listing.safety_breakdown = SafetyBreakdown(
        crime_score=crime,
        noise_score=noise,
        reputation_score=reputation,
    )
    listing.safety_details = SafetyDetails(
        crime_trend=trend,
        noise_sources=noise_sources,
    )

    # Tier classification
    if listing.safety_score >= 80:
        listing.safety_tier = "Very Safe & Quiet"
    elif listing.safety_score >= 65:
        listing.safety_tier = "Safe"
    elif listing.safety_score >= 50:
        listing.safety_tier = "Moderate"
    elif listing.safety_score >= 35:
        listing.safety_tier = "Some Concerns"
    else:
        listing.safety_tier = "Significant Concerns"

    return listing
