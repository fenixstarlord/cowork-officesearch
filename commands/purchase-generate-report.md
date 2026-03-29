---
description: Generate an HTML report (preferred) or PDF from collected purchase listing and internet data
allowed-tools: Read, Write, Glob, Bash
---

# /purchase:generate-report

Compile all collected for-sale listing data, photos, and Google Maps images into a formatted HTML report.

## Prerequisites
- `data/output/purchase-listings.json` must exist and have internet data (run `/purchase:search-listings` and `/purchase:check-internet` first)

## Inputs
None — reads from `data/output/purchase-listings.json` and `data/output/screenshots/`

## Workflow

1. Read `data/output/purchase-listings.json`. Validate that listings exist and most have internet data.
2. Read `data/config.json` for key locations and report settings
3. Read `data/output/reviewed.json` if it exists (for favorites/review badges)
4. Load the `purchase-evaluation` skill to compute a final score for each listing (includes hipness + safety components)
5. Score each listing using the purchase rubric (0-100 scale)
6. Sort listings by score (highest first)

5. **Fetch Google Maps images** for each listing (requires API key from `data/.env`):
   - Static Maps API and Street View Static API
   - Download via `curl` to `data/output/screenshots/{id}-map.jpg` and `{id}-streetview.jpg`

6. **Build HTML report** (primary format):

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

7. Tell user: "Report generated with X properties."

8. **Ask about Notion**: After the report is generated, ask the user:
   > "Would you like me to create this report as a Notion document in the Document Hub?"

   If yes, create a page in the Document Hub database (data source from `data/config.json` `notion.data_source_id`) using the `notion-create-pages` tool:
   - **Doc name**: "Portland Properties For Sale Report — {Month} {Year}"
   - **Category**: `["Planning"]`
   - **Content**: Convert the report into Notion-flavored Markdown — summary rankings table, per-listing details (address, price, beds/baths, sqft, lot size, property type, neighborhood, internet classification, score), and methodology section

## Expected Output
- `data/output/portland-purchase-report-YYYYMMDD-HHMM.html` (timestamped)
- Notion document in Document Hub (if user accepts)
- Chat confirmation with listing count and top 3 recommendations

## Delegation
Spawns the `report-builder` agent for HTML assembly.
