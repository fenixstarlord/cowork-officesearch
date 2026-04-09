---
name: safety-scoring
description: "Use this skill to evaluate neighborhood safety and noise levels for a listing address. Uses Portland's public data sources and web search for crime reports, noise complaints, and livability factors."
---

## Overview

The safety score measures the safety and noise environment around a listing address. It combines publicly available Portland data with web search results to produce a 0-100 score integrated into listing evaluation.

## Data Sources

### 1. Portland Police Bureau Crime Data (Primary)

**Source**: PortlandMaps / Portland Police Open Data
- URL: `https://www.portlandmaps.com/` — search by address, check "Crime" layer
- URL: `https://www.portland.gov/police/open-data` — downloadable datasets

**What to extract**:
- Crime incidents within 0.25 miles of the address in the last 12 months
- Crime types: property crime (theft, burglary, vandalism), violent crime (assault, robbery), other
- Trend: increasing, stable, or decreasing vs. prior year

**Browser lookup procedure**:
1. Navigate to `https://www.portlandmaps.com/`
2. Enter the listing address in the search bar
3. Click the "Crime" or "Safety" tab/layer
4. Use `get_page_text` to extract crime summary statistics
5. Note the count and types of incidents

### 2. Portland Noise Complaints

**Source**: Portland 311 data / PortlandMaps
- Noise complaints near the address (construction, nightlife, traffic, industrial)
- Proximity to known noise sources: bars/clubs, major arterials (Powell, Sandy, MLK, 82nd), freeway (I-84, I-5, I-405), rail lines

**Known high-noise corridors**:
- SE Powell Blvd — heavy truck traffic
- NE/SE Sandy Blvd — arterial traffic
- SE 82nd Ave — arterial traffic
- I-84 corridor (Sullivan's Gulch) — freeway noise
- I-5 corridor (east bank) — freeway noise
- I-405 corridor (Goose Hollow, NW) — freeway noise
- MAX light rail — periodic train noise near stations
- NE/N Mississippi Ave, NE/N Alberta St — nightlife noise on weekends

### 3. Web Search for Safety Reports

Use **WebSearch** to find recent safety discussions:

**Search queries**:
1. `Portland [neighborhood] safety crime 2025 2026`
2. `site:reddit.com Portland [neighborhood] safe OR dangerous OR sketchy`
3. `Portland [neighborhood] livability noise complaints`

**Evaluate top results for**:
- Recent crime trend articles (OregonLive, Portland Mercury, KOIN, KGW)
- Reddit threads about safety in the neighborhood
- Noise complaints or quality-of-life discussions

## Scoring Rubric (0-100)

### Safety Component (60% of total)

| Crime Level | Points (out of 60) |
|------------|-------------------|
| Very low crime (< 5 incidents/year within 0.25mi) | 55-60 |
| Low crime (5-15 incidents/year) | 45-54 |
| Moderate crime (15-30 incidents/year) | 30-44 |
| High crime (30-50 incidents/year) | 15-29 |
| Very high crime (50+ incidents/year) | 0-14 |

**Adjustments**:
- Violent crime incidents: -5 pts per incident (vs property crime)
- Crime trending down: +5 pts
- Crime trending up: -5 pts

### Noise Component (25% of total)

| Noise Level | Points (out of 25) |
|------------|-------------------|
| Quiet residential, no major roads | 22-25 |
| Residential with minor street noise | 17-21 |
| Near commercial corridor (some noise) | 12-16 |
| On major arterial or near nightlife | 6-11 |
| Near freeway, industrial, or multiple noise sources | 0-5 |

### Online Reputation Component (15% of total)

| Reputation | Points (out of 15) |
|-----------|-------------------|
| Consistently described as safe, quiet, family-friendly | 13-15 |
| Generally positive, occasional minor concerns | 9-12 |
| Mixed reviews — some safety concerns noted | 5-8 |
| Frequently flagged as unsafe or noisy | 2-4 |
| Widely regarded as dangerous or very noisy | 0-1 |

## Composite Calculation

```
safety_score = safety_component + noise_component + reputation_component
```

Total: 0-100

## Integration with Listing Data

Add to each listing object:

```json
{
  "safety_score": 72,
  "safety_breakdown": {
    "crime_score": 45,
    "noise_score": 18,
    "reputation_score": 9
  },
  "safety_details": {
    "crime_incidents_nearby": 12,
    "crime_trend": "stable",
    "noise_sources": ["SE Division St commercial traffic"],
    "safety_notes": "Low property crime, no violent incidents in 12 months. Light commercial noise from Division St during business hours."
  },
  "safety_tier": "Safe"
}
```

### Safety Tier Labels

| Score | Tier |
|-------|------|
| 80-100 | Very Safe & Quiet |
| 65-79 | Safe |
| 50-64 | Moderate |
| 35-49 | Some Concerns |
| Below 35 | Significant Concerns |

## Neighborhood Baseline Safety Notes

These are general starting points — always verify with live data:

| Neighborhood | Baseline Safety | Notes |
|-------------|----------------|-------|
| Ladd's Addition | High | Quiet residential, low crime, unique street grid |
| Laurelhurst | High | Residential, parks, low crime |
| Eastmoreland | High | Quiet residential, very low crime |
| Irvington | High | Historic residential, generally safe |
| Hawthorne / Belmont | Moderate-High | Commercial corridor activity, low violent crime |
| Richmond | Moderate-High | Residential, generally safe, some property crime |
| Buckman | Moderate | Urban density, some property crime, nightlife noise |
| Sellwood-Moreland | High | Family-oriented, low crime |
| Pearl District | Moderate | Urban, some property crime, generally safe |
| Old Town / Chinatown | Low | Higher crime rates, safety concerns well-documented |
| Downtown | Low-Moderate | Property crime, some safety concerns, improving |
| Hosford-Abernethy | Moderate | Varies by block, Division is busier |

## Notion Display

In the Notion database, safety data is stored as:
- **Safety** property: numeric score (0-100)
- **Safety Tier** property: select value (Very Safe & Quiet, Safe, Moderate, Some Concerns, Significant)
- **Safety Notes** property: brief safety notes, crime trend, and noise sources
