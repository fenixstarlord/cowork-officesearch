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
2. Load the `listing-evaluation` skill to compute a final score for each listing
3. Score each listing using the rubric (0-100 scale)
4. Sort listings by score (highest first)

5. **Fetch Google Maps images** for each listing (requires API key from `data/.env`):
   - Static Maps API: `https://maps.googleapis.com/maps/api/staticmap?center={address}&zoom=15&size=600x300&key={API_KEY}`
   - Street View Static API: `https://maps.googleapis.com/maps/api/streetview?size=600x400&location={address}&key={API_KEY}`
   - Download via `curl` to `data/output/screenshots/{id}-map.jpg` and `data/output/screenshots/{id}-streetview.jpg`

6. **Build HTML report** (primary format) using the `Write` tool:

   **Cover Section:**
   - Gradient header: "Portland Inner SE — Apartment & Office Space Search Report"
   - Date generated
   - Search parameters: Inner SE Portland, 2+ rooms, bathroom, kitchenette, fiber preferred
   - Total listings found, fiber-available count

   **Summary Rankings Table** (near top):
   - All listings ranked by score
   - Columns: Rank, Address, Price, Rooms, Fiber?, Internet Class, Score
   - Internet availability badges (color-coded)
   - Top 5 highlighted

   **Per-Listing Cards** (one per listing, sorted by score):
   - **Header**: Address + Score badge (Excellent/Good/Marginal)
   - **Link**: Clickable URL to original Craigslist listing
   - **2x2 Photo Gallery**: Up to 4 photos from Craigslist CDN (from `photo_paths` array)
   - **Street View + Google Maps**: Static images for the address
   - **All images clickable** with lightbox overlay for full-size viewing
   - **Stats**: Price, bedrooms, bathrooms, sqft, kitchen type, listing type, neighborhood
   - **Description** and **Amenities** list
   - **Internet Summary**: Text-based provider info with classification (no ISP screenshots)
   - Note: Score breakdown table is NOT shown in individual cards (only in the summary table)

   **Methodology Section:**
   - Data sources, scoring rubric, internet classification criteria

   **Filename**: `data/output/portland-apartment-report-YYYYMMDD-HHMM.html` (timestamped)

7. **Alternative: Build PDF** if user requests PDF format, using the `anthropic-skills:pdf` skill. PDF also includes photo galleries. Save to `data/output/portland-apartment-report.pdf`.

8. Tell user: "Report generated at data/output/portland-apartment-report-YYYYMMDD-HHMM.html with X listings."

9. **Ask about Notion**: After the report is generated, ask the user:
   > "Would you like me to create this report as a Notion document in the Document Hub?"

   If yes, create a page in the Document Hub database (data source `collection://1df03407-763c-8098-81b8-000b500508b8`) using the `notion-create-pages` tool:
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
