---
description: End-to-end purchase search — search for-sale listing sites (under $700k), check fiber internet, and generate an HTML report
argument-hint: "[max_results] [neighborhood]"
allowed-tools: mcp__Claude_in_Chrome__navigate, mcp__Claude_in_Chrome__find, mcp__Claude_in_Chrome__read_page, mcp__Claude_in_Chrome__computer, mcp__Claude_in_Chrome__form_input, mcp__Claude_in_Chrome__get_page_text, mcp__Claude_in_Chrome__javascript_tool, mcp__Claude_in_Chrome__tabs_context_mcp, mcp__Claude_in_Chrome__tabs_create_mcp, Read, Write, Glob, Bash
---

# /purchase

Run the full purchase search pipeline: search for-sale listing sites (under $700k), check fiber internet at each address, and generate an HTML report.

---

## Stage 1: Search Listings

### Inputs
- `max_results` (optional): Maximum total listings to collect. Default: 20
- `neighborhood` (optional): Specific neighborhood to focus on. Default: all target neighborhoods per `portland-geography` skill

### Workflow

1. Load the `purchase-search-resources` skill for sale listing site URLs and strategies
2. Load the `portland-geography` skill for target neighborhoods and zip codes
3. Open a Chrome tab via `tabs_context_mcp` / `tabs_create_mcp`
4. Create `data/output/screenshots/` directory if it doesn't exist
5. Initialize empty `data/output/purchase-listings.json` array

6. **Save search criteria** to `data/output/search-criteria.json` for `/watch` command:
   ```json
   {
     "type": "purchase",
     "saved_at": "2026-03-29T10:00:00",
     "criteria": { "max_price": 700000, "max_results": 20, "neighborhood": "all" }
   }
   ```

7. **For each residential sale site** (Zillow, Redfin, Realtor.com):
   a. Navigate to the site's Portland for-sale URL
   b. Apply filters: max price $700,000, target zip codes/neighborhoods (use multiple searches per `portland-geography` Search Radius Guidance)
   c. Include both houses and multi-family/commercial properties
   d. Wait for results to load
   e. Use `read_page` to extract listing cards from results
   f. For each promising listing (up to 5 per site):
      - Use `read_page` on the card ref to get the listing URL (href)
      - `navigate` directly to the listing URL
      - Use `find` + `read_page` to extract structured data (address, price, beds/baths, sqft, lot size, year built, property type)
      - Extract up to 8 gallery photos + floor plans via `javascript_tool` and download with `curl`
      - Extract price history, previous sales, estimated value if visible on listing page
      - Extract sale terms: HOA fees, property tax, zoning, special assessments
      - Build a listing JSON object per the purchase schema in `purchase-search-resources` skill (including new fields)
      - Add to listings array
   g. Navigate back to results or next site

8. **For each commercial sale site** (LoopNet, Craigslist commercial):
   a. Navigate to the site's Portland for-sale URL
   b. Apply filters: max price $700,000, search for "mixed use", "live work", "retail", "office"
   c. Extract listings following the same pattern
   d. Set `listing_type` to "commercial" or "mixed-use"

9. **Search additional sources** (ask user for login first):
   - Facebook Marketplace (propertyforsale category)
   - Nextdoor (community FSBO listings)
   Skip these if user declines to log in.

10. **Run deduplication** per the `deduplication` skill:
    - Normalize all addresses
    - Detect duplicates across sites
    - Merge, preserving best data and tracking `also_listed_on`
    - Report dedup summary

11. Write deduplicated listings to `data/output/purchase-listings.json`
12. Report summary: "Found X properties across Y sites (Z after dedup). W residential, V commercial/mixed-use."

#### CAPTCHA Handling
Same as rental — screenshot, ask user to solve, wait, resume.

#### Delegation
Spawns the `apartment-finder` agent for the browser automation work (same agent, different filters).

---

## Stage 2: Check Internet

Check fiber and broadband internet availability at the address of each property found in Stage 1.

1. Read `data/output/purchase-listings.json`. If missing or empty, report an error and stop.
2. Load the `fiber-internet-check` skill for ISP checker URLs and navigation procedures
3. Filter to listings where `internet` is null (allows re-running to pick up where it left off)
4. Open a Chrome tab if not already available

5. **Determine checking mode** based on listing count:
   - 5 or fewer listings: Sequential (single tab)
   - 6-15 listings: Parallel with 2 tabs
   - 16+ listings: Parallel with 3 tabs

6. **For each listing address** (use BroadbandNow as primary — one lookup per address gets all providers):
   a. **BroadbandNow** (PRIMARY): Use the Google Places autocomplete pattern from `fiber-internet-check` skill
   b. **Parallel mode**: When using multiple tabs, rotate between them during wait periods (see `internet-checker` agent Parallel Checking section)
   c. **Direct ISP sites** (FALLBACK ONLY): If BroadbandNow fails
   d. Build the internet JSON object — **no ISP screenshots needed**, text data only
   e. Classify internet suitability (Excellent/Good/Adequate/Poor)
   f. Update the listing's `internet` field
   g. If rate-limited during parallel mode, fall back to sequential with 5-second delays

7. Write enriched data back to `data/output/purchase-listings.json`
8. Report summary: "Checked X addresses. Fiber available at Y. Cable-only at Z. Failed checks: W."

#### Re-Runnability
Stage 2 only processes listings where `internet` is null. If interrupted, re-running `/purchase` can pick up where it left off (existing listings and internet data are preserved).

#### Delegation
Spawns the `internet-checker` agent for the browser automation work.

---

## Stage 3: Generate Report

Compile all collected for-sale listing data, photos, and Google Maps images into a formatted HTML report.

1. Read `data/output/purchase-listings.json`. Validate that listings exist and most have internet data.
2. Read `data/config.json` for key locations and report settings
3. Read `data/output/reviewed.json` if it exists (for favorites/review badges)
4. Load the `purchase-evaluation` skill to compute a final score for each listing (includes hipness + safety components)
5. Score each listing using the purchase rubric (0-100 scale)
6. Sort listings by score (highest first)

7. **Fetch Google Maps images** for each listing (requires API key from `data/.env`):
   - Static Maps API and Street View Static API
   - Download via `curl` to `data/output/screenshots/{id}-map.jpg` and `{id}-streetview.jpg`

8. **Build HTML report** (primary format):

   **Cover Section:**
   - Gradient header: "Portland Property Purchase — Live/Work Space Report"
   - Date generated
   - Search parameters: Central Portland, under $700k, residential + commercial
   - Total listings found, fiber-available count, deduplication summary

   **Favorites Summary** (if `reviewed.json` has favorites):
   - Quick list of favorited properties with links to detail cards
   - Price changes on favorites highlighted

   **Interactive Map** (Leaflet.js — see `report-builder` agent for implementation):
   - OpenStreetMap tiles, centered on Portland
   - Color-coded pins for each property (green 80+, yellow 60-79, orange 40-59, red below 40)
   - Popup on click: address, price, property type, score, hipness/safety tiers
   - Key locations from `data/config.json` as blue markers

   **Summary Rankings Table** (below map):
   - All listings ranked by score
   - Columns: Rank, Badges (⭐/✓/NEW), Address, Neighborhood, Price, Type, Beds/Bath, Sqft, Internet, Hipness, Safety, Score
   - Color-coded badges for internet/hipness/safety
   - Rejected listings hidden by default (toggleable)

   **Per-Listing Cards** (sorted by score):
   - Address + price + property type + status badges (⭐/✓/NEW)
   - Links to original listing + `also_listed_on` cross-listing links
   - Photo gallery: up to 8 photos (responsive grid) + floor plan if available
   - Street View + Google Maps (static images, clickable)
   - All images with lightbox overlay
   - Property details: price, beds, baths, sqft, lot size, year built, property type
   - **Price Context**: Days on market, price trend, price history timeline, previous sales, estimated value
   - **Sale Terms**: HOA fees, property tax, zoning, assessments (if extracted)
   - Description and features
   - Internet summary with classification
   - **Hipness**: Score badge + tier + buzz highlights
   - **Safety**: Score badge + tier + safety notes + noise sources
   - **Distances**: To each key location from `data/config.json`

   **Methodology Section:**
   - Data sources, scoring rubric (including hipness + safety), internet classification, deduplication approach

   **Filename**: `data/output/portland-purchase-report-YYYYMMDD-HHMM.html`

9. Tell user: "Report generated with X properties."

10. **Ask about Notion**: After the report is generated, ask the user:
    > "Would you like me to create this report as a Notion document in the Document Hub?"

    If yes, create a page in the Document Hub database (data source `collection://1df03407-763c-8098-81b8-000b500508b8`) using the `notion-create-pages` tool:
    - **Doc name**: "Portland Properties For Sale Report — {Month} {Year}"
    - **Category**: `["Planning"]`
    - **Content**: Convert the report into Notion-flavored Markdown — summary rankings table, per-listing details (address, price, beds/baths, sqft, lot size, property type, neighborhood, internet classification, score), and methodology section

#### Expected Output
- `data/output/portland-purchase-report-YYYYMMDD-HHMM.html` (timestamped)
- Notion document in Document Hub (if user accepts)
- Chat confirmation with listing count and top 3 recommendations

#### Delegation
Spawns the `report-builder` agent for HTML assembly.
