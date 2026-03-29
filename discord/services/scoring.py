"""Listing evaluation scoring.

Implements the rental and purchase scoring rubrics from the listing-evaluation
and purchase-evaluation skills.
"""

from __future__ import annotations

from utils.schemas import Listing


def score_rental(listing: Listing) -> float:
    """Score a rental listing on a 0-100 scale."""
    score = 0.0

    # Room count (12%)
    if listing.bedrooms >= 3:
        score += 12
    elif listing.bedrooms >= 2:
        score += 9
    elif listing.bedrooms >= 1:
        score += 5

    # Kitchen quality (8%)
    if listing.has_kitchen:
        score += 8
    elif listing.has_kitchenette:
        score += 5

    # Price reasonableness (14%)
    if listing.price:
        if listing.price < 1400:
            score += 14
        elif listing.price < 1800:
            score += 12
        elif listing.price < 2200:
            score += 9
        elif listing.price < 2800:
            score += 6
        else:
            score += 3

    # Square footage (8%)
    if listing.sqft:
        if listing.sqft >= 1200:
            score += 8
        elif listing.sqft >= 900:
            score += 6
        elif listing.sqft >= 700:
            score += 4
        else:
            score += 2

    # Mixed-use friendliness (8%)
    if listing.listing_type == "mixed-use":
        score += 8
    elif listing.listing_type == "commercial":
        score += 6
    elif any(kw in listing.description_excerpt.lower() for kw in ["live/work", "home office", "studio"]):
        score += 4
    else:
        score += 2

    # Fiber internet quality (10%)
    if listing.internet:
        inet_class = listing.internet.classification
        if inet_class == "Excellent":
            score += 10
        elif inet_class == "Good":
            score += 7
        elif inet_class == "Adequate":
            score += 4
        elif inet_class != "check_failed":
            score += 1

    # Food proximity / indie corridor (12%) - estimated from neighborhood
    score += _food_proximity_score(listing.neighborhood, 12)

    # Main street location (10%) - estimated from address
    score += _main_street_score(listing.address, 10)

    # Hipness score (9%)
    if listing.hipness_score:
        if listing.hipness_score >= 85:
            score += 9
        elif listing.hipness_score >= 70:
            score += 7
        elif listing.hipness_score >= 55:
            score += 5
        else:
            score += 2

    # Safety score (9%)
    if listing.safety_score:
        if listing.safety_score >= 80:
            score += 9
        elif listing.safety_score >= 65:
            score += 7
        elif listing.safety_score >= 50:
            score += 5
        else:
            score += 2

    return round(score, 1)


def score_purchase(listing: Listing) -> float:
    """Score a purchase listing on a 0-100 scale."""
    score = 0.0

    # Price value (12%)
    if listing.price:
        if listing.price < 400000:
            score += 12
        elif listing.price < 500000:
            score += 10
        elif listing.price < 600000:
            score += 7
        elif listing.price < 700000:
            score += 5
        else:
            score += 2

    # Room count (8%)
    if listing.bedrooms >= 4:
        score += 8
    elif listing.bedrooms >= 3:
        score += 6
    elif listing.bedrooms >= 2:
        score += 4

    # Square footage (8%)
    if listing.sqft:
        if listing.sqft >= 2000:
            score += 8
        elif listing.sqft >= 1500:
            score += 6
        elif listing.sqft >= 1000:
            score += 4
        else:
            score += 2

    # Mixed-use potential (10%)
    ptype = (listing.property_type or "").lower()
    ltype = listing.listing_type.lower()
    if ltype == "mixed-use" or "mixed" in ptype:
        score += 10
    elif "duplex" in ptype or "multi" in ptype:
        score += 8
    elif "commercial" in ptype or ltype == "commercial":
        score += 6
    else:
        score += 3

    # Location quality (8%)
    score += _food_proximity_score(listing.neighborhood, 8)

    # Fiber internet quality (10%)
    if listing.internet:
        inet_class = listing.internet.classification
        if inet_class == "Excellent":
            score += 10
        elif inet_class == "Good":
            score += 7
        elif inet_class == "Adequate":
            score += 4
        elif inet_class != "check_failed":
            score += 1

    # Property condition (5%)
    if listing.year_built:
        if listing.year_built >= 2010:
            score += 5
        elif listing.year_built >= 1990:
            score += 4
        elif listing.year_built >= 1960:
            score += 3
        else:
            score += 2

    # Food proximity (11%)
    score += _food_proximity_score(listing.neighborhood, 11)

    # Main street location (10%)
    score += _main_street_score(listing.address, 10)

    # Hipness (9%)
    if listing.hipness_score:
        if listing.hipness_score >= 85:
            score += 9
        elif listing.hipness_score >= 70:
            score += 7
        elif listing.hipness_score >= 55:
            score += 5
        else:
            score += 2

    # Safety (9%)
    if listing.safety_score:
        if listing.safety_score >= 80:
            score += 9
        elif listing.safety_score >= 65:
            score += 7
        elif listing.safety_score >= 50:
            score += 5
        else:
            score += 2

    return round(score, 1)


def _food_proximity_score(neighborhood: str, max_pts: float) -> float:
    """Estimate food/indie proximity score from neighborhood name."""
    from config import HIPNESS_BASELINES
    n = neighborhood.lower()
    # High food corridors
    high = ["hawthorne", "division", "alberta", "mississippi", "buckman", "belmont"]
    mid = ["sunnyside", "richmond", "pearl district", "hosford-abernethy", "sellwood", "irvington"]
    if any(h in n for h in high):
        return max_pts
    if any(m in n for m in mid):
        return max_pts * 0.7
    return max_pts * 0.3


def _main_street_score(address: str, max_pts: float) -> float:
    """Estimate main-street score from address keywords."""
    addr = address.lower()
    main_streets = ["hawthorne", "division", "belmont", "alberta", "mississippi", "broadway", "sandy", "mlk", "powell"]
    if any(s in addr for s in main_streets):
        return max_pts
    # Near a main street
    if any(s in addr for s in ["se ", "ne ", "nw ", "sw "]):
        return max_pts * 0.5
    return max_pts * 0.2


def score_listings(listings: list[Listing], mode: str = "rental") -> list[Listing]:
    """Score all listings and sort by score descending."""
    scorer = score_rental if mode == "rental" else score_purchase
    for listing in listings:
        listing.total_score = scorer(listing)
    listings.sort(key=lambda l: l.total_score, reverse=True)
    return listings
