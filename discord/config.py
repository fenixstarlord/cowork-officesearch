"""Bot configuration loaded from config.json and environment variables."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
PROJECT_DIR = BASE_DIR.parent
DATA_DIR = Path(os.getenv("DATA_DIR", PROJECT_DIR / "data" / "output"))
CONFIG_PATH = PROJECT_DIR / "data" / "config.json"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# Ensure output directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load the project config.json."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {
        "key_locations": [],
        "search_defaults": {
            "rental": {"bedrooms": 2, "min_sqft": None, "max_price": None, "mixed_use": "preferred"},
            "purchase": {"max_price": 700000, "max_results": 20},
        },
        "report_settings": {
            "max_photos_per_listing": 8,
            "include_interactive_map": True,
            "include_hipness_score": True,
            "include_safety_score": True,
            "show_rejected_listings": False,
        },
    }


# Portland zip codes for search coverage
PORTLAND_ZIPS = ["97214", "97202", "97209", "97212", "97232", "97215", "97206", "97211", "97213", "97201"]

# Rental listing sites
RENTAL_SITES = {
    "zillow": "https://www.zillow.com/portland-or/rentals/",
    "apartments": "https://www.apartments.com/portland-or/",
    "craigslist": "https://portland.craigslist.org/search/apa",
    "hotpads": "https://hotpads.com/portland-or/apartments-for-rent",
    "redfin": "https://www.redfin.com/city/30772/OR/Portland/apartments-for-rent",
}

# Commercial / mixed-use rental sites
COMMERCIAL_RENTAL_SITES = {
    "loopnet": "https://www.loopnet.com/search/commercial-real-estate/portland-or/for-lease/",
    "commercialcafe": "https://www.commercialcafe.com/commercial-space-for-rent/us/or/portland/",
}

# Purchase listing sites
PURCHASE_SITES = {
    "zillow": "https://www.zillow.com/portland-or/",
    "redfin": "https://www.redfin.com/city/30772/OR/Portland",
    "realtor": "https://www.realtor.com/realestateandhomes-search/Portland_OR",
    "craigslist": "https://portland.craigslist.org/search/rea",
}

# Commercial purchase sites
COMMERCIAL_PURCHASE_SITES = {
    "loopnet": "https://www.loopnet.com/search/commercial-real-estate/portland-or/for-sale/",
    "commercialcafe": "https://www.commercialcafe.com/commercial-property-for-sale/us/or/portland/",
}

# ISP check URL
BROADBANDNOW_URL = "https://broadbandnow.com"

# Hipness baselines by neighborhood
HIPNESS_BASELINES = {
    "hawthorne": 92, "division": 88, "alberta": 90, "mississippi": 88,
    "buckman": 90, "sunnyside": 85, "richmond": 82, "belmont": 80,
    "pearl district": 78, "hosford-abernethy": 75, "sellwood": 70,
    "irvington": 68, "laurelhurst": 65, "grant park": 62,
    "hollywood": 58, "brooklyn": 55, "south portland": 50,
    "goose hollow": 48, "old town/chinatown": 45, "eastmoreland": 42,
}

# Noise sources for safety scoring
MAJOR_ARTERIALS = ["Powell Blvd", "Sandy Blvd", "82nd Ave", "Division St", "Broadway", "MLK Blvd"]
FREEWAYS = ["I-84", "I-5", "I-405", "US-26"]
