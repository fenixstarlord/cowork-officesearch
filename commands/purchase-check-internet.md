---
description: Check fiber internet availability for all properties in data/output/purchase-listings.json
allowed-tools: mcp__Claude_in_Chrome__navigate, mcp__Claude_in_Chrome__find, mcp__Claude_in_Chrome__read_page, mcp__Claude_in_Chrome__computer, mcp__Claude_in_Chrome__form_input, mcp__Claude_in_Chrome__get_page_text, mcp__Claude_in_Chrome__tabs_context_mcp
---

# /purchase:check-internet

Check fiber and broadband internet availability at the address of each property found in Stage 1.

## Prerequisites
- `data/output/purchase-listings.json` must exist (run `/purchase:search-listings` first)

## Inputs
None — reads addresses from `data/output/purchase-listings.json`

## Workflow

1. Read `data/output/purchase-listings.json`. If missing, tell user: "No listings found. Please run `/purchase:search-listings` first."
2. Load the `fiber-internet-check` skill for ISP checker URLs and navigation procedures
3. Filter to listings where `internet` is null (allows re-running to pick up where it left off)
4. Open a Chrome tab if not already available

5. **Determine checking mode** based on listing count:
   - 5 or fewer listings: Sequential (single tab)
   - 6-15 listings: Parallel with 2 tabs
   - 16+ listings: Parallel with 3 tabs

6. **For each listing address** (use BroadbandNow as primary — one lookup per address gets all providers):
   a. **BroadbandNow** (PRIMARY): Use the Google Places autocomplete pattern from `fiber-internet-check` skill
   b. **Parallel mode**: When using multiple tabs, rotate between them during wait periods (see `internet-checker` agent Parallel Checking section)
   c. **Direct ISP sites** (FALLBACK ONLY): If BroadbandNow fails
   d. Build the internet JSON object — **no ISP screenshots needed**, text data only
   e. Classify internet suitability (Excellent/Good/Adequate/Poor)
   f. Update the listing's `internet` field
   g. If rate-limited during parallel mode, fall back to sequential with 5-second delays

7. Write enriched data back to `data/output/purchase-listings.json`
8. Report summary: "Checked X addresses. Fiber available at Y. Cable-only at Z. Failed checks: W."

## Expected Output
- `data/output/purchase-listings.json` updated with internet data
- Chat summary with fiber availability counts

## Re-Runnability
Only processes listings where `internet` is null. Re-running picks up where it left off.

## Delegation
Spawns the `internet-checker` agent for the browser automation work.
