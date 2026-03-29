#!/usr/bin/env python3
"""Generate Portland SE Apartment Search HTML report from listings.json."""

import json
import os
import base64
import math
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

# Key locations for distance calculations — loaded from config at runtime, with fallback defaults
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
_DEFAULT_KEY_LOCATIONS = [
    {"name": "Chris", "address": "10363 SE 24th Ave, Portland, OR", "lat": 45.4338, "lon": -122.6370},
    {"name": "George", "address": "3816 SW Lee St, Portland, OR 97221", "lat": 45.4885, "lon": -122.7148},
    {"name": "Jasmine", "address": "3521 SE Main St, Portland, OR 97214", "lat": 45.5122, "lon": -122.6293},
]

def _load_key_locations():
    try:
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        return config.get("key_locations", _DEFAULT_KEY_LOCATIONS)
    except (FileNotFoundError, json.JSONDecodeError):
        return _DEFAULT_KEY_LOCATIONS

KEY_LOCATIONS = _load_key_locations()

def haversine_miles(lat1, lon1, lat2, lon2):
    """Calculate distance in miles between two lat/lon points."""
    R = 3959  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def geocode_address(address, api_key):
    """Get lat/lon for an address using Google Geocoding API. Returns (lat, lon) or None."""
    cache_file = os.path.join(DATA_DIR, "screenshots", f"geocode_{hash(address) & 0xFFFFFFFF}.json")
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            data = json.load(f)
            return data.get("lat"), data.get("lon")
    try:
        encoded = urllib.parse.quote(address)
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded}&key={api_key}"
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read())
            if data["status"] == "OK":
                loc = data["results"][0]["geometry"]["location"]
                with open(cache_file, "w") as f:
                    json.dump({"lat": loc["lat"], "lon": loc["lng"]}, f)
                return loc["lat"], loc["lng"]
    except Exception as e:
        print(f"  Warning: geocode failed for {address}: {e}")
    return None, None

def get_distances(address, api_key):
    """Calculate distances from listing to each key location."""
    lat, lon = geocode_address(address, api_key)
    if lat is None:
        return [{"name": loc["name"], "distance": None} for loc in KEY_LOCATIONS]
    return [
        {"name": loc["name"], "distance": round(haversine_miles(lat, lon, loc["lat"], loc["lon"]), 1)}
        for loc in KEY_LOCATIONS
    ]

def load_api_key():
    env_path = os.path.join(DATA_DIR, "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("GOOGLE_MAPS_API_KEY="):
                    return line.strip().split("=", 1)[1]
    return os.environ.get("GOOGLE_MAPS_API_KEY", "")

def img_to_base64(path):
    """Convert image file to base64 data URI."""
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"

def fetch_google_image(url, cache_path):
    """Download a Google API image, caching to disk."""
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 1000:
        return img_to_base64(cache_path)
    try:
        urllib.request.urlretrieve(url, cache_path)
        if os.path.getsize(cache_path) > 1000:
            return img_to_base64(cache_path)
    except Exception as e:
        print(f"  Warning: failed to fetch {cache_path}: {e}")
    return None

def get_map_and_streetview(listing_id, address, api_key, screenshot_dir):
    """Get static map and street view images for an address."""
    encoded = urllib.parse.quote(address)
    results = {}

    # Static Map (400x300, zoom 15, with marker)
    map_url = (f"https://maps.googleapis.com/maps/api/staticmap?"
               f"center={encoded}&zoom=13&size=400x300&maptype=roadmap"
               f"&markers=color:red|{encoded}&key={api_key}")
    map_path = os.path.join(screenshot_dir, f"{listing_id}-map.jpg")
    results["map"] = fetch_google_image(map_url, map_path)

    # Street View (400x300)
    sv_url = (f"https://maps.googleapis.com/maps/api/streetview?"
              f"size=400x300&location={encoded}&key={api_key}")
    sv_path = os.path.join(screenshot_dir, f"{listing_id}-streetview.jpg")
    results["streetview"] = fetch_google_image(sv_url, sv_path)

    return results

# Streets known for well-rated independent restaurants/cafes
INDIE_FOOD_CORRIDORS = [
    "hawthorne", "division", "belmont", "clinton", "alberta",
    "mississippi", "williams", "nw 23rd", "nw 21st", "foster",
    "woodstock", "se 13th", "milwaukie",
]

# Streets dominated by chain restaurants (detract from score)
CHAIN_CORRIDORS = ["82nd", "outer powell", "outer sandy"]

# Main streets for location scoring
MAIN_STREETS = [
    "hawthorne", "division", "belmont", "powell", "broadway",
    "sandy", "mlk", "martin luther king", "82nd", "foster",
    "woodstock", "milwaukie", "clinton", "12th", "burnside",
    "nw 23rd", "nw 21st", "macadam", "alberta", "mississippi",
    "williams",
]


def _food_score(address, neighborhood):
    """Score food proximity (12%): indie food corridors high, chain corridors low."""
    addr = address.lower()
    hood = (neighborhood or "").lower()
    # Check chain corridors first (detract)
    if any(c in addr for c in CHAIN_CORRIDORS):
        return 2
    # Check indie food corridors
    if any(c in addr or c in hood for c in INDIE_FOOD_CORRIDORS):
        return 12
    # Inner neighborhoods generally have some indie food nearby
    inner_hoods = ["buckman", "sunnyside", "ladd", "richmond", "hosford",
                   "pearl", "old town", "irvington", "grant park", "sullivan",
                   "eliot", "boise", "king", "hawthorne", "belmont"]
    if any(h in hood for h in inner_hoods):
        return 8
    return 4


def _main_street_score(address):
    """Score whether listing is on a main street (10%)."""
    addr = address.lower()
    if any(s in addr for s in MAIN_STREETS):
        return 10
    return 2


def score_listing(listing):
    """Score a rental listing on 0-100 scale per listing-evaluation rubric."""
    score = 0
    address = listing.get("address", "")
    neighborhood = listing.get("neighborhood", "")

    # Room count (12%): meets minimum = 9, exceeds = 12
    beds = listing.get("bedrooms", 0)
    score += 12 if beds >= 3 else 9 if beds >= 2 else 0

    # Kitchen quality (8%)
    if listing.get("has_kitchen"): score += 8
    elif listing.get("has_kitchenette"): score += 5
    else: score += 2

    # Price reasonableness (14%)
    price = listing.get("price", 9999)
    if price < 1800: score += 14
    elif price < 2200: score += 11
    elif price < 2800: score += 7
    elif price < 3500: score += 4
    else: score += 2

    # Square footage (8%)
    sqft = listing.get("sqft")
    if sqft and sqft > 900: score += 8
    elif sqft and sqft > 700: score += 6
    elif sqft and sqft > 500: score += 4
    else: score += 2

    # Mixed-use friendliness (8%)
    desc = listing.get("description_excerpt", "").lower()
    amenities_str = " ".join(listing.get("amenities", [])).lower()
    combined = desc + " " + amenities_str
    if any(k in combined for k in ["live/work", "mixed use", "home office"]): score += 8
    elif any(k in combined for k in ["ground floor", "commercial"]): score += 6
    elif any(k in combined for k in ["townhouse", "flex", "creative", "loft"]): score += 4
    else: score += 2

    # Fiber internet quality (10%)
    inet = listing.get("internet") or {}
    classification = inet.get("classification", "")
    if classification == "Excellent": score += 10
    elif classification == "Good": score += 4
    elif classification == "Adequate": score += 2
    # Poor/Unknown: 0

    # Food proximity — indie restaurants (12%)
    score += _food_score(address, neighborhood)

    # Main street location (10%)
    score += _main_street_score(address)

    # Hipness score (9%)
    hipness = listing.get("hipness_score")
    if hipness and hipness >= 85: score += 9
    elif hipness and hipness >= 70: score += 7
    elif hipness and hipness >= 55: score += 5
    elif hipness and hipness >= 40: score += 3
    elif hipness: score += 1

    # Safety score (9%)
    safety = listing.get("safety_score")
    if safety and safety >= 80: score += 9
    elif safety and safety >= 65: score += 7
    elif safety and safety >= 50: score += 5
    elif safety and safety >= 35: score += 3
    elif safety: score += 1

    return score

def score_breakdown(l, sc):
    address = l.get("address", "")
    neighborhood = l.get("neighborhood", "")

    beds = l.get("bedrooms", 0)
    room_score = 15 if beds >= 3 else 11 if beds >= 2 else 0
    kitchen_score = 10 if l.get("has_kitchen") else (7 if l.get("has_kitchenette") else 3)

    price = l.get("price", 9999)
    if price < 1800: price_score = 15
    elif price < 2200: price_score = 12
    elif price < 2800: price_score = 8
    elif price < 3500: price_score = 5
    else: price_score = 2

    sqft = l.get("sqft")
    if sqft and sqft > 900: sqft_score = 10
    elif sqft and sqft > 700: sqft_score = 7
    elif sqft and sqft > 500: sqft_score = 5
    else: sqft_score = 2

    desc_lower = l.get("description_excerpt", "").lower()
    amen_lower = " ".join(l.get("amenities", [])).lower()
    combined = desc_lower + " " + amen_lower
    if any(k in combined for k in ["live/work", "mixed use", "home office"]): mixed_score = 10
    elif any(k in combined for k in ["townhouse", "individual entrance", "flex"]): mixed_score = 7
    elif any(k in combined for k in ["ground floor", "creative", "loft"]): mixed_score = 5
    else: mixed_score = 2

    inet = l.get("internet", {})
    classification = inet.get("classification", "")
    if classification == "Excellent": inet_score = 10
    elif classification == "Good": inet_score = 5
    else: inet_score = 0

    food_sc = _food_score(address, neighborhood)
    main_st_sc = _main_street_score(address)

    return [
        ("Room Count", "15%", room_score, 15),
        ("Kitchen Quality", "10%", kitchen_score, 10),
        ("Price Reasonableness", "15%", price_score, 15),
        ("Square Footage", "10%", sqft_score, 10),
        ("Mixed-Use Friendliness", "10%", mixed_score, 10),
        ("Fiber Internet", "10%", inet_score, 10),
        ("Food Proximity (Indie)", "15%", food_sc, 15),
        ("Main Street Location", "15%", main_st_sc, 15),
    ]

def build_html(listings, output_path):
    now = datetime.now()
    scored = [(score_listing(l), l) for l in listings]
    scored.sort(key=lambda x: x[0], reverse=True)

    screenshot_dir = os.path.join(DATA_DIR, "screenshots")
    api_key = load_api_key()
    if api_key:
        print(f"Google Maps API key loaded. Fetching map + street view for {len(listings)} listings...")
    else:
        print("No Google Maps API key found. Skipping map and street view images.")

    total = len(listings)
    fiber_count = sum(1 for l in listings if l.get("internet", {}).get("classification") == "Excellent")

    html = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Portland SE Apartment Search Report</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
<style>
  /* ── Layout ── */
  :root {{
    --pico-font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    --pico-border-radius: 0.5rem;
  }}
  body {{ background: var(--pico-background-color); }}
  main.container {{ max-width: 960px; padding-top: 0; }}

  /* ── Cover hero ── */
  .cover {{
    text-align: center;
    padding: 4rem 2rem;
    background: linear-gradient(135deg, #1d3557 0%, #264653 100%);
    color: #fff;
    border-radius: var(--pico-border-radius);
    margin-bottom: 2.5rem;
  }}
  .cover h1 {{ color: #fff; font-size: 2.4em; margin-bottom: 0.15em; }}
  .cover .lead {{ font-size: 1.25em; font-weight: 300; opacity: 0.92; margin-bottom: 1.2em; }}
  .cover .date {{ opacity: 0.7; font-size: 0.95em; }}
  .cover .subtitle {{ opacity: 0.6; font-size: 0.85em; margin-top: 0.35em; }}
  .cover hr {{ border: none; height: 2px; background: rgba(255,255,255,0.25); width: 200px; margin: 1.5rem auto; }}
  .cover .target {{ opacity: 0.82; font-size: 0.9em; max-width: 600px; margin: 0 auto; }}
  .cover .stats {{ display: flex; justify-content: center; gap: 2rem; margin-top: 1.2rem; }}
  .cover .stat {{ text-align: center; }}
  .cover .stat-value {{ font-size: 2em; font-weight: 700; display: block; }}
  .cover .stat-label {{ font-size: 0.8em; opacity: 0.7; text-transform: uppercase; letter-spacing: 0.05em; }}

  /* ── Summary table tweaks ── */
  table {{ font-size: 0.9em; }}
  td:first-child, th:first-child {{ text-align: center; width: 3.5em; }}
  td:nth-child(4), td:nth-child(5), td:nth-child(7),
  th:nth-child(4), th:nth-child(5), th:nth-child(7) {{ text-align: center; }}
  .summary-link {{ color: var(--pico-primary); text-decoration: none; font-weight: 500; }}
  .summary-link:hover {{ text-decoration: underline; }}

  /* ── Internet badges ── */
  .internet-badge {{
    display: inline-block; padding: 0.15em 0.65em; border-radius: 1em;
    font-size: 0.8em; font-weight: 600; white-space: nowrap;
  }}
  .internet-badge.excellent {{ background: #d8f3dc; color: #1b4332; }}
  .internet-badge.good {{ background: #fff3cd; color: #856404; }}
  .internet-badge.adequate {{ background: #e2e3e5; color: #495057; }}
  .internet-badge.poor {{ background: #f8d7da; color: #842029; }}

  /* ── Listing cards (Pico <article>) ── */
  article.listing-card {{ margin-bottom: 1.75rem; padding: 0; overflow: hidden; }}
  article.listing-card > header {{
    padding: 1.25rem 1.5rem 0.75rem;
    background: transparent; border-bottom: none;
  }}
  article.listing-card > header h3 {{ color: #264653; margin-bottom: 0.2em; font-size: 1.25em; }}
  article.listing-card > header .meta {{ color: var(--pico-muted-color); font-size: 0.9em; }}

  /* ── Score bar ── */
  .score-bar {{
    height: 0.5rem; background: var(--pico-secondary-background);
    border-radius: 0.25rem; margin: 0.5rem 0; overflow: hidden;
  }}
  .score-bar .fill {{ height: 100%; border-radius: 0.25rem; transition: width 0.5s ease; }}
  .score-bar .fill.high {{ background: #2d6a4f; }}
  .score-bar .fill.mid {{ background: #e9c46a; }}
  .score-bar .fill.low {{ background: #e76f51; }}

  /* ── Photo gallery ── */
  .gallery {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px; padding: 0 4px; }}
  .gallery img {{
    width: 100%; height: 220px; object-fit: cover;
    border-radius: var(--pico-border-radius);
    cursor: pointer; transition: transform 0.2s, filter 0.2s;
  }}
  .gallery img:hover {{ transform: scale(1.015); filter: brightness(1.05); }}
  .gallery.single {{ grid-template-columns: 1fr; }}
  .gallery.single img {{ height: 360px; }}

  /* ── Lightbox ── */
  .lightbox {{
    display: none; position: fixed; inset: 0;
    background: rgba(0,0,0,0.92); z-index: 9999;
    justify-content: center; align-items: center; cursor: pointer;
  }}
  .lightbox.active {{ display: flex; }}
  .lightbox img {{ max-width: 90%; max-height: 90%; object-fit: contain; border-radius: 0.5rem; }}

  /* ── Location row (map + street view) ── */
  .location-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px; padding: 4px 4px 0; }}
  .location-row .loc-card {{ position: relative; border-radius: var(--pico-border-radius); overflow: hidden; }}
  .location-row img {{ width: 100%; height: 180px; object-fit: cover; display: block; }}
  .location-row .loc-label {{
    position: absolute; bottom: 0; left: 0; right: 0;
    background: linear-gradient(transparent, rgba(0,0,0,0.65));
    color: #fff; padding: 0.5rem 0.75rem 0.35rem;
    font-size: 0.75em; font-weight: 600;
  }}

  /* ── Distance badges ── */
  .distances {{ display: flex; gap: 0.75rem; padding: 0.5rem 0.25rem 0; flex-wrap: wrap; }}
  .distance-badge {{
    background: var(--pico-secondary-background);
    border: 1px solid var(--pico-muted-border-color);
    border-radius: 1rem; padding: 0.25rem 0.75rem;
    font-size: 0.8em; color: var(--pico-color);
  }}
  .distance-badge .name {{ font-weight: 600; }}

  /* ── Listing body ── */
  .listing-body {{ padding: 1rem 1.5rem 1.25rem; }}
  .listing-body p {{ margin-bottom: 0.5rem; font-size: 0.9em; }}
  .listing-link {{
    display: inline-block; margin-top: 0.5rem;
    font-size: 0.85em; font-weight: 600;
  }}
</style>
</head>
<body>
<main class="container">

  <div class="cover">
    <h1>Portland SE Apartment Search</h1>
    <p class="lead">Live/Work Space Report</p>
    <div class="date">{now.strftime("%B %d, %Y at %I:%M %p")}</div>
    <div class="subtitle">Inner SE Portland &middot; Powell &amp; Division Corridors</div>
    <hr>
    <div class="target">Target: 2+ bedroom apartments with kitchen, suitable for live/work use, with reliable fiber internet connectivity.</div>
    <div class="stats">
      <div class="stat"><span class="stat-value">{total}</span><span class="stat-label">Listings</span></div>
      <div class="stat"><span class="stat-value">{fiber_count}</span><span class="stat-label">Fiber Available</span></div>
    </div>
  </div>

  <section>
  <h2>Summary Rankings</h2>
  <figure>
  <table role="grid">
    <thead><tr><th>Rank</th><th>Address</th><th>Neighborhood</th><th>Price</th><th>Beds/Bath</th><th>Internet</th><th>Score</th></tr></thead>
    <tbody>
"""

    for i, (sc, l) in enumerate(scored, 1):
        inet = l.get("internet") or {}
        inet_class = inet.get("classification", "Unknown").lower()
        inet_label = inet.get("classification", "Unknown")
        listing_anchor = f"listing-{l['id']}"
        html += f"""    <tr>
      <td>{i}</td>
      <td><a href="#{listing_anchor}" class="summary-link">{l.get("address", "Unknown").split(",")[0]}</a></td>
      <td>{l.get("neighborhood", "")}</td>
      <td>${l.get("price", 0):,}</td>
      <td>{l.get("bedrooms", 0)}BR/{l.get("bathrooms", 0)}BA</td>
      <td><span class="internet-badge {inet_class}">{inet_label}</span></td>
      <td><strong>{sc}/100</strong></td>
    </tr>\n"""

    html += "    </tbody>\n  </table>\n  </figure>\n  </section>\n\n  <section>\n  <h2>Detailed Listings</h2>\n\n"

    for rank, (sc, l) in enumerate(scored, 1):
        # Gather photos
        photos = []
        for i in range(1, 9):
            p = os.path.join(screenshot_dir, f"{l['id']}-{i}.jpg")
            b64 = img_to_base64(p)
            if b64:
                photos.append(b64)
        if not photos:
            single = os.path.join(screenshot_dir, f"{l['id']}.jpg")
            b64 = img_to_base64(single)
            if b64:
                photos.append(b64)

        grid_class = "single" if len(photos) == 1 else ""
        sqft_str = f" | {l['sqft']} sqft" if l.get("sqft") else ""
        inet = l.get("internet", {})
        inet_class = inet.get("classification", "").lower()
        amenities_str = ", ".join(l.get("amenities", []))
        breakdown = score_breakdown(l, sc)
        bar_class = "high" if sc >= 75 else "mid" if sc >= 60 else "low"

        listing_anchor = f"listing-{l['id']}"
        html += f"""  <article class="listing-card" id="{listing_anchor}">
    <header>
      <h3>#{rank} &mdash; {l["address"].split(",")[0]}</h3>
      <div class="meta">{l["neighborhood"]} &middot; ${l["price"]:,}/mo &middot; {l["bedrooms"]}BR/{l["bathrooms"]}BA{sqft_str}</div>
      <div class="score-bar"><div class="fill {bar_class}" style="width: {sc}%"></div></div>
    </header>
    <div class="gallery {grid_class}">\n"""

        for photo in photos:
            html += f'      <img src="{photo}" onclick="openLightbox(this.src)" alt="Listing photo">\n'

        html += "    </div>\n"

        # Map + Street View row
        maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(l['address'])}"
        if api_key:
            google_imgs = get_map_and_streetview(l["id"], l["address"], api_key, screenshot_dir)
            map_b64 = google_imgs.get("map")
            sv_b64 = google_imgs.get("streetview")
            if map_b64 or sv_b64:
                html += '    <div class="location-row">\n'
                if sv_b64:
                    html += f'      <div class="loc-card"><img src="{sv_b64}" onclick="openLightbox(this.src)" alt="Street View"><div class="loc-label">Street View</div></div>\n'
                if map_b64:
                    html += f'      <div class="loc-card"><a href="{maps_url}" target="_blank"><img src="{map_b64}" alt="Map"><div class="loc-label">Map (click to open)</div></a></div>\n'
                html += '    </div>\n'

        # Distance badges
        if api_key:
            distances = get_distances(l["address"], api_key)
            html += '    <div class="distances" style="padding: 4px 4px 0;">\n'
            for d in distances:
                dist_str = f"{d['distance']} mi" if d['distance'] is not None else "N/A"
                html += f'      <span class="distance-badge"><span class="name">{d["name"]}</span>: {dist_str}</span>\n'
            html += '    </div>\n'

        html += f"""    <div class="listing-body">
      <p><strong>Description:</strong> {l["description_excerpt"]}</p>
      <p><strong>Amenities:</strong> {amenities_str}</p>
      <p><strong>Internet</strong> <span class="internet-badge {inet_class}">{inet.get("classification", "N/A")}</span>: {inet.get("broadbandnow_summary", "No data")}</p>
      <a href="{l["url"]}" class="listing-link" target="_blank">View listing on Craigslist &rarr;</a>
    </div>
  </article>\n\n"""

    # Methodology
    html += """  </section>

  <section>
  <article>
    <h2>Methodology</h2>
    <h4>Data Sources</h4>
    <p>Listings sourced from Craigslist Portland (apartments/housing for rent), filtered to 2+ bedrooms within a 3-mile radius of zip code 97202 in Inner SE Portland.</p>
    <p>Internet availability checked at each specific street address using BroadbandNow.com's address-level lookup tool.</p>

    <h4>Scoring Rubric (0&ndash;100)</h4>
    <figure>
    <table>
      <thead><tr><th>Factor</th><th>Weight</th><th>Criteria</th></tr></thead>
      <tbody>
      <tr><td>Room Count</td><td>15%</td><td>2 rooms = 11pts, 3+ rooms = 15pts</td></tr>
      <tr><td>Kitchen Quality</td><td>10%</td><td>Full kitchen = 10pts, kitchenette = 7pts</td></tr>
      <tr><td>Price</td><td>15%</td><td>&lt;$1,800 = 15pts, $1,800-2,200 = 12pts, $2,200-2,800 = 8pts</td></tr>
      <tr><td>Square Footage</td><td>10%</td><td>&gt;900 sqft = 10pts, 700-900 = 7pts, &lt;700 = 2pts</td></tr>
      <tr><td>Mixed-Use Friendliness</td><td>10%</td><td>Live/work keywords = 10pts, townhouse = 7pts, none = 2pts</td></tr>
      <tr><td>Fiber Internet</td><td>10%</td><td>Excellent (fiber) = 10pts, Good (cable) = 5pts</td></tr>
      <tr><td>Food Proximity (Indie)</td><td>15%</td><td>Indie food corridor = 15pts, mixed = 10pts, chains = 5pts, chain-heavy = 2pts</td></tr>
      <tr><td>Main Street Location</td><td>15%</td><td>On main street = 15pts, 1-2 blocks = 11pts, not near = 3pts</td></tr>
      </tbody>
    </table>
    </figure>

    <h4>Target Neighborhoods</h4>
    <p>Hosford-Abernethy, Richmond, Creston-Kenilworth, Brooklyn, Buckman, and Sunnyside in Inner SE Portland.</p>

    <h4>Internet Classification</h4>
    <p><strong>Excellent:</strong> Fiber available (940+ Mbps symmetric). <strong>Good:</strong> Gigabit cable (2 Gbps) but no fiber. <strong>Adequate:</strong> Cable &lt;500 Mbps. <strong>Poor:</strong> DSL only.</p>
  </article>
  </section>
"""

    html += f"""
  <footer>
    <p><small>Report generated {now.strftime("%B %d, %Y at %I:%M %p")}. Data may change; verify listings and internet availability before signing a lease.</small></p>
  </footer>

</main>

<div class="lightbox" id="lightbox" onclick="closeLightbox()">
  <img id="lightbox-img" src="" alt="Full size">
</div>

<script>
function openLightbox(src) {{
  document.getElementById('lightbox-img').src = src;
  document.getElementById('lightbox').classList.add('active');
}}
function closeLightbox() {{
  document.getElementById('lightbox').classList.remove('active');
}}
document.addEventListener('keydown', function(e) {{
  if (e.key === 'Escape') closeLightbox();
}});
</script>

</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(html)
    print(f"HTML report generated: {output_path}")

if __name__ == "__main__":
    with open(os.path.join(DATA_DIR, "listings.json")) as f:
        listings = json.load(f)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    output_path = os.path.join(DATA_DIR, f"portland-apartment-report-{timestamp}.html")
    build_html(listings, output_path)
