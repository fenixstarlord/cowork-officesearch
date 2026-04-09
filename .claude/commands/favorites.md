---
description: Manage favorites and review history — mark listings as favorite, rejected, or reviewed
argument-hint: "[add|remove|list|clear] [listing-id] [--status favorite|rejected|reviewed]"
allowed-tools: Read, Write, Bash
---

# /favorites

Track which listings have been reviewed, favorited, or rejected. Future reports mark listings accordingly.

## Inputs
- `action` (required): `add`, `remove`, `list`, or `clear`
- `listing-id` (required for add/remove): The listing ID (e.g., `zillow-12345`)
- `--status` (optional for add): `favorite` (default), `rejected`, or `reviewed`

## Data File

All tracking data is stored in `data/output/reviewed.json`:

```json
{
  "last_updated": "2026-03-29T14:30:00",
  "listings": {
    "zillow-12345": {
      "status": "favorite",
      "added_at": "2026-03-29T14:30:00",
      "notes": "Great location, check in person",
      "address": "1234 SE Hawthorne Blvd"
    },
    "craigslist-67890": {
      "status": "rejected",
      "added_at": "2026-03-28T10:00:00",
      "notes": "Too small, no kitchen",
      "address": "5678 SE Powell Blvd"
    },
    "redfin-11111": {
      "status": "reviewed",
      "added_at": "2026-03-27T09:00:00",
      "notes": "",
      "address": "910 NE Alberta St"
    }
  }
}
```

## Actions

### `add`

```
/favorites add zillow-12345 --status favorite
```

1. Read `data/output/reviewed.json` (create if doesn't exist)
2. Look up the listing in `listings.json` or `purchase-listings.json` to get the address
3. Add or update the entry with status, timestamp, and address
4. Ask for optional notes: "Any notes for this listing? (press Enter to skip)"
5. Write back to `reviewed.json`
6. Confirm: "Added zillow-12345 (1234 SE Hawthorne Blvd) as favorite."

### `remove`

```
/favorites remove zillow-12345
```

1. Read `reviewed.json`
2. Remove the entry
3. Write back
4. Confirm: "Removed zillow-12345 from tracked listings."

### `list`

```
/favorites list
/favorites list --status favorite
```

1. Read `reviewed.json`
2. Display a formatted table:

```
Tracked Listings (5 total):

⭐ Favorites (2):
  1. zillow-12345 — 1234 SE Hawthorne Blvd — "Great location, check in person"
  2. redfin-22222 — 555 SE Division St — "Good price, needs internet check"

✕ Rejected (2):
  3. craigslist-67890 — 5678 SE Powell Blvd — "Too small, no kitchen"
  4. hotpads-33333 — 777 NE Sandy Blvd — "No fiber available"

✓ Reviewed (1):
  5. redfin-11111 — 910 NE Alberta St
```

### `clear`

```
/favorites clear
/favorites clear --status rejected
```

1. Clear all entries (or just entries matching `--status`)
2. Confirm with user before clearing: "Clear all tracked listings? (y/n)"
3. Write back

## Report Integration

When generating reports (`/rent` or `/purchase`):

1. Read `reviewed.json` if it exists
2. For each listing in the report:
   - If `favorite`: Show a ⭐ badge next to the listing name
   - If `rejected`: Either hide from report or show with a ~~strikethrough~~ style and gray background
   - If `reviewed`: Show a ✓ badge
   - If not in `reviewed.json` and `is_new` is true: Show a "NEW" badge
3. Add a "Favorites Summary" section at the top of the report listing all favorited listings

## Watch Integration

When `/watch` finds new listings:
- New listings that aren't in `reviewed.json` are flagged as truly new
- Previously rejected listings that reappear (e.g., relisted) are noted but stay rejected unless the user re-adds them
- Price changes on favorited listings are highlighted prominently
