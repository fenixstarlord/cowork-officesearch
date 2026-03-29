---
description: Watch for new listings matching saved criteria — re-runs Stage 1, diffs against previous results, and surfaces only new or price-changed listings
argument-hint: "[rental|purchase] [--interval daily|weekly]"
allowed-tools: mcp__Claude_in_Chrome__navigate, mcp__Claude_in_Chrome__find, mcp__Claude_in_Chrome__read_page, mcp__Claude_in_Chrome__computer, mcp__Claude_in_Chrome__form_input, mcp__Claude_in_Chrome__get_page_text, mcp__Claude_in_Chrome__javascript_tool, mcp__Claude_in_Chrome__tabs_context_mcp, mcp__Claude_in_Chrome__tabs_create_mcp, Read, Write, Bash, Glob
---

# /watch

Monitor listing sites for new or changed listings since the last search.

## Inputs
- `type` (required): `rental` or `purchase`
- `--interval` (optional): `daily` or `weekly`. Default: manual (run on demand)

## Prerequisites
- A previous search must have been run (`data/output/listings.json` or `data/output/purchase-listings.json` must exist)
- Previous search criteria are read from `data/output/search-criteria.json` (saved automatically by search-listings commands)

## Workflow

### 1. Load Previous State

1. Read the appropriate listings file (`listings.json` for rental, `purchase-listings.json` for purchase)
2. Read `data/output/search-criteria.json` for saved search parameters
3. Copy current listings to `data/output/listings-previous.json` (or `purchase-listings-previous.json`) as backup
4. Read `data/output/reviewed.json` if it exists (for favorites/history tracking)

### 2. Re-Run Search

1. Execute the same search as Stage 1, using saved criteria from `search-criteria.json`
2. Apply the same site list, filters, and geographic scope
3. Run deduplication (see `deduplication` skill)
4. Save new results to the listings JSON file

### 3. Diff Previous vs Current

Compare previous and current listing sets:

**New listings**: Present in current but not in previous (by normalized address)
```json
{
  "status": "new",
  "listing": { ... }
}
```

**Removed listings**: Present in previous but not in current (likely taken off market)
```json
{
  "status": "removed",
  "listing": { ... }
}
```

**Price changed**: Same address, different price
```json
{
  "status": "price_changed",
  "listing": { ... },
  "previous_price": 1850,
  "new_price": 1750,
  "change_pct": -5.4
}
```

**Still available**: Present in both, unchanged
```json
{
  "status": "unchanged"
}
```

### 4. Generate Diff Report

Save the diff to `data/output/watch-diff-YYYYMMDD-HHMM.json`:

```json
{
  "type": "rental",
  "watch_date": "2026-03-29T14:30:00",
  "previous_date": "2026-03-22T10:00:00",
  "summary": {
    "new_listings": 3,
    "removed_listings": 2,
    "price_changes": 1,
    "unchanged": 15
  },
  "new": [ ... ],
  "removed": [ ... ],
  "price_changed": [ ... ]
}
```

### 5. Report to User

Display a summary:
```
Watch results (rental) — 2026-03-29:
  ✦ 3 new listings found
  ↓ 1 price drop: 1234 SE Division St ($1,850 → $1,750, -5.4%)
  ✕ 2 listings removed (likely rented)
  — 15 listings unchanged

New listings:
  1. 5678 SE Hawthorne Blvd — $1,600/mo, 2bd/1ba, 850 sqft (zillow)
  2. 910 NE Alberta St — $2,100/mo, 3bd/1ba, 1100 sqft (apartments.com)
  3. 222 SE Belmont St — $1,900/mo, 2bd/1ba, 780 sqft (craigslist)

Would you like me to:
  a) Run internet checks on the new listings?
  b) Generate an updated report?
  c) Add these to your favorites for review?
```

### 6. Mark New Listings

New listings are flagged with `"is_new": true` in the listings JSON so the report can display a "NEW" badge.

## Search Criteria Persistence

The search-listings commands automatically save criteria to `data/output/search-criteria.json`:

```json
{
  "type": "rental",
  "saved_at": "2026-03-22T10:00:00",
  "criteria": {
    "bedrooms": 2,
    "min_sqft": 700,
    "max_price": 2500,
    "mixed_use": "preferred",
    "neighborhoods": ["all"],
    "sites_searched": ["zillow", "craigslist", "apartments.com", "redfin", "hotpads"]
  }
}
```

## Scheduling

If `--interval` is specified:
- `daily`: Remind the user to run `/watch rental` each day (or use the `/schedule` skill to automate)
- `weekly`: Same, but weekly

The watch command itself is always on-demand. Scheduling integration is handled separately via the `schedule` skill if the user wants true automation.
