"""HTML report generation service.

Replaces the report-builder agent. Generates self-contained HTML reports
with Leaflet.js interactive maps, photo galleries, and scoring.
"""

from __future__ import annotations

import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiohttp
from jinja2 import Template

import config
from services.geocoding import geocode, get_google_maps_image_url, get_street_view_url
from utils.schemas import Listing

logger = logging.getLogger(__name__)

REPORT_TEMPLATE = Template("""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9/dist/leaflet.js"></script>
<style>
  :root { --pico-font-size: 15px; }
  body { padding: 1rem; }
  .listing-card { border: 1px solid var(--pico-muted-border-color); border-radius: 8px; padding: 1rem; margin-bottom: 1.5rem; }
  .listing-card.fav { border-left: 4px solid gold; }
  .listing-card.rejected { opacity: 0.5; }
  .score-bar { display: inline-block; width: 100px; height: 12px; background: #eee; border-radius: 6px; overflow: hidden; vertical-align: middle; }
  .score-fill { height: 100%; border-radius: 6px; }
  .score-excellent .score-fill { background: #27ae60; }
  .score-good .score-fill { background: #2ecc71; }
  .score-ok .score-fill { background: #f39c12; }
  .score-poor .score-fill { background: #e74c3c; }
  .gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; margin: 0.5rem 0; }
  .gallery img { width: 100%; height: 120px; object-fit: cover; border-radius: 4px; cursor: pointer; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; }
  .badge-new { background: #3498db; color: white; }
  .badge-fav { background: gold; color: #333; }
  .badge-reviewed { background: #95a5a6; color: white; }
  #map { height: 400px; border-radius: 8px; margin-bottom: 2rem; }
  .maps-row { display: flex; gap: 8px; margin: 0.5rem 0; }
  .maps-row img { width: 50%; border-radius: 4px; }
  .stats { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 2rem; }
  .stat-card { background: var(--pico-card-background-color); padding: 1rem; border-radius: 8px; text-align: center; min-width: 120px; }
  .stat-card .value { font-size: 1.5rem; font-weight: bold; }
  .lightbox { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 9999; align-items: center; justify-content: center; }
  .lightbox.active { display: flex; }
  .lightbox img { max-width: 90%; max-height: 90%; }
  .trend-up { color: #e74c3c; }
  .trend-down { color: #27ae60; }
  .trend-stable { color: #95a5a6; }
</style>
</head>
<body>
<main class="container">
<h1>{{ title }}</h1>
<p>Generated {{ date }} | {{ listings|length }} listings</p>

<!-- Stats -->
<div class="stats">
  <div class="stat-card"><div class="value">{{ listings|length }}</div><div>Listings</div></div>
  <div class="stat-card"><div class="value">${{ price_min|int }}-${{ price_max|int }}</div><div>Price Range</div></div>
  {% if top_score %}<div class="stat-card"><div class="value">{{ top_score }}/100</div><div>Top Score</div></div>{% endif %}
  <div class="stat-card"><div class="value">{{ neighborhoods }}</div><div>Neighborhoods</div></div>
</div>

<!-- Interactive Map -->
{% if include_map %}
<div id="map"></div>
{% endif %}

<!-- Listings -->
{% for l in listings %}
<article class="listing-card {{ 'fav' if l._status == 'FAV' else ('rejected' if l._status == 'REJ' else '') }}">
  <header>
    <h3>
      {% if l._status == 'FAV' %}<span class="badge badge-fav">FAV</span>{% endif %}
      {% if l.is_new %}<span class="badge badge-new">NEW</span>{% endif %}
      <a href="{{ l.url }}">{{ l.address }}</a>
    </h3>
    <p>
      <strong>${{ "{:,.0f}".format(l.price) }}{{ "/mo" if mode == "rental" else "" }}</strong>
      | {{ l.bedrooms }}bd/{{ l.bathrooms }}ba
      {% if l.sqft %}| {{ "{:,}".format(l.sqft) }} sqft{% endif %}
      | {{ l.neighborhood }}
      {% if l.listing_type != "residential" %}({{ l.listing_type }}){% endif %}
    </p>
  </header>

  {% if l.total_score %}
  <p>
    Score:
    <span class="score-bar {{ 'score-excellent' if l.total_score >= 80 else ('score-good' if l.total_score >= 65 else ('score-ok' if l.total_score >= 50 else 'score-poor')) }}">
      <span class="score-fill" style="width: {{ l.total_score }}%"></span>
    </span>
    <strong>{{ l.total_score }}/100</strong>
  </p>
  {% endif %}

  {% if l.price_trend %}
  <p class="{{ 'trend-down' if l.price_trend == 'dropping' else ('trend-up' if l.price_trend == 'rising' else 'trend-stable') }}">
    {{ "↓" if l.price_trend == "dropping" else ("↑" if l.price_trend == "rising" else "→") }} {{ l.price_trend }}
    {% if l.days_on_market %}({{ l.days_on_market }} days on market){% endif %}
  </p>
  {% endif %}

  {% if l._photos %}
  <div class="gallery">
    {% for photo in l._photos %}<img src="{{ photo }}" onclick="openLightbox(this.src)" alt="Photo">{% endfor %}
  </div>
  {% endif %}

  {% if l._map_url or l._streetview_url %}
  <div class="maps-row">
    {% if l._map_url %}<img src="{{ l._map_url }}" alt="Map">{% endif %}
    {% if l._streetview_url %}<img src="{{ l._streetview_url }}" alt="Street View">{% endif %}
  </div>
  {% endif %}

  <details>
    <summary>Details</summary>
    {% if l.internet %}
    <p><strong>Internet:</strong> {{ l.internet.classification }} ({{ l.internet.providers_found }} providers) — {{ l.internet.broadbandnow_summary }}</p>
    {% endif %}
    {% if l.hipness_tier %}<p><strong>Hipness:</strong> {{ l.hipness_score }}/100 — {{ l.hipness_tier }}</p>{% endif %}
    {% if l.safety_tier %}<p><strong>Safety:</strong> {{ l.safety_score }}/100 — {{ l.safety_tier }}</p>{% endif %}
    {% if l.amenities %}<p><strong>Amenities:</strong> {{ l.amenities|join(", ") }}</p>{% endif %}
    {% if l.description_excerpt %}<p>{{ l.description_excerpt }}</p>{% endif %}
    {% if l._distances %}<p><strong>Distances:</strong> {% for name, dist in l._distances.items() %}{{ name }}: {{ dist }} mi {% endfor %}</p>{% endif %}
    {% if l.also_listed_on %}<p><strong>Also on:</strong> {% for a in l.also_listed_on %}{{ a.source }} {% endfor %}</p>{% endif %}
    {% if l.lease_terms and mode == "rental" %}
    <p><strong>Terms:</strong>
      {% if l.lease_terms.deposit %}Deposit: ${{ "{:,.0f}".format(l.lease_terms.deposit) }} | {% endif %}
      {% if l.lease_terms.pet_policy %}Pets: {{ l.lease_terms.pet_policy }} | {% endif %}
      {% if l.lease_terms.parking %}Parking: {{ l.lease_terms.parking }}{% endif %}
    </p>
    {% endif %}
    {% if l.sale_terms and mode == "purchase" %}
    <p><strong>Terms:</strong>
      {% if l.sale_terms.property_tax_annual %}Tax: ${{ "{:,.0f}".format(l.sale_terms.property_tax_annual) }}/yr | {% endif %}
      {% if l.sale_terms.hoa_monthly %}HOA: ${{ "{:,.0f}".format(l.sale_terms.hoa_monthly) }}/mo | {% endif %}
      {% if l.sale_terms.zoning %}Zoning: {{ l.sale_terms.zoning }}{% endif %}
    </p>
    {% endif %}
  </details>

  <footer>
    <small>Source: {{ l.source }}{% if l.also_listed_on %} + {{ l.also_listed_on|length }} more{% endif %} | ID: {{ l.id }}</small>
  </footer>
</article>
{% endfor %}

</main>

<!-- Lightbox -->
<div class="lightbox" id="lightbox" onclick="this.classList.remove('active')">
  <img id="lightbox-img" src="" alt="Full size">
</div>
<script>
function openLightbox(src) {
  document.getElementById('lightbox-img').src = src;
  document.getElementById('lightbox').classList.add('active');
}
</script>

{% if include_map %}
<script>
const map = L.map('map').setView([45.5152, -122.6784], 12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);
{% for l in listings %}
{% if l._lat and l._lng %}
L.circleMarker([{{ l._lat }}, {{ l._lng }}], {
  radius: 8,
  fillColor: '{{ "#27ae60" if l.total_score >= 80 else ("#2ecc71" if l.total_score >= 65 else ("#f39c12" if l.total_score >= 50 else "#e74c3c")) }}',
  color: '#fff', weight: 2, fillOpacity: 0.9
}).addTo(map).bindPopup('<b>{{ l.address }}</b><br>${{ "{:,.0f}".format(l.price) }}<br>Score: {{ l.total_score }}/100<br><a href="{{ l.url }}">View</a>');
{% endif %}
{% endfor %}
// Key locations
{% for loc in key_locations %}
L.marker([{{ loc.lat }}, {{ loc.lng }}], {
  icon: L.divIcon({html: '<div style="background:blue;color:white;padding:2px 6px;border-radius:4px;font-size:11px">{{ loc.name }}</div>', className: ''})
}).addTo(map);
{% endfor %}
</script>
{% endif %}
</body>
</html>
""")


async def build_report(
    listings: list[Listing],
    mode: str = "rental",
    progress_callback=None,
) -> Path:
    """Generate an HTML report and return the file path."""
    from services.favorites import FavoritesManager
    from services.geocoding import distances_to_key_locations

    cfg = config.load_config()
    fav_mgr = FavoritesManager()
    include_map = cfg["report_settings"]["include_interactive_map"]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")

    if mode == "rental":
        filename = f"portland-apartment-report-{timestamp}.html"
        title = "Portland Rental Report"
    else:
        filename = f"portland-purchase-report-{timestamp}.html"
        title = "Portland Purchase Report"

    # Enrich listings with geo data and map URLs
    key_locations = []
    for loc in cfg.get("key_locations", []):
        coords = await geocode(loc["address"])
        if coords:
            key_locations.append({"name": loc["name"], "lat": coords[0], "lng": coords[1]})

    for i, listing in enumerate(listings):
        listing._status = fav_mgr.status(listing.id)

        coords = await geocode(listing.address)
        if coords:
            listing._lat = coords[0]
            listing._lng = coords[1]
            listing._map_url = await get_google_maps_image_url(coords[0], coords[1])
            listing._streetview_url = await get_street_view_url(coords[0], coords[1])
        else:
            listing._lat = None
            listing._lng = None
            listing._map_url = ""
            listing._streetview_url = ""

        listing._distances = await distances_to_key_locations(listing.address)

        # Photo paths as relative URLs for the HTML
        listing._photos = [p for p in listing.photo_paths if Path(p).exists()]

        if progress_callback and (i + 1) % 5 == 0:
            await progress_callback(f"Preparing listing {i + 1}/{len(listings)}")

    # Compute stats
    prices = [l.price for l in listings if l.price]
    scored = [l for l in listings if l.total_score]
    neighborhoods = set(l.neighborhood for l in listings if l.neighborhood)

    html = REPORT_TEMPLATE.render(
        title=title,
        date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        mode=mode,
        listings=listings,
        include_map=include_map,
        key_locations=key_locations,
        price_min=min(prices) if prices else 0,
        price_max=max(prices) if prices else 0,
        top_score=max((l.total_score for l in scored), default=0) if scored else 0,
        neighborhoods=len(neighborhoods),
    )

    output_path = config.DATA_DIR / filename
    output_path.write_text(html)

    if progress_callback:
        await progress_callback(f"Report saved: {filename}")

    return output_path
