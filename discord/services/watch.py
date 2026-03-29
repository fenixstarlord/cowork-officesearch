"""Watch service — detect new, removed, and price-changed listings."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import config
from utils.schemas import Listing, load_listings, save_listings


def load_search_criteria() -> dict | None:
    """Load saved search criteria from previous search."""
    path = config.DATA_DIR / "search-criteria.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def save_search_criteria(criteria: dict):
    """Save search criteria for future /watch runs."""
    path = config.DATA_DIR / "search-criteria.json"
    with open(path, "w") as f:
        json.dump(criteria, f, indent=2)


def diff_listings(
    old: list[Listing], new: list[Listing]
) -> dict:
    """Compare old and new listing sets. Returns diff summary."""
    old_by_id = {l.id: l for l in old}
    new_by_id = {l.id: l for l in new}

    added = [new_by_id[lid] for lid in new_by_id if lid not in old_by_id]
    removed = [old_by_id[lid] for lid in old_by_id if lid not in new_by_id]

    price_changed = []
    for lid in set(old_by_id) & set(new_by_id):
        old_price = old_by_id[lid].price
        new_price = new_by_id[lid].price
        if old_price != new_price:
            price_changed.append({
                "listing": new_by_id[lid],
                "old_price": old_price,
                "new_price": new_price,
                "change": new_price - old_price,
            })

    # Mark new listings
    for l in added:
        l.is_new = True

    return {
        "added": added,
        "removed": removed,
        "price_changed": price_changed,
        "total_old": len(old),
        "total_new": len(new),
    }


def save_diff(diff: dict, mode: str = "rental"):
    """Save watch diff results to timestamped file."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    path = config.DATA_DIR / f"watch-diff-{timestamp}.json"

    serializable = {
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "total_old": diff["total_old"],
        "total_new": diff["total_new"],
        "added_count": len(diff["added"]),
        "removed_count": len(diff["removed"]),
        "price_changed_count": len(diff["price_changed"]),
        "added": [l.to_dict() for l in diff["added"]],
        "removed": [l.to_dict() for l in diff["removed"]],
        "price_changed": [
            {"id": pc["listing"].id, "address": pc["listing"].address,
             "old_price": pc["old_price"], "new_price": pc["new_price"],
             "change": pc["change"]}
            for pc in diff["price_changed"]
        ],
    }

    with open(path, "w") as f:
        json.dump(serializable, f, indent=2)

    return path
