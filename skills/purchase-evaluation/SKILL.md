---
name: purchase-evaluation
description: "Use this skill to evaluate and score properties for sale against purchase criteria: under $700k, suitable for live/work use, central Portland location, fiber internet availability."
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
| Price value | 20% | Under $400k = 20pts, $400-500k = 16pts, $500-600k = 12pts, $600-700k = 8pts |
| Room count / size | 15% | 4+ rooms = 15pts, 3 rooms = 12pts, 2 rooms = 8pts |
| Square footage | 15% | Over 1,500 sqft = 15pts, 1,000-1,500 = 12pts, 700-1,000 = 8pts, under 700 = 4pts |
| Location quality | 15% | Walkable commercial corridor = 15pts, inner neighborhood = 12pts, outer neighborhood = 8pts |
| Mixed-use potential | 15% | Already mixed-use/commercial = 15pts, duplex/multi-family = 12pts, house with separate entrance = 8pts, standard house = 4pts |
| Fiber internet | 10% | Fiber confirmed = 10pts, gigabit cable = 5pts, cable only = 3pts, no data = 0pts |
| Property condition | 10% | Move-in ready / recently renovated = 10pts, good condition = 7pts, needs work = 4pts, major renovation needed = 2pts |

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
