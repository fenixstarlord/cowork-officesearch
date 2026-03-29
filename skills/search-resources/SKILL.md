---
name: search-resources
description: "Use this skill when searching for apartment or rental listings, or when checking internet availability. Contains the definitive list of listing sites, ISP coverage checker URLs, site-specific search strategies, filter navigation paths, and data extraction patterns for each source."
---

## Residential Listing Sites

| Site | Base URL | Strategy |
|------|----------|----------|
| Zillow Rentals | `https://www.zillow.com/portland-or/rentals/` | Apply filters for 2+ beds, zoom to SE Portland on map, use `read_page` for listing cards, click into each for amenities |
| Apartments.com | `https://www.apartments.com/portland-or/` | Use search bar with neighborhood name, filter 2+ beds, scroll cards |
| Craigslist Portland | `https://portland.craigslist.org/search/apa` | Append `?min_bedrooms=2&postal=97202&search_distance=3`, look for keywords "live/work", "mixed use", "home office" |
| HotPads | `https://hotpads.com/portland-or/apartments-for-rent` | Filter panel 2+ beds, map-based zoom to SE |
| Redfin | `https://www.redfin.com/city/30772/OR/Portland/apartments-for-rent` | Filter 2+ beds, check both Apartment and House types |

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
  JSON.stringify(urls.slice(0,4))
  ```
  Download each with `curl -s -o data/output/screenshots/{id}-{n}.jpg "{url}"` (n = 1-4). Do NOT rely on Chrome `save_to_disk` screenshots — they exist only in extension memory and never write to disk.

### Chrome Extension Troubleshooting

If `computer` actions (screenshot, click, key) fail with "Cannot access a chrome-extension:// URL", the read-only tools (`navigate`, `find`, `read_page`, `form_input`, `get_page_text`) will still work. Ask the user to:
1. Disable conflicting Chrome extensions
2. Restart Chrome
3. Re-run the search

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
  "photo_paths": ["data/output/screenshots/zillow-12345-1.jpg", "data/output/screenshots/zillow-12345-2.jpg", "data/output/screenshots/zillow-12345-3.jpg", "data/output/screenshots/zillow-12345-4.jpg"],
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
