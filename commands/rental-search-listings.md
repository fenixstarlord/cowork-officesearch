---
description: Search Portland rental listing sites based on user-specified criteria gathered through interactive questions
argument-hint: ""
allowed-tools: mcp__Claude_in_Chrome__navigate, mcp__Claude_in_Chrome__find, mcp__Claude_in_Chrome__read_page, mcp__Claude_in_Chrome__computer, mcp__Claude_in_Chrome__form_input, mcp__Claude_in_Chrome__get_page_text, mcp__Claude_in_Chrome__javascript_tool, mcp__Claude_in_Chrome__tabs_context_mcp, mcp__Claude_in_Chrome__tabs_create_mcp
---

# /rental:search-listings

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
4. Create `data/screenshots/` directory if needed
5. Initialize empty `data/listings.json` array

6. **Translate criteria to site-specific filters:**
   - **Craigslist**: URL params (`min_bedrooms`, `max_price`, `min_sqft`, `postal`, `search_distance`)
   - **Zillow/Redfin**: Filter panel controls
   - **Apartments.com/HotPads**: Search bar + filter panel

7. **For each listing site**, apply filters and extract listings:
   a. Navigate to site URL
   b. Apply user's filters
   c. Use multiple zip code searches for broad target area (per `portland-geography`)
   d. Extract listing cards, click into each
   e. Use `find` + `read_page` for structured data
   f. Extract up to 4 gallery photos via `javascript_tool` + download with `curl`
   g. Build listing JSON objects

8. **If user wants mixed-use**, also search LoopNet, CommercialCafe, Craigslist commercial

9. Write listings to `data/listings.json`
10. Report summary to user

## Craigslist URL Parameter Reference

```
?min_bedrooms=2&max_price=2000&minSqft=700&postal=97214&search_distance=3
&pets_cat=1&pets_dog=1&laundry=1&parking=1
```

## CAPTCHA Handling
Screenshot, ask user to solve in browser, wait, resume.

## Delegation
Spawns the `apartment-finder` agent for browser automation.
