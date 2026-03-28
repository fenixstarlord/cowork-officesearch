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

DATA_DIR = "/Users/dit/github/cowork-aparmentsearch/data"

# Key locations for distance calculations
KEY_LOCATIONS = [
    {"name": "Chris", "address": "10363 SE 24th Ave, Portland, OR", "lat": 45.4338, "lon": -122.6370},
    {"name": "George", "address": "3816 SW Lee St, Portland, OR 97221", "lat": 45.4885, "lon": -122.7148},
    {"name": "Jasmine", "address": "SE 39th and Hawthorne, Portland, OR", "lat": 45.5118, "lon": -122.6209},
]

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
    env_path = os.path.join(DATA_DIR, ".env")
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

def score_listing(listing):
    score = 0

    # Room count (20%): meets minimum = 15, exceeds = 20
    beds = listing.get("bedrooms", 0)
    score += 20 if beds >= 3 else 15 if beds >= 2 else 0

    # Kitchen quality (15%)
    if listing.get("has_kitchen"): score += 15
    elif listing.get("has_kitchenette"): score += 10
    else: score += 5

    # Price reasonableness (20%)
    price = listing.get("price", 9999)
    if price < 1800: score += 20
    elif price < 2200: score += 16
    elif price < 2800: score += 10
    elif price < 3500: score += 6
    else: score += 3

    # Square footage (15%)
    sqft = listing.get("sqft")
    if sqft and sqft > 900: score += 15
    elif sqft and sqft > 700: score += 11
    elif sqft and sqft > 500: score += 7
    else: score += 3

    # Mixed-use friendliness (15%)
    desc = listing.get("description_excerpt", "").lower()
    amenities_str = " ".join(listing.get("amenities", [])).lower()
    combined = desc + " " + amenities_str
    if any(k in combined for k in ["live/work", "mixed use", "home office"]): score += 15
    elif any(k in combined for k in ["townhouse", "individual entrance", "flex"]): score += 11
    elif any(k in combined for k in ["ground floor", "creative", "loft"]): score += 7
    else: score += 3

    # Fiber internet quality (15%)
    inet = listing.get("internet", {})
    qf = inet.get("quantum_fiber", {})
    cl = inet.get("centurylink", {})
    if qf.get("available") and qf.get("max_down", 0) >= 8000: score += 15
    elif (qf.get("available") or cl.get("available")) and cl.get("fiber"): score += 12
    elif inet.get("classification") == "Good": score += 5
    elif inet.get("classification") == "Adequate": score += 3

    return score

def score_breakdown(l, sc):
    beds = l.get("bedrooms", 0)
    room_score = 20 if beds >= 3 else 15
    kitchen_score = 15 if l.get("has_kitchen") else (10 if l.get("has_kitchenette") else 5)

    neighborhood = l.get("neighborhood", "")
    address = l.get("address", "").lower()
    if any(k in address for k in ["powell", "division", "holgate"]): prox_score = 20
    elif neighborhood in ["Hosford-Abernethy", "Creston-Kenilworth", "Brooklyn"]: prox_score = 15
    elif neighborhood in ["Buckman", "Richmond", "Sunnyside"]: prox_score = 10
    else: prox_score = 5

    price = l.get("price", 9999)
    if price < 1800: price_score = 15
    elif price < 2200: price_score = 12
    elif price < 2800: price_score = 8
    elif price < 3500: price_score = 5
    else: price_score = 3

    sqft = l.get("sqft")
    if sqft and sqft > 900: sqft_score = 10
    elif sqft and sqft > 700: sqft_score = 7
    elif sqft and sqft > 500: sqft_score = 4
    else: sqft_score = 2

    desc_lower = l.get("description_excerpt", "").lower()
    amen_lower = " ".join(l.get("amenities", [])).lower()
    combined = desc_lower + " " + amen_lower
    if any(k in combined for k in ["live/work", "mixed use", "home office"]): mixed_score = 10
    elif any(k in combined for k in ["townhouse", "individual entrance", "flex"]): mixed_score = 7
    elif any(k in combined for k in ["ground floor", "creative", "loft"]): mixed_score = 5
    else: mixed_score = 3

    inet = l.get("internet", {})
    classification = inet.get("classification", "")
    if classification == "Excellent": inet_score = 10
    elif classification == "Good": inet_score = 5
    else: inet_score = 0

    return [
        ("Room Count", "20%", room_score, 20),
        ("Kitchen Quality", "15%", kitchen_score, 15),
        ("Powell/Division Proximity", "20%", prox_score, 20),
        ("Price Reasonableness", "15%", price_score, 15),
        ("Square Footage", "10%", sqft_score, 10),
        ("Mixed-Use Friendliness", "10%", mixed_score, 10),
        ("Fiber Internet", "10%", inet_score, 10),
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

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Portland SE Apartment Search Report</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #333; background: #f8f9fa; line-height: 1.5; }}
  .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}

  /* Cover */
  .cover {{ text-align: center; padding: 80px 20px; background: linear-gradient(135deg, #1d3557 0%, #264653 100%); color: white; border-radius: 12px; margin-bottom: 40px; }}
  .cover h1 {{ font-size: 2.4em; margin-bottom: 4px; font-weight: 700; }}
  .cover h2 {{ font-size: 1.4em; font-weight: 300; opacity: 0.9; margin-bottom: 20px; }}
  .cover .date {{ opacity: 0.7; font-size: 0.95em; }}
  .cover .subtitle {{ opacity: 0.6; font-size: 0.85em; margin-top: 6px; }}
  .cover hr {{ border: none; height: 2px; background: rgba(255,255,255,0.3); width: 200px; margin: 24px auto; }}
  .cover .target {{ opacity: 0.8; font-size: 0.9em; max-width: 600px; margin: 0 auto; }}

  /* Summary table */
  .section-header {{ font-size: 1.5em; color: #1d3557; margin: 30px 0 16px; font-weight: 700; border-bottom: 3px solid #1d3557; padding-bottom: 8px; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; }}
  th {{ background: #264653; color: white; padding: 10px 12px; font-size: 0.85em; text-align: center; }}
  th:nth-child(2) {{ text-align: left; }}
  td {{ padding: 10px 12px; font-size: 0.85em; text-align: center; border-bottom: 1px solid #dee2e6; }}
  td:nth-child(2) {{ text-align: left; }}
  tr:nth-child(even) {{ background: #f1faee; }}
  tr:hover {{ background: #e8f4f8; }}

  /* Listing cards */
  .listing-card {{ background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 28px; overflow: hidden; }}
  .listing-header {{ padding: 20px 24px 12px; }}
  .listing-header h3 {{ color: #2d6a4f; font-size: 1.3em; margin-bottom: 4px; }}
  .listing-header .meta {{ color: #6c757d; font-size: 0.9em; }}

  /* Photo gallery */
  .gallery {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px; padding: 0 4px; }}
  .gallery img {{ width: 100%; height: 220px; object-fit: cover; border-radius: 4px; cursor: pointer; transition: transform 0.2s; }}
  .gallery img:hover {{ transform: scale(1.02); }}
  .gallery.single {{ grid-template-columns: 1fr; }}
  .gallery.single img {{ height: 360px; }}

  /* Lightbox */
  .lightbox {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 1000; justify-content: center; align-items: center; cursor: pointer; }}
  .lightbox.active {{ display: flex; }}
  .lightbox img {{ max-width: 90%; max-height: 90%; object-fit: contain; border-radius: 8px; }}

  /* Location row (map + street view) */
  .location-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px; padding: 4px 4px 0; }}
  .location-row .loc-card {{ position: relative; border-radius: 4px; overflow: hidden; }}
  .location-row img {{ width: 100%; height: 180px; object-fit: cover; display: block; }}
  .location-row .loc-label {{ position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(transparent, rgba(0,0,0,0.7)); color: white; padding: 8px 12px 6px; font-size: 0.75em; font-weight: 600; }}

  /* Details */
  .listing-body {{ padding: 16px 24px 20px; }}
  .listing-body p {{ margin-bottom: 8px; font-size: 0.9em; }}
  .listing-body strong {{ color: #1d3557; }}
  .internet-badge {{ display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.8em; font-weight: 600; }}
  .internet-badge.excellent {{ background: #d8f3dc; color: #2d6a4f; }}
  .internet-badge.good {{ background: #fff3cd; color: #856404; }}

  /* Score breakdown */
  .score-section {{ margin-top: 12px; }}
  .score-table {{ width: auto; margin: 8px 0; }}
  .score-table th {{ background: #2d6a4f; font-size: 0.8em; padding: 6px 12px; }}
  .score-table td {{ font-size: 0.8em; padding: 6px 12px; }}
  .score-table tr:last-child {{ background: #d8f3dc; font-weight: 700; }}
  .score-total {{ font-size: 1.4em; font-weight: 700; color: #2d6a4f; float: right; margin-top: -36px; }}

  /* Score bar */
  .score-bar {{ height: 8px; background: #e9ecef; border-radius: 4px; margin: 4px 0; overflow: hidden; }}
  .score-bar .fill {{ height: 100%; border-radius: 4px; transition: width 0.5s; }}
  .score-bar .fill.high {{ background: #2d6a4f; }}
  .score-bar .fill.mid {{ background: #f4a261; }}
  .score-bar .fill.low {{ background: #e76f51; }}

  .listing-link {{ display: inline-block; margin-top: 8px; color: #1d3557; text-decoration: none; font-size: 0.85em; font-weight: 600; }}
  .listing-link:hover {{ text-decoration: underline; }}

  /* Distance badges */
  .distances {{ display: flex; gap: 12px; margin: 8px 0; flex-wrap: wrap; }}
  .distance-badge {{ background: #e8f4f8; border: 1px solid #a8dadc; border-radius: 16px; padding: 4px 12px; font-size: 0.8em; color: #1d3557; }}
  .distance-badge .name {{ font-weight: 600; }}

  /* Summary links */
  .summary-link {{ color: #1d3557; text-decoration: none; }}
  .summary-link:hover {{ text-decoration: underline; color: #2d6a4f; }}

  /* Methodology */
  .methodology {{ background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); padding: 24px; margin-top: 20px; }}
  .methodology h4 {{ color: #1d3557; margin: 16px 0 8px; }}
  .methodology p {{ font-size: 0.9em; margin-bottom: 8px; }}
  .methodology table {{ margin: 12px 0; }}

  .footer {{ text-align: center; color: #6c757d; font-size: 0.8em; padding: 30px 0; }}
</style>
</head>
<body>
<div class="container">

  <div class="cover">
    <h1>Portland SE Apartment Search</h1>
    <h2>Live/Work Space Report</h2>
    <div class="date">{now.strftime("%B %d, %Y at %I:%M %p")}</div>
    <div class="subtitle">Inner SE Portland | Powell &amp; Division Corridors</div>
    <hr>
    <div class="target">Target: 2+ bedroom apartments with kitchen, suitable for live/work use, with reliable fiber internet connectivity.</div>
  </div>

  <h2 class="section-header">Summary Rankings</h2>
  <table>
    <tr><th>Rank</th><th>Address</th><th>Neighborhood</th><th>Price</th><th>Beds/Bath</th><th>Internet</th><th>Score</th></tr>
"""

    for i, (sc, l) in enumerate(scored, 1):
        inet_class = l["internet"]["classification"].lower()
        listing_anchor = f"listing-{l['id']}"
        html += f"""    <tr>
      <td>{i}</td>
      <td><a href="#{listing_anchor}" class="summary-link">{l["address"].split(",")[0]}</a></td>
      <td>{l["neighborhood"]}</td>
      <td>${l["price"]:,}</td>
      <td>{l["bedrooms"]}BR/{l["bathrooms"]}BA</td>
      <td><span class="internet-badge {inet_class}">{l["internet"]["classification"]}</span></td>
      <td><strong>{sc}/100</strong></td>
    </tr>\n"""

    html += "  </table>\n\n  <h2 class=\"section-header\">Detailed Listings</h2>\n\n"

    for rank, (sc, l) in enumerate(scored, 1):
        # Gather photos
        photos = []
        for i in range(1, 5):
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
        html += f"""  <div class="listing-card" id="{listing_anchor}">
    <div class="listing-header">
      <h3>#{rank} &mdash; {l["address"].split(",")[0]}</h3>
      <div class="meta">{l["neighborhood"]} | ${l["price"]:,}/mo | {l["bedrooms"]}BR/{l["bathrooms"]}BA{sqft_str}</div>
      <div class="score-bar"><div class="fill {bar_class}" style="width: {sc}%"></div></div>
    </div>
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
  </div>\n\n"""

    # Methodology
    html += """  <div class="methodology">
    <h2 class="section-header">Methodology</h2>
    <h4>Data Sources</h4>
    <p>Listings sourced from Craigslist Portland (apartments/housing for rent), filtered to 2+ bedrooms within a 3-mile radius of zip code 97202 in Inner SE Portland.</p>
    <p>Internet availability checked at each specific street address using BroadbandNow.com's address-level lookup tool.</p>

    <h4>Scoring Rubric (0-100)</h4>
    <table>
      <tr><th>Factor</th><th>Weight</th><th>Criteria</th></tr>
      <tr><td>Room Count</td><td>20%</td><td>2 rooms = 15pts, 3+ rooms = 20pts</td></tr>
      <tr><td>Kitchen Quality</td><td>15%</td><td>Full kitchen = 15pts, kitchenette = 10pts</td></tr>
      <tr><td>Powell/Division Proximity</td><td>20%</td><td>On corridor = 20pts, adjacent = 15pts, nearby = 10pts</td></tr>
      <tr><td>Price</td><td>15%</td><td>&lt;$1,800 = 15pts, $1,800-2,200 = 12pts, $2,200-2,800 = 8pts</td></tr>
      <tr><td>Square Footage</td><td>10%</td><td>&gt;900 sqft = 10pts, 700-900 = 7pts, &lt;700 = 4pts</td></tr>
      <tr><td>Mixed-Use Friendliness</td><td>10%</td><td>Live/work keywords = 10pts, townhouse = 7pts, none = 3pts</td></tr>
      <tr><td>Fiber Internet</td><td>10%</td><td>Excellent (fiber) = 10pts, Good (cable) = 5pts</td></tr>
    </table>

    <h4>Target Neighborhoods</h4>
    <p>Hosford-Abernethy, Richmond, Creston-Kenilworth, Brooklyn, Buckman, and Sunnyside in Inner SE Portland.</p>

    <h4>Internet Classification</h4>
    <p>Excellent: Fiber available (940+ Mbps symmetric). Good: Gigabit cable (2 Gbps) but no fiber. Adequate: Cable &lt;500 Mbps. Poor: DSL only.</p>
  </div>
"""

    html += f"""
  <div class="footer">
    Report generated {now.strftime("%B %d, %Y at %I:%M %p")}. Data may change; verify listings and internet availability before signing a lease.
  </div>

</div>

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
