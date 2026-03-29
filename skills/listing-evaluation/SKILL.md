---
name: listing-evaluation
description: "Use this skill to evaluate and score rental listings. Mandatory: kitchen/kitchenette and fiber internet. Scoring based on room count, kitchen quality, price, square footage, mixed-use friendliness, fiber quality, and proximity to key people."
---

## Mandatory Requirements (Must-Have)

A listing MUST meet ALL of these to be included:

- Minimum bedroom count specified by user (default: 2+)
- At least 1 bathroom
- Kitchen or kitchenette (scan for: "kitchen", "kitchenette", "galley kitchen", "cooking area", "stove", "oven", "range", "refrigerator", "microwave")
- Fiber internet available at the address (checked in Stage 2 — if no fiber, downgrade significantly)
- Location within the target area (see `portland-geography` skill)

## Scoring Rubric (0-100 scale)

| Factor | Weight | Scoring |
|--------|--------|---------|
| Room count | 20% | Meets minimum = 15pts, exceeds by 1+ = 20pts |
| Kitchen quality | 15% | Full kitchen = 15pts, kitchenette = 10pts, unclear = 5pts |
| Price reasonableness | 20% | Under $1,800 = 20pts, $1,800-2,200 = 16pts, $2,200-2,800 = 10pts, $2,800-3,500 = 6pts, over $3,500 = 3pts |
| Square footage | 15% | Over 900 sqft = 15pts, 700-900 = 11pts, 500-700 = 7pts, under 500 = 3pts |
| Mixed-use friendliness | 15% | Explicit "live/work" or "home office" = 15pts, ground floor commercial = 11pts, "flex space" / townhouse = 7pts, no mention = 3pts |
| Fiber internet quality | 15% | Fiber 8Gbps = 15pts, Fiber 940Mbps = 12pts, gigabit cable only = 5pts, cable only = 3pts, no data = 0pts |

## Key Locations for Distance Calculation

Each listing should show distance from these three locations:

| Name | Address |
|------|---------|
| **Chris** | 10363 SE 24th Ave, Portland, OR |
| **George** | 3816 SW Lee St, Portland, OR 97221 |
| **Jasmine** | 3521 SE Main St, Portland, OR 97214 |

Distances are calculated as straight-line (or driving if available) and displayed in the report for each listing.

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
