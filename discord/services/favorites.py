"""Favorites and review history tracking.

Manages the reviewed.json file with favorites, rejected, and reviewed listings.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import config


class FavoritesManager:
    """Track reviewed, favorited, and rejected listings."""

    def __init__(self, path: Path | None = None):
        self.path = path or (config.DATA_DIR / "reviewed.json")
        self._data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            with open(self.path) as f:
                return json.load(f)
        return {"favorites": [], "rejected": [], "reviewed": []}

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=2)

    @property
    def favorites(self) -> list[str]:
        return self._data.get("favorites", [])

    @property
    def rejected(self) -> list[str]:
        return self._data.get("rejected", [])

    @property
    def reviewed(self) -> list[str]:
        return self._data.get("reviewed", [])

    def add_favorite(self, listing_id: str) -> bool:
        """Add a listing to favorites. Returns True if newly added."""
        if listing_id in self.favorites:
            return False
        self._data["favorites"].append(listing_id)
        if listing_id in self._data["rejected"]:
            self._data["rejected"].remove(listing_id)
        if listing_id not in self._data["reviewed"]:
            self._data["reviewed"].append(listing_id)
        self._save()
        return True

    def remove_favorite(self, listing_id: str) -> bool:
        if listing_id in self._data["favorites"]:
            self._data["favorites"].remove(listing_id)
            self._save()
            return True
        return False

    def reject(self, listing_id: str) -> bool:
        """Mark a listing as rejected."""
        if listing_id in self._data["rejected"]:
            return False
        self._data["rejected"].append(listing_id)
        if listing_id in self._data["favorites"]:
            self._data["favorites"].remove(listing_id)
        if listing_id not in self._data["reviewed"]:
            self._data["reviewed"].append(listing_id)
        self._save()
        return True

    def mark_reviewed(self, listing_id: str):
        if listing_id not in self._data["reviewed"]:
            self._data["reviewed"].append(listing_id)
            self._save()

    def is_favorite(self, listing_id: str) -> bool:
        return listing_id in self.favorites

    def is_rejected(self, listing_id: str) -> bool:
        return listing_id in self.rejected

    def clear_all(self):
        self._data = {"favorites": [], "rejected": [], "reviewed": []}
        self._save()

    def status(self, listing_id: str) -> str:
        """Get the review status badge for a listing."""
        if listing_id in self.favorites:
            return "FAV"
        if listing_id in self.rejected:
            return "REJ"
        if listing_id in self.reviewed:
            return "REVIEWED"
        return "NEW"
