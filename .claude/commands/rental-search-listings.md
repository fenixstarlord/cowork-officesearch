---
description: Search Portland rental listing sites based on user-specified criteria gathered through interactive questions
argument-hint: ""
allowed-tools: mcp__Claude_in_Chrome__navigate, mcp__Claude_in_Chrome__find, mcp__Claude_in_Chrome__read_page, mcp__Claude_in_Chrome__computer, mcp__Claude_in_Chrome__form_input, mcp__Claude_in_Chrome__get_page_text, mcp__Claude_in_Chrome__javascript_tool, mcp__Claude_in_Chrome__tabs_context_mcp, mcp__Claude_in_Chrome__tabs_create_mcp
---

# /rental-search-listings

Search rental listing sites for spaces in Portland matching criteria gathered from the user.

## Step 1: Ask the User

Before searching, ask these questions (use AskUserQuestion or chat):

1. **Room count** — How many bedrooms? (Studio, 1, 2, 3+)
2. **Square footage** — Minimum square footage? (Any, 500+, 700+, 900+, 1000+)
3. **Price maximum** — Max monthly rent? (No cap, $1,500, $2,000, $2,500, $3,000, custom)
4. **Mixed use or business** — Do you need mixed-use/commercial zoning or the ability to run a business from the space? (Yes, No, Preferred but not required)

### Always Required (do not ask)
- Fiber internet availability (checked in Stage 2)
- Kitchen or kitchenette

## Step 2: Confirm and Search

Confirm the parsed criteria:
> "Searching for: [bedrooms], [min sqft], under [price], [mixed-use preference], with kitchen, fiber internet required. Sound right?"

## Step 3: Execute Search

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

## Craigslist URL Parameter Reference

```
?min_bedrooms=2&max_price=2000&minSqft=700&postal=97214&search_distance=3
&pets_cat=1&pets_dog=1&laundry=1&parking=1
```

## CAPTCHA Handling
Screenshot, ask user to solve in browser, wait, resume.

## Delegation
Spawns the `apartment-finder` agent for browser automation.
