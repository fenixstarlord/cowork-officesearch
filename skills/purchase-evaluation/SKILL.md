---
name: purchase-evaluation
description: "Use this skill to evaluate and score properties for sale against purchase criteria: under $700k, suitable for live/work use, central Portland location, with hipness and safety scoring."
user-invocable: false
---

## Mandatory Requirements (Must-Have)

A listing MUST meet ALL of these to be included:

- Price at or under $700,000
- At least 2 rooms (bedrooms or usable spaces)
- At least 1 bathroom
- Kitchen or kitchenette
- Location within the target area (see `portland-geography` skill)

## Scoring Rubric (0-100 scale)

| Factor | Weight | Scoring |
|--------|--------|---------|
| Price value | 12% | Under $400k = 12pts, $400-500k = 10pts, $500-600k = 7pts, $600-700k = 5pts |
| Room count / size | 8% | 4+ rooms = 8pts, 3 rooms = 6pts, 2 rooms = 4pts |
| Square footage | 8% | Over 1,500 sqft = 8pts, 1,000-1,500 = 6pts, 700-1,000 = 4pts, under 700 = 2pts |
| Location quality | 8% | Walkable commercial corridor = 8pts, inner neighborhood = 6pts, outer neighborhood = 4pts |
| Mixed-use potential | 10% | Already mixed-use/commercial = 10pts, duplex/multi-family = 8pts, house with separate entrance = 5pts, standard house = 3pts |
| Fiber internet | 10% | Fiber confirmed = 10pts, gigabit cable = 5pts, cable only = 3pts, no data = 0pts |
| Property condition | 5% | Move-in ready / recently renovated = 5pts, good condition = 4pts, needs work = 2pts, major renovation needed = 1pt |
| Food proximity (indie) | 11% | Near indie food corridor = 11pts, mixed indie/chain = 7pts, mostly chains = 4pts, chain-heavy/no food = 2pts |
| Main street location | 10% | On a main street = 10pts, 1-2 blocks away = 8pts, 3-5 blocks = 5pts, not near = 2pts |
| Hipness score | 9% | See `hipness-scoring` skill. Score mapped: 85+ = 9pts, 70-84 = 7pts, 55-69 = 5pts, 40-54 = 3pts, below 40 = 1pt |
| Safety score | 9% | See `safety-scoring` skill. Score mapped: 80+ = 9pts, 65-79 = 7pts, 50-64 = 5pts, 35-49 = 3pts, below 35 = 1pt |

## Food Proximity

Prioritize properties near **well-rated, independently owned** restaurants and cafes. Chain restaurants detract from the score.

**Indie food corridors** (score highest):
- SE Hawthorne Blvd, SE Division St, SE Belmont St, SE Clinton St
- NE/N Alberta St, N Mississippi Ave, NE/N Williams Ave
- NW 23rd Ave, NW 21st Ave
- SE Foster Rd (Foster-Powell section), SE Woodstock Blvd
- SE 13th Ave (Sellwood), SE Milwaukie Ave

**Chain-heavy corridors** (score lowest):
- SE 82nd Ave, outer SE Powell Blvd (east of 52nd), outer NE Sandy Blvd (east of Hollywood)

## Main Streets

Properties on or near these streets score higher:

- SE Hawthorne Blvd, SE Division St, SE Belmont St, SE Powell Blvd
- SE Clinton St, SE Foster Rd, SE Woodstock Blvd, SE Milwaukie Ave
- NE/SE Broadway, NE/SE Sandy Blvd, NE/SE MLK Jr Blvd, SE 12th Ave
- W/E Burnside St, NW 23rd Ave, NW 21st Ave, SW Macadam Ave
- NE/N Alberta St, N Mississippi Ave, NE/N Williams Ave

## Property Type Classification

- **Single-family house**: Standard house, may have basement/garage convertible to office
- **Duplex/triplex/fourplex**: Multi-unit, live in one + use another as office, or rent out units
- **Mixed-use building**: Already zoned commercial + residential. Ideal for live/work.
- **Commercial building**: Office/retail space, may require residential conversion permits
- **Condo/townhouse**: Check HOA rules for commercial use before scoring high on mixed-use

## Mixed-Use Keywords

Scan descriptions for:
- "mixed use", "live/work", "home office", "commercial"
- "zoned commercial", "retail below", "storefront"
- "duplex", "triplex", "fourplex", "multi-family"
- "separate entrance", "ADU", "accessory dwelling"
- "basement office", "ground floor commercial"
- "income property", "investment"

## Key Locations for Distance Calculation

Key locations are configured in `data/config.json` under `key_locations`. The report dynamically reads from this config. Default locations: Chris, George, Jasmine (see config for addresses).

## Disqualifiers (Auto-Reject)

- Price over $700,000
- Located outside Portland city limits
- Land-only (no structure)
- Tear-down / condemned
- HOA that prohibits any business use (for condos)

## Score Interpretation

- **80-100**: Excellent match — prioritize
- **60-79**: Good match — include in report
- **40-59**: Marginal — include if few better options
- **Below 40**: Poor match — exclude
