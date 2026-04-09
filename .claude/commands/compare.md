---
description: Generate a side-by-side comparison of 2-3 selected listings
argument-hint: "[listing-id-1] [listing-id-2] [listing-id-3]"
allowed-tools: Read, Write, Bash, Glob
---

# /compare

Create a focused side-by-side comparison of 2-3 listings from the current dataset.

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

### 2. Generate Comparison HTML

Create a self-contained HTML file at `data/output/comparison-YYYYMMDD-HHMM.html` with:

**Layout**: Side-by-side columns (2 or 3 columns depending on input)

**Header Row**: Listing photo (first photo from each) + address

**Comparison Table** (rows for each attribute):

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
| **Hipness Score** | 90 | 72 | 85 |
| **Safety Score** | 68 | 74 | 71 |
| **Walk Score** | 92 | 85 | 88 |
| **Distance to Chris** | 3.2 mi | 4.1 mi | 2.8 mi |
| **Distance to George** | 5.1 mi | 4.8 mi | 5.3 mi |
| **Distance to Jasmine** | 0.8 mi | 1.2 mi | 0.5 mi |

*For purchase listings, also include: lot sqft, year built, property type, HOA fees, property tax*

**Highlight differences**: Cells where one listing clearly wins are highlighted green; worst values are highlighted light red. This makes it easy to see trade-offs at a glance.

**Photo Row**: First 2 photos from each listing side by side

**Map Row**: Google Maps static image for each listing, or a single interactive map with all 2-3 pins

**Pros & Cons Section** (per listing):
Generate a brief pros/cons list based on the data:
- Pros: highest-scoring attributes, unique amenities, best scores
- Cons: lowest-scoring attributes, missing features, concerns

**Links**: Direct links to each original listing

### 3. Styling

Use **Pico CSS v2** for base styling, with custom CSS for:
- Side-by-side column layout (flexbox/grid)
- Highlighted cells (green for best, red for worst per row)
- Responsive design (stacks vertically on mobile)

### 4. Report to User

```
Comparison generated: data/output/comparison-20260329-1430.html

Summary:
  Best price: Listing C ($1,600/mo)
  Best space: Listing B (1,100 sqft, 3bd)
  Best location: Listing C (closest to Jasmine, highest hipness)
  Best internet: Listing A (Fiber 8Gbps)
```
