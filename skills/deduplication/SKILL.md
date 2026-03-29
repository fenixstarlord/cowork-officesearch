---
name: deduplication
description: "Use this skill to detect and merge duplicate listings that appear across multiple listing sites. Normalizes addresses and compares key fields to identify the same property listed on Zillow, Redfin, Craigslist, etc."
user-invocable: false
---

## Overview

The same property frequently appears on multiple listing sites (Zillow, Redfin, Craigslist, Apartments.com, etc.). This skill detects duplicates and merges them into a single canonical listing, preserving the best data from each source.

## When to Run

Deduplication runs automatically at the end of Stage 1 (search-listings), after all sites have been scraped and before writing the final JSON output.

## Address Normalization

Before comparing, normalize each address string:

1. **Lowercase** the entire string
2. **Expand abbreviations**: `se` → `southeast`, `sw` → `southwest`, `ne` → `northeast`, `nw` → `northwest`, `st` → `street`, `blvd` → `boulevard`, `ave` → `avenue`, `dr` → `drive`, `rd` → `road`, `ct` → `court`, `ln` → `lane`, `pl` → `place`, `apt` → `apartment`, `ste` → `suite`
3. **Strip unit/apartment suffixes** for comparison: remove `#101`, `apt 2`, `unit b`, etc. (but preserve in data)
4. **Remove punctuation**: periods, commas, hashes
5. **Collapse whitespace**: multiple spaces → single space
6. **Strip zip code** for comparison (neighborhoods may differ by source)

Example: `"1234 SE Powell Blvd #2, Portland, OR 97202"` → `"1234 southeast powell boulevard portland"`

## Duplicate Detection

Two listings are considered duplicates if they match on **any** of these criteria:

### Primary Match (high confidence)
- **Normalized address match**: Identical after normalization
- **Address + price match**: Same street number + street name AND price within 5% of each other

### Secondary Match (medium confidence — confirm with additional fields)
- **Street number + street name match** with different units → may be same building, different units → keep both unless price is identical
- **Same price + same bed/bath count + same sqft** in the same neighborhood → likely duplicate even if address text differs slightly

## Merge Strategy

When duplicates are found, merge into a single listing:

1. **Keep the listing with more complete data** as the base (most fields populated)
2. **Prefer data sources in this order**: Zillow > Redfin > Realtor.com > Apartments.com > HotPads > Craigslist > LoopNet > CommercialCafe
3. **Merge fields**:
   - `address`: Use the most complete/formal version
   - `price`: Use the most recently updated (prefer Zillow/Redfin over Craigslist)
   - `sqft`: Use the value from the most reliable source
   - `amenities`: Union of all amenities from all sources
   - `description_excerpt`: Keep the longest/most detailed
   - `photo_paths`: Union of all photos (up to max limit)
   - `has_kitchen` / `has_kitchenette`: If any source confirms kitchen, set to true
4. **Track all source URLs**:
   ```json
   {
     "id": "zillow-12345",
     "source": "zillow",
     "url": "https://zillow.com/...",
     "also_listed_on": [
       {"source": "craigslist", "url": "https://portland.craigslist.org/...", "price": 1850},
       {"source": "redfin", "url": "https://redfin.com/...", "price": 1850}
     ]
   }
   ```

## Deduplication Report

After merging, output a summary:
```
Deduplication complete:
- Total raw listings: 28
- Duplicates found: 6 (3 pairs)
- Final unique listings: 22
- Merged pairs:
  - "1234 SE Powell Blvd" (zillow + craigslist + redfin)
  - "5678 SE Hawthorne Blvd" (apartments.com + hotpads)
  - "910 NW 23rd Ave" (loopnet + commercialcafe)
```

## Edge Cases

- **Different units at same address**: Same building but different unit numbers → keep as separate listings
- **Price discrepancies > 10%**: May be different listings or outdated data → flag for manual review, keep both
- **One listing has internet data, other doesn't**: Preserve the internet data in merged result
- **Conflicting data** (e.g., different bed counts): Flag the discrepancy in a `data_conflicts` field
