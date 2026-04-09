---
description: Generate a side-by-side comparison of 2-3 selected listings
argument-hint: "[listing-id-1] [listing-id-2] [listing-id-3]"
allowed-tools: Read, Bash
---

# /compare

Create a focused side-by-side comparison of 2-3 listings from the current dataset, displayed in chat.

## Inputs
- 2 or 3 listing IDs (e.g., `zillow-12345 craigslist-67890 redfin-11111`)
- If no IDs provided, ask the user which listings to compare (show a numbered list of available listings)

## Prerequisites
- `data/output/listings.json` or `data/output/purchase-listings.json` must exist with scored listings

## Workflow

### 1. Load Listings

1. Read both `listings.json` and `purchase-listings.json` to find the requested IDs
2. If an ID isn't found, report the error and list available IDs
3. Load 2-3 matching listing objects

### 2. Display Comparison

Present a markdown comparison table in chat:

```
## Comparison: [Address A] vs [Address B] vs [Address C]

| Attribute | Listing A | Listing B | Listing C |
|-----------|-----------|-----------|-----------|
| **Address** | full address | full address | full address |
| **Price** | $1,850/mo | $2,100/mo | $1,600/mo |
| **Bedrooms** | 2 | 3 | 2 |
| **Bathrooms** | 1 | 1.5 | 1 |
| **Sqft** | 850 | 1,100 | 780 |
| **Price/sqft** | $2.18/sqft | $1.91/sqft | $2.05/sqft |
| **Neighborhood** | Buckman | Richmond | Sunnyside |
| **Kitchen** | Full | Kitchenette | Full |
| **Listing Type** | Residential | Mixed-use | Residential |
| **Internet** | Excellent (Fiber 8Gbps) | Good (Cable 2Gbps) | Excellent (Fiber 940Mbps) |
| **Overall Score** | 82 | 75 | 78 |
| **Hipness** | 90 (Very Hip) | 72 (Very Hip) | 85 (Cultural Epicenter) |
| **Safety** | 68 (Safe) | 74 (Safe) | 71 (Safe) |
| **Distance to Chris** | 3.2 mi | 4.1 mi | 2.8 mi |
| **Distance to George** | 5.1 mi | 4.8 mi | 5.3 mi |
| **Distance to Jasmine** | 0.8 mi | 1.2 mi | 0.5 mi |
```

For purchase listings, also include: lot sqft, year built, property type, HOA fees, property tax.

Mark the **best value** in each row with a note (e.g., "← best").

### 3. Pros & Cons

After the table, provide a brief pros/cons analysis for each listing:

```
### Listing A — 1234 SE Hawthorne Blvd
**Pros**: Best internet (Fiber 8Gbps), highest overall score, on a main street
**Cons**: Highest price, smallest sqft, moderate safety score

### Listing B — 5678 SE Division St
**Pros**: Most space (1,100 sqft, 3bd), mixed-use zoning, best safety
**Cons**: No fiber, lowest overall score, kitchenette only

### Listing C — 910 SE Belmont St
**Pros**: Lowest price, closest to Jasmine, highest hipness
**Cons**: Smallest unit, furthest from George
```

### 4. Links

Include Notion database links and original listing URLs for each listing.
