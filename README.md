# Portland Office Search

Claude Code plugin that searches for live/work spaces in Portland, OR, checks fiber internet availability at each address, and generates HTML reports with photos, maps, and scores. Supports both **rental** and **purchase** searches.

## Prerequisites

- Claude Code with Cowork mode
- [Claude in Chrome](https://chromewebstore.google.com/detail/claude-in-chrome) extension installed and connected
- Active Chrome browser window
- Google Maps API key in `data/.env`:
  ```
  GOOGLE_MAPS_API_KEY=your_key_here
  ```
  (Required for static map, street view, interactive map geocoding, and distance calculations in reports)

## Commands

### Rental Search (`/rental:*`)

```
/rental:search-listings    # Stage 1: Search rental listing sites
/rental:check-internet     # Stage 2: Check fiber internet at each address
/rental:generate-report    # Stage 3: Generate HTML report
```

### Purchase Search (`/purchase:*`)

```
/purchase:search-listings    # Stage 1: Search for-sale listings (under $700k)
/purchase:check-internet     # Stage 2: Check fiber internet at each address
/purchase:generate-report    # Stage 3: Generate HTML report
```

### Utility Commands

```
/watch                       # Monitor for new/price-changed listings since last search
/compare                     # Side-by-side comparison of 2-3 selected listings
/favorites                   # Track reviewed/favorited/rejected listings
```

Run pipeline stages in order. Each builds on the previous stage's output. Utility commands can be run independently.

## Interactive Search Flow

When you run `/rental:search-listings`, the plugin asks four questions before searching:

1. **Room count** -- How many bedrooms? (Studio, 1, 2, 3+)
2. **Square footage** -- Minimum square footage? (Any, 500+, 700+, 900+, 1000+)
3. **Price maximum** -- Max monthly rent? (No cap, $1,500, $2,000, $2,500, $3,000, custom)
4. **Mixed-use preference** -- Need mixed-use/commercial zoning? (Yes, No, Preferred but not required)

Kitchen and fiber internet are always required and not asked. After confirming criteria, the plugin translates them to site-specific filters and searches across listing sites. Criteria are saved for `/watch` to reuse later.

Purchase searches use the `$700k` price cap and search residential + commercial for-sale sites.

## Target Area

Central Portland on both sides of the Willamette River:

- **East side**: Buckman, Hosford-Abernethy, Richmond, Sunnyside, Hawthorne, Belmont, Brooklyn, Creston-Kenilworth, Sellwood-Moreland, Laurelhurst, and more
- **West side**: Pearl District, Downtown, Goose Hollow, South Portland, NW 23rd / Nob Hill
- **Inner NE**: Irvington, Grant Park, Hollywood, Sullivan's Gulch, Eliot, Boise, King

## Report Features

Reports are generated as self-contained HTML files:

- **Interactive map** -- Leaflet.js map with color-coded pins for all listings and key location markers
- **Photo gallery** -- Up to 8 listing photos per card (configurable), plus floor plans when available, with lightbox overlay
- **Google Street View** -- Street-level image for each address
- **Google Maps** -- Static map with marker, hyperlinked to Google Maps
- **Distance calculations** -- To configurable key locations (editable in `data/config.json`)
- **Fiber internet data** -- Provider list, speeds, and classification (Excellent/Good/Adequate/Poor) from BroadbandNow
- **Scoring** -- 0-100 composite score based on 10 weighted factors including hipness and safety
- **Hipness score** -- Cultural vibrancy from indie businesses, walkability, and web/Reddit buzz
- **Safety score** -- Crime data, noise levels, and online reputation
- **Price context** -- Days on market, price trends, price history timeline
- **Lease/sale terms** -- Deposit, pet policy, parking, HOA, property tax, zoning
- **Deduplication** -- Cross-site duplicate detection with merged data and source tracking
- **Favorites badges** -- ⭐ (favorite), ✓ (reviewed), NEW indicators per listing
- **Summary rankings table** -- All listings ranked with clickable links to detailed cards

PDF generation is available as an alternative format.

## Listing Sites Searched

**Residential rentals**: Zillow, Apartments.com, Craigslist Portland, HotPads, Redfin
**Commercial rentals**: LoopNet, CommercialCafe, Craigslist (commercial/office)
**For-sale residential**: Zillow, Redfin, Realtor.com, Craigslist
**For-sale commercial**: LoopNet, CommercialCafe, Craigslist
**Additional sources** (login required): Facebook Marketplace, Nextdoor

## Internet Checking

BroadbandNow is the primary ISP checker -- one address lookup returns all providers (Quantum Fiber, CenturyLink, Xfinity, AT&T, T-Mobile, etc.). Direct ISP sites (CenturyLink, Ziply, Xfinity) are fallbacks only. Internet data is text-based; no ISP screenshots are captured. For 6+ listings, parallel multi-tab checking is used to reduce total time.

## Project Structure

```
.claude-plugin/
  plugin.json                          # Plugin manifest

commands/
  rental-search-listings.md            # /rental:search-listings
  rental-check-internet.md             # /rental:check-internet
  rental-generate-report.md            # /rental:generate-report
  purchase-search-listings.md          # /purchase:search-listings
  purchase-check-internet.md           # /purchase:check-internet
  purchase-generate-report.md          # /purchase:generate-report
  watch.md                             # /watch — new listing alerts
  compare.md                           # /compare — side-by-side comparison
  favorites.md                         # /favorites — review tracking

skills/
  search-resources/SKILL.md            # Rental site URLs, strategies, JSON schema
  purchase-search-resources/SKILL.md   # For-sale site URLs, strategies, purchase JSON schema
  portland-geography/SKILL.md          # Neighborhoods, zip codes, corridors, hipness baselines
  fiber-internet-check/SKILL.md        # BroadbandNow procedures, ISP fallbacks
  listing-evaluation/SKILL.md          # Rental scoring rubric (0-100)
  purchase-evaluation/SKILL.md         # Purchase scoring rubric (0-100, $700k cap)
  hipness-scoring/SKILL.md             # Area cultural vibrancy scoring
  safety-scoring/SKILL.md              # Neighborhood safety and noise scoring
  deduplication/SKILL.md               # Cross-site listing deduplication

agents/
  apartment-finder.md                  # Browser automation for listing extraction
  internet-checker.md                  # BroadbandNow + ISP fallback automation
  report-builder.md                    # HTML/PDF report compilation

data/
  .env                                 # Google Maps API key (gitignored)
  config.json                          # Key locations, search defaults, report settings
  output/listings.json                 # Rental listings (runtime, gitignored)
  output/purchase-listings.json        # Purchase listings (runtime, gitignored)
  output/reviewed.json                 # Favorites/review history (runtime, gitignored)
  output/search-criteria.json          # Saved criteria for /watch (runtime, gitignored)
  output/screenshots/                  # Photos, maps, street view (gitignored)
  output/*.html                        # Generated reports (gitignored)
  generate_report.py                   # Legacy PDF report generator
  generate_html_report.py              # Legacy HTML report generator
```

## Data Flow

```
Stage 1: Search Listings
  Browser automation -> extract listing data + download up to 8 photos + floor plans
  -> extract price history, lease/sale terms
  -> deduplicate across sites
  -> data/output/listings.json (or purchase-listings.json)
  -> data/output/screenshots/{id}-1.jpg through {id}-8.jpg, {id}-floorplan.jpg

Stage 2: Check Internet
  Read listings.json -> BroadbandNow lookups (parallel for 6+ listings)
  -> enrich with internet data
  -> data/output/listings.json (updated with internet field)

Stage 3: Generate Report
  Read listings.json + reviewed.json + config.json + screenshots/ + Google Maps API
  -> score with hipness + safety components
  -> data/output/screenshots/{id}-map.jpg, {id}-streetview.jpg
  -> data/output/portland-apartment-report-YYYYMMDD-HHMM.html (with interactive map)
```

## CAPTCHA Handling

When a site shows a CAPTCHA, the plugin pauses and asks you to solve it in the visible Chrome browser window. Tell the plugin in chat when you are done and it will continue.

## Configuration

Edit `data/config.json` to customize:

- **Key locations** -- People/places to calculate distances to (default: Chris, George, Jasmine)
- **Search defaults** -- Default bedroom count, price caps
- **Report settings** -- Max photos per listing, toggle interactive map, toggle hipness/safety scores, show/hide rejected listings
