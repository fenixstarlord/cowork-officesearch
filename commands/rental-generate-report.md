---
description: Generate an HTML report (preferred) or PDF from collected listing and internet data
allowed-tools: Read, Write, Glob, Bash
---

# /rental:generate-report

Compile all collected listing data, photos, and Google Maps images into a formatted HTML report (preferred) or PDF.

## Prerequisites
- `data/output/listings.json` must exist and have internet data (run `/rental:search-listings` and `/rental:check-internet` first)

## Inputs
None — reads from `data/output/listings.json` and `data/output/screenshots/`

## Workflow

1. Read `data/output/listings.json`. Validate that listings exist and most have internet data.
2. Read `data/config.json` for key locations and report settings
3. Read `data/output/reviewed.json` if it exists (for favorites/review badges)
4. Load the `listing-evaluation` skill to compute a final score for each listing (includes hipness + safety components)
5. Score each listing using the rubric (0-100 scale)
6. Sort listings by score (highest first)

5. **Fetch Google Maps images** for each listing (requires API key from `data/.env`):
   - Static Maps API: `https://maps.googleapis.com/maps/api/staticmap?center={address}&zoom=15&size=600x300&key={API_KEY}`
   - Street View Static API: `https://maps.googleapis.com/maps/api/streetview?size=600x400&location={address}&key={API_KEY}`
   - Download via `curl` to `data/output/screenshots/{id}-map.jpg` and `data/output/screenshots/{id}-streetview.jpg`

6. **Build HTML report** (primary format) using the `Write` tool:

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

7. **Alternative: Build PDF** if user requests PDF format, using the `anthropic-skills:pdf` skill. PDF also includes photo galleries. Save to `data/output/portland-apartment-report.pdf`.

8. Tell user: "Report generated at data/output/portland-apartment-report-YYYYMMDD-HHMM.html with X listings."

9. **Ask about Notion**: After the report is generated, ask the user:
   > "Would you like me to create this report as a Notion document in the Document Hub?"

   If yes, create a page in the Document Hub database (data source from `data/config.json` `notion.data_source_id`) using the `notion-create-pages` tool:
   - **Doc name**: "Portland Office/Apartment Search Report — {Month} {Year}"
   - **Category**: `["Planning"]`
   - **Content**: Convert the report into Notion-flavored Markdown — summary rankings table, per-listing details (address, price, beds/baths, sqft, neighborhood, internet classification, score), and methodology section

## Expected Output
- `data/output/portland-apartment-report-YYYYMMDD-HHMM.html` (primary, timestamped)
- `data/output/portland-apartment-report.pdf` (alternative, if requested)
- Notion document in Document Hub (if user accepts)
- Chat confirmation with listing count and top 3 recommendations

## Delegation
Spawns the `report-builder` agent for HTML/PDF assembly.
