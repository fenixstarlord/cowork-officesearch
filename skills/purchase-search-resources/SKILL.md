---
name: purchase-search-resources
description: "Use this skill when searching for houses or buildings for sale in Portland. Contains listing sites, strategies, purchase JSON schema, price history extraction, and sale term scraping."
user-invocable: false
---

## Residential For-Sale Sites

| Site | Base URL | Strategy |
|------|----------|----------|
| Zillow | `https://www.zillow.com/portland-or/` | Filter: For Sale, max $700k, include House + Multi-Family + Condo. Use multiple zip code searches per `portland-geography`. |
| Redfin | `https://www.redfin.com/city/30772/OR/Portland` | Filter: For Sale, max $700k, all property types. Map-based zoom to target area. |
| Realtor.com | `https://www.realtor.com/realestateandsales/Portland_OR` | Filter: max price $700k, all property types. |
| Craigslist | `https://portland.craigslist.org/search/rea` | Real estate for sale section. Append `?max_price=700000`. Search for "house", "building", "mixed use", "duplex". |

## Additional For-Sale Sources

| Site | Base URL | Strategy |
|------|----------|----------|
| Facebook Marketplace | `https://www.facebook.com/marketplace/portland/propertyforsale/` | FSBO listings, often not on MLS. Login required — ask user to log in first. |
| Nextdoor | `https://nextdoor.com/for_sale_and_free/?search=house+for+sale` | Community-sourced FSBO listings. Login required — ask user to log in first. |

**Note**: Facebook Marketplace and Nextdoor require user login. Ask the user to log in before searching these sites.

## Commercial For-Sale Sites

| Site | Base URL | Strategy |
|------|----------|----------|
| LoopNet | `https://www.loopnet.com/search/commercial-real-estate/portland-or/for-sale/` | Filter max $700k. Search "mixed use", "live work", "retail", "office". |
| Craigslist Commercial | `https://portland.craigslist.org/search/rea` | Search "commercial", "mixed use", "live work", "building" with max $700k. |
| CommercialCafe | `https://www.commercialcafe.com/commercial-real-estate/us/or/portland/` | Search for-sale listings, filter to $700k max. |

## Price Cap

**Maximum price: $700,000.** Apply this filter on every site. Include both residential and commercial properties.

## Property Types to Include

- Single-family houses
- Duplexes / triplexes / fourplexes
- Multi-family buildings
- Mixed-use (commercial + residential)
- Commercial buildings (office, retail) suitable for live/work conversion
- Condos/townhouses (if they allow commercial use)

## JSON Data Schema

```json
{
  "id": "zillow-12345",
  "source": "zillow",
  "url": "https://...",
  "address": "1234 SE Powell Blvd, Portland, OR 97202",
  "price": 550000,
  "bedrooms": 3,
  "bathrooms": 2,
  "sqft": 1800,
  "lot_sqft": 5000,
  "year_built": 1924,
  "property_type": "single-family",
  "has_kitchen": true,
  "amenities": ["garage", "basement", "hardwood floors"],
  "description_excerpt": "...",
  "neighborhood": "Hosford-Abernethy",
  "listing_type": "residential",
  "photo_paths": ["data/output/screenshots/zillow-12345-1.jpg", "..."],
  "floorplan_path": null,
  "also_listed_on": [],
  "price_history": null,
  "days_on_market": null,
  "price_trend": null,
  "previous_sales": null,
  "estimated_value": null,
  "sale_terms": null,
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

Same as rental — added by `/purchase:check-internet`:

```json
{
  "internet": {
    "providers_found": 5,
    "quantum_fiber": { "available": true, "fiber": true, "max_down": 8000, "price_from": 45 },
    "xfinity": { "available": true, "fiber": false, "max_down": 2000, "connection": "Cable", "price_from": 40 },
    "broadbandnow_summary": "5 providers. Fiber: Quantum Fiber (8 Gbps)...",
    "classification": "Excellent"
  }
}
```

## Price History & Trends

When visiting individual listing detail pages, extract price/sale history if available:

**Zillow**: "Price History" section — dates, events (listed, price change, pending, sold), and prices. Also check "Zestimate" for estimated value.
**Redfin**: "Price Insights" and "Sale History" — includes previous sales, price changes
**Realtor.com**: "Price History" section — similar format
**Craigslist**: No history — note original post date only

Extract into the listing object:
```json
{
  "price_history": [
    {"date": "2026-01-15", "event": "Listed", "price": 599000},
    {"date": "2026-02-20", "event": "Price drop", "price": 575000}
  ],
  "days_on_market": 73,
  "price_trend": "dropping",
  "previous_sales": [
    {"date": "2018-06-01", "price": 425000}
  ],
  "estimated_value": 590000
}
```

## Sale Terms Extraction

When on a listing detail page, also extract sale terms if visible:

**Keywords to scan for**:
- HOA fees: "HOA", "monthly dues", "association fee"
- Property tax: "tax", "property tax", "annual tax"
- Zoning: "zoned", "zoning", "R1", "C1", "MU", "mixed-use"
- Special assessments: "assessment", "LID"
- Financing notes: "assumable loan", "seller financing", "cash only"

Extract into the listing object:
```json
{
  "sale_terms": {
    "hoa_monthly": 250,
    "property_tax_annual": 5400,
    "zoning": "R2.5 (residential, duplex allowed)",
    "special_assessments": null,
    "financing_notes": null
  }
}
```

If terms are not visible, set `"sale_terms": null`.

## Photo Extraction

Same patterns as rental — use `javascript_tool` to extract gallery image URLs and download with `curl`. Site-specific selectors may vary:
- **Zillow**: Look for `img` elements in the photo carousel/gallery
- **Redfin**: Photo gallery container with `img` elements
- **Craigslist**: `.thumb img` with URL replacement (tested)
- **LoopNet**: Gallery/carousel images

Extract up to 8 photos per listing (configurable via `data/config.json` `max_photos_per_listing`). Also extract floor plan images if available — save to `{id}-floorplan.jpg`.
