---
description: End-to-end purchase search — search for-sale listing sites (under $700k), check fiber internet, and sync results to Notion
argument-hint: "[max_results] [neighborhood]"
allowed-tools: mcp__Claude_in_Chrome__navigate, mcp__Claude_in_Chrome__find, mcp__Claude_in_Chrome__read_page, mcp__Claude_in_Chrome__computer, mcp__Claude_in_Chrome__form_input, mcp__Claude_in_Chrome__get_page_text, mcp__Claude_in_Chrome__javascript_tool, mcp__Claude_in_Chrome__tabs_context_mcp, mcp__Claude_in_Chrome__tabs_create_mcp, Read, Bash
---

# /purchase

Run the full purchase search pipeline: search for-sale listing sites (under $700k), check fiber internet at each address, and sync results to a Notion database.

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

6. **For each residential sale site** (Zillow, Redfin, Realtor.com):
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

## Stage 3: Sync to Notion

Score all listings and sync them to the Notion database, where each listing becomes a row with properties and page content.

1. Read `data/output/purchase-listings.json`. Validate that listings exist and most have internet data.
2. Read `data/config.json` for Notion database ID and key locations.
3. Load the `purchase-evaluation` skill to compute a final score for each listing (includes hipness + safety components).
4. Score each listing using the purchase rubric (0-100 scale).
5. Filter to listings where `notion_synced` is not `true` (enables resume after interruption).
6. For each un-synced listing, sync to Notion:
   a. Search the database for an existing page matching this address (Name property)
   b. If found: update the existing page's properties and body content
   c. If not found: create a new page with all properties and body content
   d. On success: set `notion_synced = true` in the JSON and write back immediately
7. Save a CSV backup to `data/output/purchase-listings-YYYYMMDD-HHMM.csv` (text data only, no screenshots).
8. Remove stale listings from Notion — any Purchase rows whose address is no longer in the current results.
9. Report: "Synced X properties to Notion. Y new, Z updated, W skipped, R removed. Top 3: [addresses with scores]."

See the `report-builder` agent for the full Notion database schema, distance calculation, and page body format.

#### Re-Runnability
Stage 3 only syncs listings where `notion_synced` is not `true`. If interrupted, re-running `/purchase` picks up where it left off.

#### Expected Output
- Notion database rows created/updated (one per listing)
- CSV backup at `data/output/purchase-listings-YYYYMMDD-HHMM.csv`
- Stale Notion rows removed (listings no longer in results)
- Chat confirmation with sync counts and top 3 recommendations

#### Delegation
Spawns the `report-builder` agent for Notion sync.
