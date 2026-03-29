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
2. Load the `purchase-evaluation` skill to compute a final score for each listing
3. Score each listing using the purchase rubric (0-100 scale)
4. Sort listings by score (highest first)

5. **Fetch Google Maps images** for each listing (requires API key from `data/.env`):
   - Static Maps API and Street View Static API
   - Download via `curl` to `data/output/screenshots/{id}-map.jpg` and `{id}-streetview.jpg`

6. **Build HTML report** (primary format):

   **Cover Section:**
   - Gradient header: "Portland Property Purchase — Live/Work Space Report"
   - Date generated
   - Search parameters: Central Portland, under $700k, residential + commercial
   - Total listings found, fiber-available count

   **Summary Rankings Table:**
   - All listings ranked by score
   - Columns: Rank, Address, Neighborhood, Price, Type, Beds/Bath, Sqft, Internet, Score

   **Per-Listing Cards** (sorted by score):
   - Address + price + property type
   - 2x2 photo gallery
   - Street View + Google Maps
   - All images clickable with lightbox
   - Property details: price, beds, baths, sqft, lot size, year built, property type
   - Description and features
   - Internet summary with classification
   - Link to original listing

   **Methodology Section:**
   - Data sources, scoring rubric, internet classification

   **Filename**: `data/output/portland-purchase-report-YYYYMMDD-HHMM.html`

7. Tell user: "Report generated with X properties."

## Expected Output
- `data/output/portland-purchase-report-YYYYMMDD-HHMM.html` (timestamped)
- Chat confirmation with listing count and top 3 recommendations

## Delegation
Spawns the `report-builder` agent for HTML assembly.
