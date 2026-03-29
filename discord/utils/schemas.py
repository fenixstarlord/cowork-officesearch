"""Data models for listings, internet data, and scoring."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class PriceEvent:
    date: str
    event: str
    price: float


@dataclass
class LeaseTerms:
    lease_length: Optional[str] = None
    deposit: Optional[float] = None
    application_fee: Optional[float] = None
    pet_policy: Optional[str] = None
    parking: Optional[str] = None
    utilities: Optional[str] = None


@dataclass
class SaleTerms:
    hoa_monthly: Optional[float] = None
    property_tax_annual: Optional[float] = None
    zoning: Optional[str] = None
    special_assessments: Optional[str] = None
    financing_notes: Optional[str] = None


@dataclass
class PreviousSale:
    date: str
    price: float


@dataclass
class InternetProvider:
    available: bool = False
    fiber: bool = False
    max_down: Optional[float] = None
    connection: Optional[str] = None
    price_from: Optional[float] = None


@dataclass
class InternetData:
    providers_found: int = 0
    quantum_fiber: Optional[InternetProvider] = None
    xfinity: Optional[InternetProvider] = None
    att: Optional[InternetProvider] = None
    tmobile: Optional[InternetProvider] = None
    centurylink: Optional[InternetProvider] = None
    broadbandnow_summary: str = ""
    classification: str = "Unknown"


@dataclass
class HipnessBreakdown:
    neighborhood_baseline: float = 0
    indie_business_density: float = 0
    walkability_bikeability: float = 0
    cultural_venues: float = 0
    online_buzz: float = 0


@dataclass
class HipnessBuzz:
    search_date: str = ""
    reddit_highlights: list[str] = field(default_factory=list)
    press_highlights: list[str] = field(default_factory=list)
    new_openings: list[str] = field(default_factory=list)
    events_nearby: list[str] = field(default_factory=list)
    buzz_score: float = 0
    buzz_summary: str = ""


@dataclass
class SafetyBreakdown:
    crime_score: float = 0
    noise_score: float = 0
    reputation_score: float = 0


@dataclass
class SafetyDetails:
    crime_incidents_nearby: int = 0
    crime_trend: str = "unknown"
    noise_sources: list[str] = field(default_factory=list)
    safety_notes: str = ""


@dataclass
class AlsoListedOn:
    source: str
    url: str
    price: Optional[float] = None


@dataclass
class Listing:
    id: str
    source: str
    url: str
    address: str
    price: float
    bedrooms: int = 0
    bathrooms: int = 0
    sqft: Optional[int] = None
    has_kitchen: bool = False
    has_kitchenette: bool = False
    amenities: list[str] = field(default_factory=list)
    description_excerpt: str = ""
    neighborhood: str = ""
    listing_type: str = "residential"
    photo_paths: list[str] = field(default_factory=list)
    floorplan_path: Optional[str] = None
    also_listed_on: list[AlsoListedOn] = field(default_factory=list)
    price_history: list[PriceEvent] = field(default_factory=list)
    days_on_market: Optional[int] = None
    price_trend: str = ""
    lease_terms: Optional[LeaseTerms] = None
    sale_terms: Optional[SaleTerms] = None
    lot_sqft: Optional[int] = None
    year_built: Optional[int] = None
    property_type: Optional[str] = None
    previous_sales: list[PreviousSale] = field(default_factory=list)
    estimated_value: Optional[float] = None
    hipness_score: float = 0
    hipness_breakdown: Optional[HipnessBreakdown] = None
    hipness_buzz: Optional[HipnessBuzz] = None
    hipness_tier: str = ""
    safety_score: float = 0
    safety_breakdown: Optional[SafetyBreakdown] = None
    safety_details: Optional[SafetyDetails] = None
    safety_tier: str = ""
    is_new: bool = False
    internet: Optional[InternetData] = None
    # Computed
    total_score: float = 0

    def to_dict(self) -> dict:
        return asdict(self)


def listing_from_dict(data: dict) -> Listing:
    """Construct a Listing from a raw dict (e.g., loaded from JSON)."""
    also = [AlsoListedOn(**a) if isinstance(a, dict) else a for a in data.pop("also_listed_on", [])]
    price_hist = [PriceEvent(**p) if isinstance(p, dict) else p for p in data.pop("price_history", [])]
    prev_sales = [PreviousSale(**p) if isinstance(p, dict) else p for p in data.pop("previous_sales", [])]

    lease = data.pop("lease_terms", None)
    if isinstance(lease, dict):
        lease = LeaseTerms(**lease)

    sale = data.pop("sale_terms", None)
    if isinstance(sale, dict):
        sale = SaleTerms(**sale)

    inet = data.pop("internet", None)
    if isinstance(inet, dict):
        for key in ("quantum_fiber", "xfinity", "att", "tmobile", "centurylink"):
            if isinstance(inet.get(key), dict):
                inet[key] = InternetProvider(**inet[key])
        inet = InternetData(**inet)

    hb = data.pop("hipness_breakdown", None)
    if isinstance(hb, dict):
        hb = HipnessBreakdown(**hb)

    hbuzz = data.pop("hipness_buzz", None)
    if isinstance(hbuzz, dict):
        hbuzz = HipnessBuzz(**hbuzz)

    sb = data.pop("safety_breakdown", None)
    if isinstance(sb, dict):
        sb = SafetyBreakdown(**sb)

    sd = data.pop("safety_details", None)
    if isinstance(sd, dict):
        sd = SafetyDetails(**sd)

    return Listing(
        also_listed_on=also,
        price_history=price_hist,
        previous_sales=prev_sales,
        lease_terms=lease,
        sale_terms=sale,
        internet=inet,
        hipness_breakdown=hb,
        hipness_buzz=hbuzz,
        safety_breakdown=sb,
        safety_details=sd,
        **data,
    )


def load_listings(path: Path) -> list[Listing]:
    """Load listings from a JSON file."""
    if not path.exists():
        return []
    with open(path) as f:
        raw = json.load(f)
    return [listing_from_dict(item) for item in raw]


def save_listings(listings: list[Listing], path: Path) -> None:
    """Save listings to a JSON file."""
    with open(path, "w") as f:
        json.dump([l.to_dict() for l in listings], f, indent=2)
