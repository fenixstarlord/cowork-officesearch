"""Cross-site listing deduplication.

Implements the deduplication skill: normalizes addresses and merges
duplicate listings from different sources.
"""

from __future__ import annotations

import re

from utils.schemas import AlsoListedOn, Listing

# Source priority for merge (higher = preferred)
SOURCE_PRIORITY = {
    "zillow": 5,
    "redfin": 4,
    "realtor": 3,
    "apartments": 2,
    "hotpads": 2,
    "loopnet": 2,
    "craigslist": 1,
    "commercialcafe": 1,
}


def normalize_address(address: str) -> str:
    """Normalize an address for deduplication comparison."""
    addr = address.lower().strip()

    # Expand common abbreviations
    replacements = {
        r"\bse\b": "southeast",
        r"\bsw\b": "southwest",
        r"\bne\b": "northeast",
        r"\bnw\b": "northwest",
        r"\bst\b": "street",
        r"\bave\b": "avenue",
        r"\bblvd\b": "boulevard",
        r"\bdr\b": "drive",
        r"\bln\b": "lane",
        r"\bct\b": "court",
        r"\bpl\b": "place",
        r"\brd\b": "road",
        r"\bpkwy\b": "parkway",
        r"\bapt\b": "apartment",
        r"\bunit\b": "unit",
        r"\bfl\b": "floor",
    }
    for pattern, replacement in replacements.items():
        addr = re.sub(pattern, replacement, addr)

    # Remove unit/apartment suffixes
    addr = re.sub(r"(?:apartment|unit|suite|#)\s*\w+", "", addr)

    # Remove punctuation and extra whitespace
    addr = re.sub(r"[^\w\s]", "", addr)
    addr = re.sub(r"\s+", " ", addr).strip()

    # Remove trailing zip/state
    addr = re.sub(r"\s+(?:or|oregon)\s+\d{5}.*$", "", addr)
    addr = re.sub(r"\s+\d{5}.*$", "", addr)

    return addr


def is_duplicate(a: Listing, b: Listing) -> bool:
    """Check if two listings are duplicates."""
    # Exact normalized address match
    if normalize_address(a.address) == normalize_address(b.address):
        return True

    # Fuzzy: same street number + street name + price within 5%
    addr_a = normalize_address(a.address)
    addr_b = normalize_address(b.address)

    num_a = re.match(r"(\d+)", addr_a)
    num_b = re.match(r"(\d+)", addr_b)

    if num_a and num_b and num_a.group(1) == num_b.group(1):
        # Same street number, check street name overlap
        words_a = set(addr_a.split()[1:4])
        words_b = set(addr_b.split()[1:4])
        if words_a & words_b:  # At least one shared street word
            if a.price and b.price:
                ratio = a.price / b.price if b.price else 0
                if 0.95 <= ratio <= 1.05:
                    return True

    return False


def deduplicate_listings(listings: list[Listing]) -> list[Listing]:
    """Remove duplicate listings, keeping the most complete version."""
    if not listings:
        return []

    result: list[Listing] = []
    merged_ids: set[str] = set()

    for listing in listings:
        if listing.id in merged_ids:
            continue

        # Find duplicates
        dupes = []
        for other in listings:
            if other.id != listing.id and other.id not in merged_ids and is_duplicate(listing, other):
                dupes.append(other)
                merged_ids.add(other.id)

        if dupes:
            # Merge: keep highest priority source
            all_versions = [listing] + dupes
            all_versions.sort(key=lambda l: SOURCE_PRIORITY.get(l.source, 0), reverse=True)
            primary = all_versions[0]

            # Track other sources
            for other in all_versions[1:]:
                primary.also_listed_on.append(
                    AlsoListedOn(source=other.source, url=other.url, price=other.price)
                )
                # Merge missing data from lower priority sources
                if not primary.sqft and other.sqft:
                    primary.sqft = other.sqft
                if not primary.description_excerpt and other.description_excerpt:
                    primary.description_excerpt = other.description_excerpt
                if not primary.photo_paths and other.photo_paths:
                    primary.photo_paths = other.photo_paths

            result.append(primary)
        else:
            result.append(listing)

    return result
