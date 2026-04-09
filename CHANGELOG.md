# Changelog

All changes to the Portland Office Search project.

## 2026-04-09 — Replace HTML Reports with Notion Database

### Output
- Replaced HTML/PDF report generation with Notion database sync
- Each listing becomes a row with 28 properties (score, price, internet, hipness, safety, etc.)
- Page body contains description, amenities, distances, internet provider breakdown, price history
- Re-running updates existing rows (matched by address) instead of creating duplicates
- Notion database ID configurable in `data/config.json`

### Removed
- HTML report generation (Pico CSS, Leaflet.js interactive map, photo galleries, lightbox)
- PDF report generation (`anthropic-skills:pdf`)
- Python report generators (`generate_report.py`, `generate_html_report.py`)
- Notion Document Hub integration (replaced by direct database sync)

## 2026-04-09 — Convert to Standalone Cowork Project

### Structure
- Converted from Claude plugin format to standalone Cowork project format
- Moved `commands/` → `.claude/commands/`
- Moved `skills/` → `.claude/skills/`
- Moved `agents/` → `.claude/agents/`
- Removed `.claude-plugin/plugin.json` (no longer needed)
- Removed `package.sh` (no longer needed for distribution)

### Command Naming
- Commands no longer namespaced: `/rental:search-listings` → `/rental-search-listings`, etc.
- Updated all internal cross-references to match
- Fixed stale `/apt:search-listings` reference in report-builder agent

### Command Consolidation
- Merged 3 rental commands into single `/rent` (search → check internet → sync to Notion)
- Merged 3 purchase commands into single `/purchase` (search → check internet → sync to Notion)
- Removed 6 individual stage commands (`rental-search-listings`, `rental-check-internet`, `rental-generate-report`, `purchase-search-listings`, `purchase-check-internet`, `purchase-generate-report`)

### Documentation
- Updated CLAUDE.md and README.md for standalone project format
- Replaced "plugin" terminology with "project" throughout

## 2026-03-27 — Project Rename and Purchase Mode

### Project Identity
- Renamed project from "apartment-search" to "office-search" (`plugin.json` name field updated)
- Plugin description updated to reflect dual rental/purchase scope

### Purchase Search Pipeline
- Added `/purchase:search-listings` command with $700k price cap for houses, duplexes, multi-family, mixed-use, and commercial buildings
- Added `/purchase:check-internet` command (same BroadbandNow-first flow as rental)
- Added `/purchase:generate-report` command for HTML report output
- Created `purchase-search-resources` skill with for-sale site URLs (Zillow, Redfin, Realtor.com, Craigslist real estate, LoopNet, CommercialCafe) and purchase-specific JSON schema (adds `lot_sqft`, `year_built`, `property_type` fields)
- Created `purchase-evaluation` skill with purchase-specific scoring rubric (price value, room count, sqft, location quality, mixed-use potential, fiber internet, property condition)
- Purchase data stored in `data/output/purchase-listings.json` (separate from rental `data/output/listings.json`)
- Purchase reports output to `data/portland-purchase-report-YYYYMMDD-HHMM.html`

### Target Area Expansion
- Expanded search area from Inner SE Portland (Powell/Division corridors only) to central Portland on both sides of the Willamette River
- Added west side neighborhoods: Pearl District, Old Town/Chinatown, Downtown, Goose Hollow, South Portland
- Added north/inner NE neighborhoods: Irvington, Grant Park, Hollywood, Sullivan's Gulch
- Added east side neighborhoods: Laurelhurst, Sellwood-Moreland, Eastmoreland, Westmoreland, Reed
- Updated `portland-geography` skill with full neighborhood tables, zip codes, transit notes, and multi-search radius guidance (4 searches across 97214, 97202, 97209, 97212)

## 2026-03-27 — Command Rename

- Renamed commands from `/apt:*` to `/rental:*` (`search-listings`, `check-internet`, `generate-report`)
- Renamed command files from `search-listings.md` / `check-internet.md` / `generate-report.md` to `rental-search-listings.md` / `rental-check-internet.md` / `rental-generate-report.md`
- Updated all internal cross-references

## 2026-03-27 — Interactive Search Flow

- Replaced hardcoded search criteria with interactive user questions at the start of `/rental:search-listings`
- Questions cover: room count, minimum square footage, price maximum, mixed-use preference
- Kitchen and fiber internet remain always-required (not asked)
- Confirmation step before executing search: "Searching for: [criteria]. Sound right?"
- Criteria translated to site-specific filters (Craigslist URL params, Zillow/Redfin filter panels, Apartments.com search bar)

## 2026-03-27 — Scoring Rubric Overhaul

- Removed Powell/Division proximity factor from scoring (was 20% weight)
- Redistributed weights: Room count 20%, Kitchen quality 15%, Price reasonableness 20%, Square footage 15%, Mixed-use friendliness 15%, Fiber internet quality 15%
- Updated `listing-evaluation` skill with new weight table
- Updated `generate_html_report.py` `score_listing()` to match new rubric
- Note: `generate_report.py` (PDF) and `score_breakdown()` in HTML report still reference the old rubric (legacy)

### Distance Calculations
- Added distance calculations from each listing to three key locations: Chris (SE 24th Ave), George (SW Lee St), Jasmine (SE Main St)
- Distances displayed as badges in HTML report listing cards
- Uses Google Geocoding API with disk-based cache (`data/output/screenshots/geocode_*.json`)
- Haversine formula for straight-line distance in miles

## 2026-03-27 — HTML Report Enhancements

### Report Format
- Added HTML as primary report format (PDF remains as alternative)
- HTML report uses `Write` tool directly (no external dependencies like reportlab)
- Created `data/generate_html_report.py` as standalone Python generator
- HTML reports timestamped: `portland-apartment-report-YYYYMMDD-HHMM.html`

### Google Maps Integration
- Added Google Maps Static API images to each listing card (map with red marker)
- Added Street View Static API images to each listing card
- Google Maps API key stored in `data/.env` (gitignored)
- Images downloaded via `curl` and cached to `data/output/screenshots/{id}-map.jpg` and `{id}-streetview.jpg`
- Map images hyperlinked to Google Maps (opens in new tab)
- Adjusted map zoom level from 15 to 13 for better neighborhood context

### Photo Gallery
- Switched from single listing screenshot to 2x2 photo grid (up to 4 photos per listing)
- Photo naming: `{id}-1.jpg` through `{id}-4.jpg` (was single `{id}.jpg`)
- Gallery uses CSS grid with hover scale effect
- Single-photo fallback layout when only one image available
- All images clickable with lightbox overlay for full-size viewing

### Summary Table
- Summary table entries hyperlinked to listing anchor IDs within the report
- Added `summary-link` CSS class for in-page navigation

### Listing Cards
- Removed score breakdown table from individual listing cards (score details only in summary rankings table)
- Added distance badges showing miles to Chris, George, and Jasmine
- Added score bar visualization (color-coded: green/orange/red by score range)

## 2026-03-27 — Photo Download Method

- Switched from Chrome `save_to_disk` screenshot to JavaScript image URL extraction + curl download
- `save_to_disk` screenshots exist only in Chrome extension memory and never write to disk
- New method: `javascript_tool` extracts gallery `img.src` URLs, then `Bash` `curl -s -o` downloads them
- Craigslist-specific: thumbnail URLs (`.thumb img`) rewritten from `_50x50c.jpg` to `_600x450.jpg` for full-size images
- Documented in `search-resources` skill and `apartment-finder` agent

## 2026-03-27 — BroadbandNow as Primary ISP Checker

- Promoted BroadbandNow from fallback to primary ISP checker (was behind direct CenturyLink/Ziply/Xfinity checks)
- One lookup per address returns all providers (Quantum Fiber, CenturyLink, Xfinity, AT&T, T-Mobile, etc.)
- Direct ISP sites demoted to fallback-only role
- ISP data is text-only -- no ISP screenshots captured or stored
- Documented BroadbandNow Google Places autocomplete pattern: must type short address and select from dropdown (direct submission fails)
- Added JavaScript native value setter method for BroadbandNow input field as more reliable alternative to `computer` `type` action
- Documented `form_input` truncation bug (~30 character limit on BroadbandNow)

## 2026-03-27 — Trial Run Learnings

- Discovered Chrome extension conflicts: `computer` actions (screenshot, click, key) fail with "Cannot access a chrome-extension:// URL" when other extensions interfere; read-only tools (`navigate`, `find`, `read_page`, `form_input`, `get_page_text`) still work
- Documented Craigslist extraction patterns: gallery view URL params, `find` for listing cards by neighborhood/title, detail page structure (heading, sidebar, region elements), `get_page_text` returns empty on Craigslist (use `find`/`read_page` instead)
- Discovered BroadbandNow autocomplete requires typing (not pasting via `form_input`), short addresses (no state/zip), and waiting for dropdown before clicking
- Added troubleshooting sections to `search-resources` skill and `apartment-finder` agent

## 2026-03-27 — Initial Plugin Scaffolding

- Created three-stage pipeline architecture: search listings, check internet, generate report
- Set up plugin manifest (`.claude-plugin/plugin.json`)
- Created skills: `search-resources` (listing sites and strategies), `portland-geography` (neighborhoods and zip codes), `fiber-internet-check` (ISP lookup procedures), `listing-evaluation` (scoring rubric)
- Created commands: `search-listings`, `check-internet`, `generate-report` (originally as `/apt:*`)
- Created agents: `apartment-finder` (browser-driven listing scraper), `internet-checker` (ISP coverage lookups), `report-builder` (report compilation)
- Data contract: `data/output/listings.json` as shared state between stages
- Screenshots stored in `data/output/screenshots/` directory
- Initial report format: PDF via `data/generate_report.py` using reportlab
- Target area: Inner SE Portland, Powell/Division corridors (Hosford-Abernethy, Richmond, Creston-Kenilworth, Brooklyn, Buckman)
- Safety boundaries: read-only browsing, no account creation, no personal info submission, CAPTCHA handling via user interaction
