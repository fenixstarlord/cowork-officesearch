# Portland Office Search

Claude Code project that searches for live/work spaces in Portland, OR, checks fiber internet availability at each address, and syncs results to a Notion database with scores and detailed data. Supports both **rental** and **purchase** searches.

## Prerequisites

- Claude Code with Cowork mode
- [Claude in Chrome](https://chromewebstore.google.com/detail/claude-in-chrome) extension installed and connected
- Active Chrome browser window
- Notion connector enabled in Cowork (for syncing listings to database)
- Google Maps API key in `data/.env`:
  ```
  GOOGLE_MAPS_API_KEY=your_key_here
  ```
  (Required for listing photo downloads and distance calculations)

## Commands

```
/rent       # Full rental pipeline: search → check internet → sync to Notion
/purchase   # Full purchase pipeline: search → check internet → sync to Notion
```

Each pipeline command runs all three stages end-to-end. If interrupted, re-running picks up where it left off.

## Interactive Search Flow

When you run `/rent`, the project asks four questions before searching:

1. **Room count** -- How many bedrooms? (Studio, 1, 2, 3+)
2. **Square footage** -- Minimum square footage? (Any, 500+, 700+, 900+, 1000+)
3. **Price maximum** -- Max monthly rent? (No cap, $1,500, $2,000, $2,500, $3,000, custom)
4. **Mixed-use preference** -- Need mixed-use/commercial zoning? (Yes, No, Preferred but not required)

Kitchen and fiber internet are always required and not asked. After confirming criteria, the project translates them to site-specific filters and searches across listing sites.

Purchase searches use the `$700k` price cap and search residential + commercial for-sale sites.

## Target Area

Central Portland on both sides of the Willamette River:

- **East side**: Buckman, Hosford-Abernethy, Richmond, Sunnyside, Hawthorne, Belmont, Brooklyn, Creston-Kenilworth, Sellwood-Moreland, Laurelhurst, and more
- **West side**: Pearl District, Downtown, Goose Hollow, South Portland
- **Inner NE**: Irvington, Grant Park, Hollywood, Sullivan's Gulch

## Notion Database Output

Each listing becomes a row in a Notion database with 28 properties:

- **Core**: Address, Price, Score (0-100), Bedrooms, Bathrooms, Sqft, Neighborhood
- **Classification**: Type (Rental/Purchase), Listing Type, Property Type, Source
- **Internet**: Classification (Excellent/Good/Adequate/Poor), Provider details
- **Scoring**: Hipness score + tier, Safety score + tier
- **Market**: Price Trend, Days on Market
- **Links**: Listing URL, Street View, Google Maps, Also Listed On
- **Details**: Terms, Hipness Notes, Safety Notes

Each listing's **page body** contains: description, amenities, driving distances to key locations (via Google Maps Distance Matrix API), full internet provider breakdown, and price history.

Re-running updates existing rows (matched by address) rather than creating duplicates. Use Notion's built-in views to sort, filter, and group listings.

## Listing Sites Searched

**Residential rentals**: Zillow, Apartments.com, Craigslist Portland, HotPads, Redfin
**Commercial rentals**: LoopNet, CommercialCafe, Craigslist (commercial/office)
**For-sale residential**: Zillow, Redfin, Realtor.com, Craigslist
**For-sale commercial**: LoopNet, CommercialCafe, Craigslist

## Internet Checking

BroadbandNow is the primary ISP checker -- one address lookup returns all providers (Quantum Fiber, CenturyLink, Xfinity, AT&T, T-Mobile, etc.). Direct ISP sites (CenturyLink, Ziply, Xfinity) are fallbacks only. Internet data is text-based; no ISP screenshots are captured.

## Project Structure

```
.claude/
  commands/
    rent.md                            # /rent — full rental pipeline
    purchase.md                        # /purchase — full purchase pipeline
  skills/
    search-resources/SKILL.md          # Rental site URLs, strategies, JSON schema
    purchase-search-resources/SKILL.md # For-sale site URLs, strategies, purchase JSON schema
    portland-geography/SKILL.md        # Neighborhoods, zip codes, corridors, transit
    fiber-internet-check/SKILL.md      # BroadbandNow procedures, ISP fallbacks
    listing-evaluation/SKILL.md        # Rental scoring rubric (0-100)
    purchase-evaluation/SKILL.md       # Purchase scoring rubric (0-100, $700k cap)
    hipness-scoring/SKILL.md           # Area hipness/vibrancy scoring
    safety-scoring/SKILL.md            # Neighborhood safety and noise scoring
    deduplication/SKILL.md             # Cross-site listing deduplication
  agents/
    apartment-finder.md                # Browser automation for listing extraction
    internet-checker.md                # BroadbandNow + ISP fallback automation
    report-builder.md                  # Scores listings and syncs to Notion

data/
  .env                                 # Google Maps API key (gitignored)
  config.json                          # Key locations, search defaults, Notion database ID
  output/                              # Runtime outputs (gitignored)
    listings.json                      # Rental listings
    purchase-listings.json             # Purchase listings
    screenshots/                       # Listing photos
```

## Data Flow

```
Stage 1: Search Listings
  Browser automation -> extract listing data + download photos
  -> data/output/listings.json (or data/output/purchase-listings.json)
  -> data/output/screenshots/{id}-1.jpg through {id}-8.jpg

Stage 2: Check Internet
  Read listings.json -> BroadbandNow lookups -> enrich with internet data
  -> data/output/listings.json (updated with internet field)

Stage 3: Sync to Notion
  Read listings.json -> score each listing -> create/update Notion database rows
  -> Notion database (one row per listing, 28 properties + page body)
```

## CAPTCHA Handling

When a site shows a CAPTCHA, the project pauses and asks you to solve it in the visible Chrome browser window. Tell Claude in chat when you are done and it will continue.
