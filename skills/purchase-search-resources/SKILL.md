---
name: purchase-search-resources
description: "Use this skill when searching for houses or buildings for sale in Portland. Contains listing sites for residential and commercial properties, site-specific strategies, and the JSON data schema for purchase listings."
---

## Residential For-Sale Sites

| Site | Base URL | Strategy |
|------|----------|----------|
| Zillow | `https://www.zillow.com/portland-or/` | Filter: For Sale, max $700k, include House + Multi-Family + Condo. Use multiple zip code searches per `portland-geography`. |
| Redfin | `https://www.redfin.com/city/30772/OR/Portland` | Filter: For Sale, max $700k, all property types. Map-based zoom to target area. |
| Realtor.com | `https://www.realtor.com/realestateandsales/Portland_OR` | Filter: max price $700k, all property types. |
| Craigslist | `https://portland.craigslist.org/search/rea` | Real estate for sale section. Append `?max_price=700000`. Search for "house", "building", "mixed use", "duplex". |

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
  "photo_paths": ["data/screenshots/zillow-12345-1.jpg", "..."],
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

## Photo Extraction

Same patterns as rental — use `javascript_tool` to extract gallery image URLs and download with `curl`. Site-specific selectors may vary:
- **Zillow**: Look for `img` elements in the photo carousel/gallery
- **Redfin**: Photo gallery container with `img` elements
- **Craigslist**: `.thumb img` with URL replacement (tested)
- **LoopNet**: Gallery/carousel images
