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
  (Required for static map, street view, and distance calculations in reports)

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

Run stages in order. Each builds on the previous stage's output.

## Interactive Search Flow

When you run `/rental:search-listings`, the plugin asks four questions before searching:

1. **Room count** -- How many bedrooms? (Studio, 1, 2, 3+)
2. **Square footage** -- Minimum square footage? (Any, 500+, 700+, 900+, 1000+)
3. **Price maximum** -- Max monthly rent? (No cap, $1,500, $2,000, $2,500, $3,000, custom)
4. **Mixed-use preference** -- Need mixed-use/commercial zoning? (Yes, No, Preferred but not required)

Kitchen and fiber internet are always required and not asked. After confirming criteria, the plugin translates them to site-specific filters and searches across listing sites.

Purchase searches use the `$700k` price cap and search residential + commercial for-sale sites.

## Target Area

Central Portland on both sides of the Willamette River:

- **East side**: Buckman, Hosford-Abernethy, Richmond, Sunnyside, Hawthorne, Belmont, Brooklyn, Creston-Kenilworth, Sellwood-Moreland, Laurelhurst, and more
- **West side**: Pearl District, Downtown, Goose Hollow, South Portland
- **Inner NE**: Irvington, Grant Park, Hollywood, Sullivan's Gulch

## Report Features

Reports are generated as self-contained HTML files with embedded images:

- **2x2 photo gallery** -- Up to 4 listing photos per card, clickable with lightbox overlay
- **Google Street View** -- Street-level image for each address
- **Google Maps** -- Static map with marker, hyperlinked to Google Maps
- **Distance calculations** -- Straight-line miles to three key locations (Chris, George, Jasmine)
- **Fiber internet data** -- Provider list, speeds, and classification (Excellent/Good/Adequate/Poor) from BroadbandNow
- **Scoring** -- 0-100 score based on room count, kitchen, price, sqft, mixed-use potential, and fiber quality
- **Summary rankings table** -- All listings ranked with hyperlinks to detailed cards below

PDF generation is available as an alternative format via `data/generate_report.py`.

## Listing Sites Searched

**Residential rentals**: Zillow, Apartments.com, Craigslist Portland, HotPads, Redfin
**Commercial rentals**: LoopNet, CommercialCafe, Craigslist (commercial/office)
**For-sale residential**: Zillow, Redfin, Realtor.com, Craigslist
**For-sale commercial**: LoopNet, CommercialCafe, Craigslist

## Internet Checking

BroadbandNow is the primary ISP checker -- one address lookup returns all providers (Quantum Fiber, CenturyLink, Xfinity, AT&T, T-Mobile, etc.). Direct ISP sites (CenturyLink, Ziply, Xfinity) are fallbacks only. Internet data is text-based; no ISP screenshots are captured.

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

skills/
  search-resources/SKILL.md            # Rental site URLs, strategies, JSON schema
  purchase-search-resources/SKILL.md   # For-sale site URLs, strategies, purchase JSON schema
  portland-geography/SKILL.md          # Neighborhoods, zip codes, corridors, transit
  fiber-internet-check/SKILL.md        # BroadbandNow procedures, ISP fallbacks
  listing-evaluation/SKILL.md          # Rental scoring rubric (0-100)
  purchase-evaluation/SKILL.md         # Purchase scoring rubric (0-100, $700k cap)

agents/
  apartment-finder.md                  # Browser automation for listing extraction
  internet-checker.md                  # BroadbandNow + ISP fallback automation
  report-builder.md                    # HTML/PDF report compilation

data/
  .env                                 # Google Maps API key (gitignored)
  listings.json                        # Rental listings (runtime, gitignored)
  purchase-listings.json               # Purchase listings (runtime, gitignored)
  generate_report.py                   # PDF report generator (reportlab)
  generate_html_report.py              # HTML report generator (standalone Python)
  screenshots/                         # Photos, maps, street view (gitignored)
  *.html / *.pdf                       # Generated reports (gitignored)
```

## Data Flow

```
Stage 1: Search Listings
  Browser automation -> extract listing data + download photos
  -> data/output/listings.json (or data/output/purchase-listings.json)
  -> data/output/screenshots/{id}-1.jpg through {id}-4.jpg

Stage 2: Check Internet
  Read listings.json -> BroadbandNow lookups -> enrich with internet data
  -> data/output/listings.json (updated with internet field)

Stage 3: Generate Report
  Read listings.json + screenshots/ + Google Maps API
  -> data/output/screenshots/{id}-map.jpg, {id}-streetview.jpg
  -> data/output/portland-apartment-report-YYYYMMDD-HHMM.html
```

## CAPTCHA Handling

When a site shows a CAPTCHA, the plugin pauses and asks you to solve it in the visible Chrome browser window. Tell the plugin in chat when you are done and it will continue.
