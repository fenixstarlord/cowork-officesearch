---
name: hipness-scoring
description: "Use this skill to evaluate and score the cultural hipness/vibrancy of a listing's area. Combines a neighborhood baseline score with live data from Google Maps Places API, Walk Score, and web/Reddit buzz searches."
---

## Overview

The hipness score measures the cultural vibrancy, indie character, and "cool factor" of a listing's surrounding area. It uses a **hybrid approach**: a static neighborhood baseline adjusted by live data lookups.

**Final hipness score: 0-100 scale**, integrated into the listing evaluation as a weighted factor.

## Scoring Components

### 1. Neighborhood Baseline (25%)

A pre-assigned score for each Portland neighborhood based on known cultural character. See the **Neighborhood Hipness Baselines** table in the `portland-geography` skill.

| Score Range | Meaning |
|-------------|---------|
| 90-100 | Cultural epicenter — nationally recognized hip district |
| 75-89 | Very hip — strong indie identity, active creative scene |
| 60-74 | Hip-adjacent — solid character, some indie anchors |
| 40-59 | Neutral — residential-focused, limited cultural draw |
| Below 40 | Low hipness — suburban feel, chain-dominated |

### 2. Indie Business Density (25%)

Use **Google Maps Places API** (key in `data/.env`) to count indie-character businesses within a **0.5-mile radius** of the listing address.

**Categories to search** (use Places API `nearbySearch` with these types/keywords):

| Category | Search Keywords | High Score Threshold |
|----------|----------------|---------------------|
| Coffee & cafes | `coffee shop`, `cafe`, `espresso` | 5+ = max points |
| Breweries & taprooms | `brewery`, `taproom`, `cidery` | 3+ = max points |
| Restaurants (indie) | `restaurant` (exclude chains) | 8+ = max points |
| Bars & cocktail | `cocktail bar`, `wine bar`, `dive bar` | 3+ = max points |
| Creative retail | `bookstore`, `record store`, `vintage`, `thrift`, `antique` | 3+ = max points |
| Bike shops | `bike shop`, `bicycle` | 1+ = max points |
| Art & culture | `art gallery`, `tattoo`, `maker space` | 2+ = max points |

**Chain filtering**: Exclude results matching known chains (Starbucks, Dutch Bros, Subway, McDonald's, Chipotle, Taco Bell, Panda Express, Buffalo Wild Wings, Applebee's, Chili's, IHOP, Denny's, Pizza Hut, Domino's, Papa John's). Count only non-chain results.

**Scoring**:
- Count total qualifying indie businesses across all categories
- 20+ businesses = 25pts (max)
- 15-19 = 20pts
- 10-14 = 15pts
- 5-9 = 10pts
- 1-4 = 5pts
- 0 = 0pts

### 3. Walkability & Bikeability (15%)

Look up **Walk Score** and **Bike Score** for the listing address.

**Method**: Use browser tools to navigate to `walkscore.com` and search the address. Extract Walk Score and Bike Score values.

**Scoring**:
- Walk Score 90+ AND Bike Score 90+ = 15pts
- Walk Score 80+ AND Bike Score 70+ = 12pts
- Walk Score 70+ OR Bike Score 80+ = 9pts
- Walk Score 50-69 = 6pts
- Walk Score below 50 = 3pts

### 4. Cultural Venues Proximity (15%)

Use **Google Maps Places API** to find cultural venues within **1 mile** of the listing.

**Venue types to search**:

| Venue Type | Keywords |
|-----------|----------|
| Live music | `live music venue`, `concert hall`, `music club` |
| Theaters | `theater`, `performing arts`, `comedy club`, `improv` |
| Galleries | `art gallery`, `gallery` |
| Community spaces | `community center`, `co-op`, `food co-op`, `maker space`, `hackerspace` |
| Independent cinema | `independent cinema`, `arthouse cinema` |
| Farmers markets | `farmers market` |

**Scoring**:
- 8+ venues = 15pts (max)
- 5-7 venues = 12pts
- 3-4 venues = 9pts
- 1-2 venues = 5pts
- 0 = 0pts

### 5. Online Buzz — Web & Reddit Search (20%)

Use the **WebSearch** tool to find recent online discussion about the neighborhood's hipness, cultural activity, and desirability.

#### Search Queries

For each listing, run **3 searches** using the neighborhood name and/or nearby corridor:

1. **Reddit buzz**: `site:reddit.com Portland [neighborhood] hip OR cool OR best OR vibe OR trendy`
2. **General press**: `Portland [neighborhood] "best neighborhood" OR "up and coming" OR "hidden gem" OR "coolest" OR "hottest"`
3. **Events & culture**: `Portland [neighborhood] new restaurant OR new bar OR new brewery OR pop-up OR street fair OR art walk 2025 2026`

#### Evaluation Criteria

Read the top 5-10 results from each search and assess:

| Signal | Points | Examples |
|--------|--------|---------|
| **Strong positive buzz** | 18-20 | Multiple recent articles/threads calling it hip, trendy, or a "must-visit"; featured in "best neighborhoods" lists |
| **Moderate positive buzz** | 13-17 | Some positive mentions, a few new openings, occasional Reddit praise |
| **Neutral / mixed** | 7-12 | Mentioned but not especially praised; some positive, some negative threads |
| **Low / negative buzz** | 3-6 | Rarely mentioned; threads focus on crime, decline, or boring character |
| **No buzz** | 0-2 | Essentially no online discussion about the area's culture or character |

#### What Counts as "Hip" Signals

**Positive signals** (increase score):
- New indie businesses opening (especially coffee, restaurants, breweries, galleries)
- "Best neighborhood" or "coolest neighborhood" mentions in media (Eater, Portland Mercury, Willamette Week, OregonLive, Thrillist, TimeOut)
- Reddit threads recommending the area for food, nightlife, or culture
- Street fairs, art walks, First Friday events, farmers markets
- Mentions of creative community, artists, musicians living in the area
- Food cart pods nearby
- References to the area being "walkable", "bikeable", or having "great vibes"

**Negative signals** (decrease score):
- "Avoid this area" or safety concerns dominating discussion
- References to gentrification pushing out the culture that made it hip
- "Dead" or "boring" characterizations
- Mostly chain/corporate development displacing indie businesses
- Threads about the area declining or losing character

#### Recording Buzz Findings

For each listing, record:
```json
{
  "hipness_buzz": {
    "search_date": "YYYY-MM-DD",
    "reddit_highlights": ["summary of notable Reddit mentions"],
    "press_highlights": ["summary of notable press/blog mentions"],
    "new_openings": ["any recently opened hip businesses nearby"],
    "events_nearby": ["recurring cultural events in the area"],
    "buzz_score": 0-20,
    "buzz_summary": "1-2 sentence summary of the area's online reputation"
  }
}
```

## Composite Score Calculation

```
hipness_score = (neighborhood_baseline * 0.25)
              + (indie_business_density * 0.25)
              + (walkability_bikeability * 0.15)
              + (cultural_venues * 0.15)
              + (online_buzz * 0.20)
```

All component scores are on their own 0-max scale (see above), then weighted.

**Final score is 0-100.**

## Integration with Listing Data

Add the following fields to each listing object (rental or purchase):

```json
{
  "hipness_score": 78,
  "hipness_breakdown": {
    "neighborhood_baseline": 85,
    "indie_business_density": 20,
    "walkability_bikeability": 12,
    "cultural_venues": 12,
    "online_buzz": 17
  },
  "hipness_buzz": {
    "search_date": "2026-03-29",
    "reddit_highlights": [],
    "press_highlights": [],
    "new_openings": [],
    "events_nearby": [],
    "buzz_score": 17,
    "buzz_summary": ""
  },
  "hipness_tier": "Very Hip"
}
```

### Hipness Tier Labels

| Score | Tier |
|-------|------|
| 85-100 | Cultural Epicenter |
| 70-84 | Very Hip |
| 55-69 | Hip-Adjacent |
| 40-54 | Neutral |
| Below 40 | Low Hipness |

## Execution Order

1. Look up neighborhood baseline from `portland-geography` skill
2. Run Google Maps Places API searches for indie businesses and cultural venues (can be parallelized)
3. Look up Walk Score / Bike Score via browser
4. Run 3 web searches for online buzz (can be parallelized)
5. Read and evaluate web search results
6. Calculate composite score
7. Attach to listing object

Steps 2, 3, and 4 can run in parallel. Step 5 depends on step 4. Steps 6-7 depend on all prior steps.

## Report Display

In the HTML report, display the hipness score as:
- A colored badge next to the listing score (green for 70+, yellow for 40-69, gray for below 40)
- A expandable section showing the breakdown and buzz highlights
- Notable "hip finds" (new openings, events, Reddit praise) as bullet points
