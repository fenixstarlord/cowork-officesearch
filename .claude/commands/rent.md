---
description: End-to-end rental search — search listing sites, check fiber internet, and generate an HTML report
argument-hint: ""
allowed-tools: mcp__Claude_in_Chrome__navigate, mcp__Claude_in_Chrome__find, mcp__Claude_in_Chrome__read_page, mcp__Claude_in_Chrome__computer, mcp__Claude_in_Chrome__form_input, mcp__Claude_in_Chrome__get_page_text, mcp__Claude_in_Chrome__javascript_tool, mcp__Claude_in_Chrome__tabs_context_mcp, mcp__Claude_in_Chrome__tabs_create_mcp, Read, Write, Glob, Bash
---

# /rent

Run the full rental search pipeline: search listing sites, check fiber internet at each address, and generate an HTML report.

---

## Stage 1: Search Listings

### Step 1: Ask the User

Before searching, ask these questions (use AskUserQuestion or chat):

1. **Room count** — How many bedrooms? (Studio, 1, 2, 3+)
2. **Square footage** — Minimum square footage? (Any, 500+, 700+, 900+, 1000+)
3. **Price maximum** — Max monthly rent? (No cap, $1,500, $2,000, $2,500, $3,000, custom)
4. **Mixed use or business** — Do you need mixed-use/commercial zoning or the ability to run a business from the space? (Yes, No, Preferred but not required)

#### Always Required (do not ask)
- Fiber internet availability (checked in Stage 2)
- Kitchen or kitchenette

### Step 2: Confirm and Search

Confirm the parsed criteria:
> "Searching for: [bedrooms], [min sqft], under [price], [mixed-use preference], with kitchen, fiber internet required. Sound right?"

### Step 3: Execute Search

1. Load the `search-resources` skill for site URLs and strategies
2. Load the `portland-geography` skill for neighborhoods and zip codes
3. Open a Chrome tab
4. Create `data/output/screenshots/` directory if needed
5. Initialize empty `data/output/listings.json` array

6. **Save search criteria** to `data/output/search-criteria.json` for `/watch` command:
   ```json
   {
     "type": "rental",
     "saved_at": "2026-03-29T10:00:00",
     "criteria": { "bedrooms": 2, "min_sqft": 700, "max_price": 2500, "mixed_use": "preferred" }
   }
   ```

7. **Translate criteria to site-specific filters:**
   - **Craigslist**: URL params (`min_bedrooms`, `max_price`, `min_sqft`, `postal`, `search_distance`)
   - **Zillow/Redfin**: Filter panel controls
   - **Apartments.com/HotPads**: Search bar + filter panel

8. **For each listing site**, apply filters and extract listings:
   a. Navigate to site URL
   b. Apply user's filters
   c. Use multiple zip code searches for broad target area (per `portland-geography`)
   d. Extract listing cards, click into each
   e. Use `find` + `read_page` for structured data
   f. Extract up to 8 gallery photos + floor plans via `javascript_tool` + download with `curl`
   g. Extract price history and lease terms when visible on listing pages
   h. Build listing JSON objects (including new fields: `price_history`, `lease_terms`, `floorplan_path`, etc.)

9. **If user wants mixed-use**, also search LoopNet, CommercialCafe, Craigslist commercial

10. **Search additional sources** (ask user for login first):
    - Facebook Marketplace (propertyrentals category)
    - Nextdoor (community rental listings)
    Skip these if user declines to log in.

11. **Run deduplication** per the `deduplication` skill:
    - Normalize all addresses
    - Detect duplicates by address match or address + price match
    - Merge duplicates, preserving best data and tracking cross-listing URLs in `also_listed_on`
    - Report dedup summary

12. Write deduplicated listings to `data/output/listings.json`
13. Report summary to user: "Found X listings across Y sites (Z after deduplication). W commercial/mixed-use."

#### Craigslist URL Parameter Reference

```
?min_bedrooms=2&max_price=2000&minSqft=700&postal=97214&search_distance=3
&pets_cat=1&pets_dog=1&laundry=1&parking=1
```

#### CAPTCHA Handling
Screenshot, ask user to solve in browser, wait, resume.

#### Delegation
Spawns the `apartment-finder` agent for browser automation.

---

## Stage 2: Check Internet

Check fiber and broadband internet availability at the address of each listing found in Stage 1.

1. Read `data/output/listings.json`. If missing or empty, report an error and stop.
2. Load the `fiber-internet-check` skill for ISP checker URLs and navigation procedures
3. Filter to listings where `internet` is null (allows re-running to pick up where it left off)
4. Open a Chrome tab if not already available

5. **Determine checking mode** based on listing count:
   - 5 or fewer listings: Sequential (single tab)
   - 6-15 listings: Parallel with 2 tabs
   - 16+ listings: Parallel with 3 tabs

6. **For each listing address** (use BroadbandNow as primary — one lookup per address gets all providers):
   a. **BroadbandNow** (PRIMARY): Use the Google Places autocomplete pattern from `fiber-internet-check` skill:
      - Type short address (number + street + city) into search input
      - Wait for autocomplete dropdown, click the matching suggestion
      - Extract all providers, speeds, connection types from results page
      - For subsequent addresses, use the "refine search" box on the results page
   b. **Parallel mode**: When using multiple tabs, rotate between them during wait periods (see `internet-checker` agent Parallel Checking section)
   c. **Direct ISP sites** (FALLBACK ONLY): If BroadbandNow fails or data seems incomplete, check CenturyLink/Xfinity directly
   d. Build the internet JSON object per the schema in `search-resources` skill — **no ISP screenshots needed**, text data only
   e. Classify internet suitability (Excellent/Good/Adequate/Poor) per `fiber-internet-check` skill
   f. Update the listing's `internet` field
   g. If rate-limited during parallel mode, fall back to sequential with 5-second delays

7. Write enriched data back to `data/output/listings.json`
8. Report summary: "Checked X addresses. Fiber available at Y. Cable-only at Z. Failed checks: W."

If an address fails all providers, mark internet as:
```json
{ "internet": { "status": "check_failed", "note": "All provider checks failed for this address" } }
```

#### CAPTCHA Handling
If any ISP checker shows a CAPTCHA: take a screenshot, ask user to solve it in the browser, wait for confirmation, resume.

#### Re-Runnability
Stage 2 only processes listings where `internet` is null. If interrupted, re-running `/rent` can pick up where it left off (existing listings and internet data are preserved).

#### Delegation
Spawns the `internet-checker` agent for the browser automation work.

---

## Stage 3: Generate Report

Compile all collected listing data, photos, and Google Maps images into a formatted HTML report (preferred) or PDF.

1. Read `data/output/listings.json`. Validate that listings exist and most have internet data.
2. Read `data/config.json` for key locations and report settings
3. Read `data/output/reviewed.json` if it exists (for favorites/review badges)
4. Load the `listing-evaluation` skill to compute a final score for each listing (includes hipness + safety components)
5. Score each listing using the rubric (0-100 scale)
6. Sort listings by score (highest first)

7. **Fetch Google Maps images** for each listing (requires API key from `data/.env`):
   - Static Maps API: `https://maps.googleapis.com/maps/api/staticmap?center={address}&zoom=15&size=600x300&key={API_KEY}`
   - Street View Static API: `https://maps.googleapis.com/maps/api/streetview?size=600x400&location={address}&key={API_KEY}`
   - Download via `curl` to `data/output/screenshots/{id}-map.jpg` and `data/output/screenshots/{id}-streetview.jpg`

8. **Build HTML report** (primary format) using the `Write` tool:

   **Cover Section:**
   - Gradient header: "Portland — Apartment & Office Space Search Report"
   - Date generated
   - Search parameters: target area, rooms, bathroom, kitchenette, fiber preferred
   - Total listings found, fiber-available count, deduplication summary

   **Favorites Summary** (if `reviewed.json` has favorites):
   - Quick list of all favorited listings with links to their cards
   - Price changes on favorites since last report highlighted

   **Interactive Map** (Leaflet.js — see `report-builder` agent for implementation):
   - OpenStreetMap tiles, centered on Portland
   - Color-coded pins for each listing (green 80+, yellow 60-79, orange 40-59, red below 40)
   - Popup on click: address, price, score, hipness/safety tiers, link to detail card
   - Key locations from `data/config.json` as blue markers

   **Summary Rankings Table** (below map):
   - All listings ranked by score
   - Columns: Rank, Badges (⭐/✓/NEW), Address, Price, Rooms, Internet, Hipness, Safety, Score
   - Internet/hipness/safety badges (color-coded)
   - Top 5 highlighted
   - Rejected listings hidden by default (toggleable)

   **Per-Listing Cards** (one per listing, sorted by score):
   - **Header**: Address + Score badge + status badges (⭐/✓/NEW)
   - **Link**: Clickable URL to original listing + `also_listed_on` links if cross-listed
   - **Photo Gallery**: Up to 8 photos (responsive grid) + floor plan if available
   - **Street View + Google Maps**: Static images for the address
   - **All images clickable** with lightbox overlay for full-size viewing
   - **Stats**: Price, bedrooms, bathrooms, sqft, kitchen type, listing type, neighborhood
   - **Price Context**: Days on market, price trend (↓/→/↑), price history timeline
   - **Lease Terms**: Deposit, pet policy, parking, utilities (if extracted)
   - **Description** and **Amenities** list
   - **Internet Summary**: Text-based provider info with classification
   - **Hipness**: Score badge + tier + buzz highlights (new openings, Reddit mentions)
   - **Safety**: Score badge + tier + safety notes + noise sources
   - **Distances**: To each key location from `data/config.json`
   - Note: Score breakdown table is NOT shown in individual cards (only in the summary table)

   **Methodology Section:**
   - Data sources, scoring rubric (including hipness + safety), internet classification criteria, deduplication approach

   **Filename**: `data/output/portland-apartment-report-YYYYMMDD-HHMM.html` (timestamped)

9. **Alternative: Build PDF** if user requests PDF format, using the `anthropic-skills:pdf` skill. PDF also includes photo galleries. Save to `data/output/portland-apartment-report.pdf`.

10. Tell user: "Report generated at data/output/portland-apartment-report-YYYYMMDD-HHMM.html with X listings."

11. **Ask about Notion**: After the report is generated, ask the user:
   > "Would you like me to create this report as a Notion document in the Document Hub?"

   If yes, create a page in the Document Hub database (data source `collection://1df03407-763c-8098-81b8-000b500508b8`) using the `notion-create-pages` tool:
   - **Doc name**: "Portland Office/Apartment Search Report — {Month} {Year}"
   - **Category**: `["Planning"]`
   - **Content**: Convert the report into Notion-flavored Markdown — summary rankings table, per-listing details (address, price, beds/baths, sqft, neighborhood, internet classification, score), and methodology section

#### Expected Output
- `data/output/portland-apartment-report-YYYYMMDD-HHMM.html` (primary, timestamped)
- `data/output/portland-apartment-report.pdf` (alternative, if requested)
- Notion document in Document Hub (if user accepts)
- Chat confirmation with listing count and top 3 recommendations

#### Delegation
Spawns the `report-builder` agent for HTML/PDF assembly.
