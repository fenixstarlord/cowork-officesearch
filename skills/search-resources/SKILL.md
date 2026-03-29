---
name: search-resources
description: "Use this skill when searching for apartment or rental listings. Contains listing sites, site-specific search strategies, filter navigation paths, data extraction patterns, price history extraction, and lease term scraping."
user-invocable: false
---

## Residential Listing Sites

| Site | Base URL | Strategy |
|------|----------|----------|
| Zillow Rentals | `https://www.zillow.com/portland-or/rentals/` | Apply filters for 2+ beds, zoom to SE Portland on map, use `read_page` for listing cards, click into each for amenities |
| Apartments.com | `https://www.apartments.com/portland-or/` | Use search bar with neighborhood name, filter 2+ beds, scroll cards |
| Craigslist Portland | `https://portland.craigslist.org/search/apa` | Append `?min_bedrooms=2&postal=97202&search_distance=3`, look for keywords "live/work", "mixed use", "home office" |
| HotPads | `https://hotpads.com/portland-or/apartments-for-rent` | Filter panel 2+ beds, map-based zoom to SE |
| Redfin | `https://www.redfin.com/city/30772/OR/Portland/apartments-for-rent` | Filter 2+ beds, check both Apartment and House types |

## Additional Listing Sources

| Site | Base URL | Strategy |
|------|----------|----------|
| Facebook Marketplace | `https://www.facebook.com/marketplace/portland/propertyrentals/` | Filter by price, bedrooms. Many FSBO/private listings not on major sites. Login required — ask user to log in first. |
| Nextdoor | `https://nextdoor.com/for_sale_and_free/?search=rental` | Community-sourced listings, often private landlords. Login required — ask user to log in first. |

**Note**: Facebook Marketplace and Nextdoor require user login. Before searching these sites, ask the user: "I need to search Facebook Marketplace / Nextdoor. Please log in to [site] in the browser, then tell me when you're ready." Skip if user declines.

## Commercial/Mixed-Use Listing Sites

| Site | Base URL | Strategy |
|------|----------|----------|
| LoopNet | `https://www.loopnet.com/search/commercial-real-estate/portland-or/for-lease/` | Search for "mixed use" or "live/work", filter to SE Portland |
| CommercialCafe | `https://www.commercialcafe.com/commercial-real-estate/us/or/portland/` | Search mixed-use listings |
| Craigslist Commercial | `https://portland.craigslist.org/search/off` | Office/commercial section, search "live work" or "mixed use" |

## ISP Coverage Checker Sites

| Provider | URL | Role |
|----------|-----|------|
| BroadbandNow | `https://broadbandnow.com/` | **PRIMARY** -- aggregates all providers in one lookup. Uses Google Places autocomplete. |
| CenturyLink/Lumen | `https://www.centurylink.com/home/internet.html` | FALLBACK only |
| Ziply Fiber | `https://ziplyfiber.com/check-availability` | FALLBACK only |
| Xfinity | `https://www.xfinity.com/learn/internet-service` | FALLBACK only |

## Search Strategy Per Site

Step-by-step Chrome tool usage pattern for each listing site:

1. `navigate` to base URL
2. `find` filter controls (bedroom dropdown, neighborhood input)
3. `form_input` to set filter values
4. `computer` click to apply filters
5. `read_page` to get listing cards from results
6. Click into individual listings — prefer `navigate` with the href from `read_page` over `computer` click (more reliable)
7. Use `find` + `read_page` to extract listing details (address heading, beds/baths, amenities list). **Avoid `get_page_text`** on Craigslist — it often returns empty; structured extraction via `find`/`read_page` is more reliable.
8. Extract listing photos via `javascript_tool` (see Craigslist-Specific Patterns) and download with `curl`. **Do NOT use `computer` `screenshot` with `save_to_disk`** -- it never writes to disk. No ISP screenshots needed -- internet data is text-only from BroadbandNow.

### Craigslist-Specific Patterns (Tested)

- Gallery view loads reliably with URL params: `?min_bedrooms=2&postal=97202&search_distance=3`
- `find` "listing cards" returns all results with neighborhood, price, beds, sqft visible in card metadata
- To find specific listings, search by partial title text: `find` "Beautiful Contemporary Townhouse Brooklyn listing" — returns the exact link element with href. Faster than reading all cards.
- Each card has a link `href` — use `read_page` on the card ref to get the URL, then `navigate` directly
- To find listings by neighborhood: `find` "listing cards with SE Portland neighborhood names" returns refs for neighborhood text nodes — then read the parent card for URLs
- On listing detail pages: address is in a heading element, beds/baths in sidebar, amenities are link elements
- Property name, full address, and description are in a `region` element — use `read_page` with its ref
- **Photo gallery extraction**: Use `javascript_tool` to get up to 4 gallery image URLs:
  ```js
  var thumbs = document.querySelectorAll('.thumb img');
  var urls = [];
  thumbs.forEach(function(t) { if(t.src) urls.push(t.src.replace('_50x50c.jpg','_600x450.jpg')); });
  JSON.stringify(urls.slice(0,8))
  ```
  Download each with `curl -s -o data/output/screenshots/{id}-{n}.jpg "{url}"` (n = 1 through 8, configurable via `data/config.json` `max_photos_per_listing`). Do NOT rely on Chrome `save_to_disk` screenshots — they exist only in extension memory and never write to disk.

  **Floor plan extraction**: If the listing has a floor plan image (common on Zillow, Apartments.com), extract it separately:
  ```js
  var fp = document.querySelector('[alt*="floor plan"], [alt*="Floor Plan"], .floor-plan img');
  fp ? fp.src : null
  ```
  Download to `data/output/screenshots/{id}-floorplan.jpg` if found.

### Chrome Extension Troubleshooting

If `computer` actions (screenshot, click, key) fail with "Cannot access a chrome-extension:// URL", the read-only tools (`navigate`, `find`, `read_page`, `form_input`, `get_page_text`) will still work. Ask the user to:
1. Disable conflicting Chrome extensions
2. Restart Chrome
3. Re-run the search

## Price History & Trends

When visiting individual listing detail pages, extract price history data if available:

**Zillow**: Look for "Price History" section on listing page — contains date, event (listed, price change, sold), and price
**Redfin**: Look for "Price Insights" or "Price History" section — similar format
**Apartments.com**: May show "Price Change" indicators on listing cards
**Craigslist**: No history available — note original post date only

Extract into the listing object:
```json
{
  "price_history": [
    {"date": "2026-03-01", "event": "Listed", "price": 1850},
    {"date": "2026-03-15", "event": "Price drop", "price": 1750}
  ],
  "days_on_market": 28,
  "price_trend": "dropping"
}
```

If no history is available, set `"price_history": null`.

## Lease Terms Extraction

When on a listing detail page, also extract lease/move-in terms if visible:

**Keywords to scan for**:
- Lease length: "12 month", "6 month", "month-to-month", "flexible lease"
- Move-in costs: "deposit", "first/last", "application fee", "move-in special"
- Pet policy: "pets allowed", "no pets", "cats ok", "dogs ok", "pet deposit", "pet rent"
- Parking: "parking included", "garage", "off-street", "street parking", "parking fee"
- Utilities: "utilities included", "water included", "tenant pays", "gas/electric"

Extract into the listing object:
```json
{
  "lease_terms": {
    "lease_length": "12 months",
    "deposit": 1850,
    "application_fee": 50,
    "pet_policy": "cats ok, no dogs",
    "parking": "off-street included",
    "utilities": "water/sewer/trash included, tenant pays electric/gas",
    "move_in_special": null
  }
}
```

If terms are not visible, set `"lease_terms": null`.

## No Price Cap

Collect all listings regardless of price. The `listing-evaluation` skill handles price weighting in scoring.

## JSON Data Schema

Each listing should be stored as a JSON object following this structure:

```json
{
  "id": "zillow-12345",
  "source": "zillow",
  "url": "https://...",
  "address": "1234 SE Powell Blvd, Portland, OR 97202",
  "price": 1850,
  "bedrooms": 2,
  "bathrooms": 1,
  "sqft": 950,
  "has_kitchen": true,
  "has_kitchenette": false,
  "amenities": ["dishwasher", "laundry in unit"],
  "description_excerpt": "...",
  "neighborhood": "Hosford-Abernethy",
  "listing_type": "residential",
  "photo_paths": ["data/output/screenshots/zillow-12345-1.jpg", "data/output/screenshots/zillow-12345-2.jpg"],
  "floorplan_path": null,
  "also_listed_on": [],
  "price_history": null,
  "days_on_market": null,
  "price_trend": null,
  "lease_terms": null,
  "hipness_score": null,
  "hipness_breakdown": null,
  "hipness_buzz": null,
  "hipness_tier": null,
  "safety_score": null,
  "safety_breakdown": null,
  "safety_details": null,
  "safety_tier": null,
  "is_new": false,
  "internet": null
}
```

## Internet Enrichment Schema

Added by Stage 2 (fiber-internet-check) after the initial listing is collected. No ISP screenshots needed — text data only:

```json
{
  "internet": {
    "providers_found": 5,
    "quantum_fiber": { "available": true, "fiber": true, "max_down": 8000, "price_from": 45 },
    "xfinity": { "available": true, "fiber": false, "max_down": 2000, "connection": "Cable", "price_from": 40 },
    "att": { "available": true, "max_down": 300, "connection": "5G", "price_from": 65 },
    "tmobile": { "available": true, "max_down": 415, "connection": "5G", "price_from": 50 },
    "centurylink": { "available": true, "fiber": true, "max_down": 940, "price_from": 50 },
    "broadbandnow_summary": "5 providers. Fiber: Quantum Fiber (8 Gbps), CenturyLink (940 Mbps). Cable: Xfinity (2 Gbps).",
    "classification": "Excellent"
  }
}
```
