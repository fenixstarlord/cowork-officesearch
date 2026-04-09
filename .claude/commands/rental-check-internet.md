---
description: Check fiber internet availability for all listings in data/output/listings.json
allowed-tools: mcp__Claude_in_Chrome__navigate, mcp__Claude_in_Chrome__find, mcp__Claude_in_Chrome__read_page, mcp__Claude_in_Chrome__computer, mcp__Claude_in_Chrome__form_input, mcp__Claude_in_Chrome__get_page_text, mcp__Claude_in_Chrome__tabs_context_mcp
---

# /rental-check-internet

Check fiber and broadband internet availability at the address of each listing found in Stage 1.

## Prerequisites
- `data/output/listings.json` must exist (run `/rental-search-listings` first)

## Inputs
None — reads addresses from `data/output/listings.json`

## Workflow

1. Read `data/output/listings.json`. If missing, tell user: "No listings found. Please run `/rental-search-listings` first."
2. Load the `fiber-internet-check` skill for ISP checker URLs and navigation procedures
3. Filter to listings where `internet` is null (allows re-running to pick up where it left off)
4. Open a Chrome tab if not already available

5. **Determine checking mode** based on listing count:
   - 5 or fewer listings: Sequential (single tab)
   - 6-15 listings: Parallel with 2 tabs
   - 16+ listings: Parallel with 3 tabs

6. **For each listing address** (use BroadbandNow as primary — one lookup per address gets all providers):
   a. **BroadbandNow** (PRIMARY): Use the Google Places autocomplete pattern from `fiber-internet-check` skill:
      - Type short address (number + street + city) into search input
      - Wait for autocomplete dropdown, click the matching suggestion
      - Extract all providers, speeds, connection types from results page
      - For subsequent addresses, use the "refine search" box on the results page
   b. **Parallel mode**: When using multiple tabs, rotate between them during wait periods (see `internet-checker` agent Parallel Checking section)
   c. **Direct ISP sites** (FALLBACK ONLY): If BroadbandNow fails or data seems incomplete, check CenturyLink/Xfinity directly
   d. Build the internet JSON object per the schema in `search-resources` skill — **no ISP screenshots needed**, text data only
   e. Classify internet suitability (Excellent/Good/Adequate/Poor) per `fiber-internet-check` skill
   f. Update the listing's `internet` field
   g. If rate-limited during parallel mode, fall back to sequential with 5-second delays

7. Write enriched data back to `data/output/listings.json`
8. Report summary: "Checked X addresses. Fiber available at Y. Cable-only at Z. Failed checks: W."

## Expected Output
- `data/output/listings.json` updated with internet data for each listing
- Chat summary with fiber availability counts
- No ISP screenshots — internet data is text-only

## CAPTCHA Handling
If any ISP checker shows a CAPTCHA:
1. Take a screenshot
2. Ask user to solve it in the browser
3. Wait for confirmation
4. Resume checking

If an address fails all providers, mark internet as:
```json
{ "internet": { "status": "check_failed", "note": "All provider checks failed for this address" } }
```

## Re-Runnability
This command only processes listings where `internet` is null. If it's interrupted, re-running picks up where it left off.

## Delegation
Spawns the `internet-checker` agent for the browser automation work.
