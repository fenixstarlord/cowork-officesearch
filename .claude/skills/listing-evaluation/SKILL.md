---
name: listing-evaluation
description: "Use this skill to evaluate and score rental listings. Mandatory: kitchen/kitchenette and fiber internet. Scoring based on room count, kitchen quality, price, square footage, mixed-use friendliness, fiber quality, and proximity to key people."
---

## Mandatory Requirements (Must-Have)

A listing MUST meet ALL of these to be included:

- Minimum bedroom count specified by user (default: 2+), OR "Whole house" property style (any bedroom count, property must be a house)
- At least 1 bathroom
- Kitchen or kitchenette (scan for: "kitchen", "kitchenette", "galley kitchen", "cooking area", "stove", "oven", "range", "refrigerator", "microwave")
- Fiber internet available at the address (checked in Stage 2 — if no fiber, downgrade significantly)
- Location within the target area (see `portland-geography` skill)

## Scoring Rubric (0-100 scale)

| Factor | Weight | Scoring |
|--------|--------|---------|
| Room count | 12% | Meets minimum = 9pts, exceeds by 1+ = 12pts. Whole house: 3+ beds = 12pts, 2 beds = 9pts, 1 bed = 6pts |
| Kitchen quality | 8% | Full kitchen = 8pts, kitchenette = 5pts, unclear = 2pts |
| Price reasonableness | 14% | Under $1,800 = 14pts, $1,800-2,200 = 11pts, $2,200-2,800 = 7pts, $2,800-3,500 = 4pts, over $3,500 = 2pts |
| Square footage | 8% | Over 900 sqft = 8pts, 700-900 = 6pts, 500-700 = 4pts, under 500 = 2pts |
| Mixed-use friendliness | 8% | Explicit "live/work" or "home office" = 8pts, ground floor commercial = 6pts, "flex space" / townhouse = 4pts, no mention = 2pts |
| Fiber internet quality | 10% | Fiber 8Gbps = 10pts, Fiber 940Mbps = 8pts, gigabit cable only = 4pts, cable only = 2pts, no data = 0pts |
| Food proximity (indie) | 12% | Near indie food corridor = 12pts, mixed indie/chain = 8pts, mostly chains = 4pts, chain-heavy/no food = 2pts |
| Main street location | 10% | On a main street = 10pts, 1-2 blocks away = 8pts, 3-5 blocks = 5pts, not near = 2pts |
| Hipness score | 9% | See `hipness-scoring` skill. Score mapped: 85+ = 9pts, 70-84 = 7pts, 55-69 = 5pts, 40-54 = 3pts, below 40 = 1pt |
| Safety score | 9% | See `safety-scoring` skill. Score mapped: 80+ = 9pts, 65-79 = 7pts, 50-64 = 5pts, 35-49 = 3pts, below 35 = 1pt |

## Food Proximity

Prioritize listings near **well-rated, independently owned** restaurants and cafes. Chain restaurants detract from the score.

**Indie food corridors** (score highest):
- SE Hawthorne Blvd, SE Division St, SE Belmont St, SE Clinton St
- NE/N Alberta St, N Mississippi Ave, NE/N Williams Ave
- NW 23rd Ave, NW 21st Ave
- SE Foster Rd (Foster-Powell section), SE Woodstock Blvd
- SE 13th Ave (Sellwood), SE Milwaukie Ave

**Chain-heavy corridors** (score lowest):
- SE 82nd Ave, outer SE Powell Blvd (east of 52nd), outer NE Sandy Blvd (east of Hollywood)

## Main Streets

Listings on or near these streets score higher:

- SE Hawthorne Blvd, SE Division St, SE Belmont St, SE Powell Blvd
- SE Clinton St, SE Foster Rd, SE Woodstock Blvd, SE Milwaukie Ave
- NE/SE Broadway, NE/SE Sandy Blvd, NE/SE MLK Jr Blvd, SE 12th Ave
- W/E Burnside St, NW 23rd Ave, NW 21st Ave, SW Macadam Ave
- NE/N Alberta St, N Mississippi Ave, NE/N Williams Ave

## Key Locations for Distance Calculation

Key locations are configured in `data/config.json` under `key_locations`. Each entry has a `name` and `address`. The default locations are:

| Name | Address |
|------|---------|
| **Chris** | 10363 SE 24th Ave, Portland, OR |
| **George** | 3816 SW Lee St, Portland, OR 97221 |
| **Jasmine** | 3521 SE Main St, Portland, OR 97214 |

To add, remove, or change key locations, edit `data/config.json`. Distance calculations dynamically read from this config — no code changes needed.

Distances are calculated as driving distance via the Google Maps Distance Matrix API and displayed in each Notion listing page.

## Disqualifiers (Auto-Reject)

- No bathroom listed
- Located outside Portland city limits
- Shared kitchen or shared bathroom (unless user explicitly allows)
- Listing is clearly a scam (no photos, suspicious price, vague location)
- No fiber internet available (unless user overrides)

## Mixed-Use Keywords

Scan listing descriptions and amenities for these terms:

- "live/work", "mixed use", "home office", "commercial"
- "zoned commercial", "retail below", "ground floor"
- "flex space", "creative space", "artist loft", "studio/loft"
- "work from home", "office space", "business use"

## Listing Type Classification

- **Residential with office potential**: Standard apartment with extra room, allows home business
- **Mixed-use**: Zoned for both residential and commercial
- **Live/work**: Explicitly designed for living and working
- **Commercial with residential**: Commercial space with living quarters

## Score Interpretation

- **80-100**: Excellent match — prioritize
- **60-79**: Good match — include in report
- **40-59**: Marginal — include if few better options
- **Below 40**: Poor match — exclude
