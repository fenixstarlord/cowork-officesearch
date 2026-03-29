---
description: Search Portland listing sites for houses and buildings for sale (residential + commercial) under $700k
argument-hint: "[max_results] [neighborhood]"
allowed-tools: mcp__Claude_in_Chrome__navigate, mcp__Claude_in_Chrome__find, mcp__Claude_in_Chrome__read_page, mcp__Claude_in_Chrome__computer, mcp__Claude_in_Chrome__form_input, mcp__Claude_in_Chrome__get_page_text, mcp__Claude_in_Chrome__javascript_tool, mcp__Claude_in_Chrome__tabs_context_mcp, mcp__Claude_in_Chrome__tabs_create_mcp
---

# /purchase:search-listings

Search residential and commercial listing sites for properties for sale in Portland's target area, under $700k.

## Inputs
- `max_results` (optional): Maximum total listings to collect. Default: 20
- `neighborhood` (optional): Specific neighborhood to focus on. Default: all target neighborhoods per `portland-geography` skill

## Workflow

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
      - Extract up to 4 gallery photos via `javascript_tool` and download with `curl`
      - Build a listing JSON object per the purchase schema in `purchase-search-resources` skill
      - Add to listings array
   g. Navigate back to results or next site

7. **For each commercial sale site** (LoopNet, Craigslist commercial):
   a. Navigate to the site's Portland for-sale URL
   b. Apply filters: max price $700,000, search for "mixed use", "live work", "retail", "office"
   c. Extract listings following the same pattern
   d. Set `listing_type` to "commercial" or "mixed-use"

8. Write the complete listings array to `data/output/purchase-listings.json`
9. Report summary to user: "Found X properties for sale across Y sites (Z residential, W commercial)"

## Expected Output
- `data/output/purchase-listings.json` populated with listing objects (internet field set to null)
- Photos saved in `data/output/screenshots/`
- Chat summary with counts

## CAPTCHA Handling
Same as rental — screenshot, ask user to solve, wait, resume.

## Delegation
Spawns the `apartment-finder` agent for the browser automation work (same agent, different filters).
