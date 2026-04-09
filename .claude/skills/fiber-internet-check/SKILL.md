---
name: fiber-internet-check
description: "Use this skill when checking fiber or broadband internet availability at a specific Portland address. BroadbandNow is the primary checker (aggregates all providers in one lookup). Direct ISP sites are fallbacks only if BroadbandNow fails. Includes tested browser navigation patterns."
---

## Provider Priority Order

1. **BroadbandNow** (PRIMARY) -- Aggregator that returns all providers at a specific address in one lookup. Use this first. Returns Quantum Fiber, CenturyLink, Xfinity, AT&T, T-Mobile, Verizon availability.
2. **CenturyLink/Lumen** (FALLBACK) -- Direct check if BroadbandNow misses fiber data. Brand name: "Quantum Fiber" for fiber plans.
3. **Ziply Fiber** (FALLBACK) -- Only if BroadbandNow doesn't list it. Available in some Portland neighborhoods.
4. **Xfinity/Comcast** (FALLBACK) -- Only if BroadbandNow data seems incomplete.

## Step-by-Step: BroadbandNow (PRIMARY — Tested and Working)

**IMPORTANT**: BroadbandNow uses Google Places autocomplete. You CANNOT just type an address and submit — it will error with "Please enter a valid address." You MUST select from the autocomplete dropdown.

### First Address (from homepage):
1. `navigate` to `https://broadbandnow.com/`
2. `computer` action `wait` for 2 seconds
3. `computer` action `left_click` on the search input (~center of page, coordinate ~[755, 303])
4. `computer` action `type` a SHORT address: street number + street name + city (e.g., "4030 SE Holgate Portland") — do NOT include state/zip, keep it short to trigger autocomplete
5. `computer` action `wait` for 2 seconds — autocomplete dropdown appears
6. Use `find` "autocomplete suggestion [street name] [city]" to locate the matching suggestion by ref — this is more reliable than clicking by coordinate
7. `computer` action `left_click` on the returned ref
8. `computer` action `wait` for 3 seconds — page navigates to address-specific results
9. Verify page shows "Internet Providers at Your Address" and "We found X providers available at your address"
10. Use `find` to locate "providers found at your address" to get the count
11. Use `get_page_text` to extract all provider names, speeds, connection types, and prices
12. Scroll down to see all providers if needed

### Subsequent Addresses (from results page refine box):
1. `computer` action `triple_click` on the refine search input (top right, ~coordinate [1105, 195]) to select existing text
2. `computer` action `type` the new short address
3. `computer` action `wait` for 2 seconds for autocomplete
4. `find` "autocomplete suggestion [street name] [city]" to locate the matching suggestion by ref
5. `computer` action `left_click` on the returned ref
6. `computer` action `wait` for 3 seconds for results
7. Extract data as above

### Key Gotchas (Tested):
- `form_input` TRUNCATES at ~30 characters on BroadbandNow — use `computer` action `type` instead
- The autocomplete dropdown requires typing, NOT pasting via `form_input`
- If autocomplete doesn't appear, try typing slower or a shorter query
- URL navigation without lat/long params falls back to zip-level results (NOT address-specific)

## Step-by-Step: CenturyLink/Lumen (FALLBACK)

1. `navigate` to `https://www.centurylink.com/home/internet.html`
2. `find` the address input (placeholder like "Enter your address" or "Check availability")
3. `computer` action `type` the full address (avoid `form_input` — may truncate)
4. `computer` click the search/check button
5. `computer` action `wait` for 3 seconds
6. `read_page` or `get_page_text` to extract available plans
7. Look for keywords: "Fiber", "940 Mbps", "Quantum Fiber", "Up to 940"

**Note**: CenturyLink often shows a CAPTCHA on first visit. Follow CAPTCHA handling procedure below.

## Step-by-Step: Ziply Fiber (FALLBACK)

1. `navigate` to `https://ziplyfiber.com/check-availability`
2. `find` address input field
3. `computer` action `type` the full address
4. `computer` click "Check Availability" button
5. `computer` action `wait` for 3 seconds
6. `get_page_text` for plan details
7. Look for fiber tiers: 50, 100, 300, 1000, 2000 Mbps

## Step-by-Step: Xfinity/Comcast (FALLBACK)

1. `navigate` to `https://www.xfinity.com/learn/internet-service`
2. `find` "Check availability" button or address input
3. `computer` action `type` the full address
4. Submit and `computer` action `wait` for 3 seconds
5. `get_page_text` to extract available plans and speeds
6. Note highest available speed and technology type (cable vs fiber)

## Result Schema

No ISP screenshots needed — text data only:

```json
{
  "providers_found": 5,
  "quantum_fiber": { "available": true, "fiber": true, "max_down": 8000, "price_from": 45 },
  "xfinity": { "available": true, "fiber": false, "max_down": 2000, "connection": "Cable", "price_from": 40 },
  "att": { "available": true, "max_down": 300, "connection": "5G", "price_from": 65 },
  "tmobile": { "available": true, "max_down": 415, "connection": "5G", "price_from": 50 },
  "centurylink": { "available": true, "fiber": true, "max_down": 940, "price_from": 50 },
  "broadbandnow_summary": "5 providers. Fiber: Quantum Fiber (8 Gbps), CenturyLink (940 Mbps). Cable: Xfinity (2 Gbps).",
  "classification": "Excellent"
}
```

## Common Gotchas

- **BroadbandNow** requires Google Places autocomplete selection — direct text submission fails
- **BroadbandNow** `form_input` truncates at ~30 chars — always use `computer` `type` instead
- **CenturyLink** often shows a redirect or CAPTCHA on first visit
- **Ziply** may not recognize all address formats — try variations
- **Xfinity** sometimes requires zip code only for initial check, then full address

## CAPTCHA Handling

If any ISP checker shows a CAPTCHA:

1. Take a screenshot of the CAPTCHA page
2. Ask the user: "I've hit a CAPTCHA on [provider]. Please solve it in the browser window, then tell me when you're done."
3. Wait for user confirmation in chat
4. Continue with data extraction
5. If user can't solve it, mark that provider as "check_failed" for this address

## Internet Suitability Classification

Based on results, classify each address:

- **Excellent**: Residential fiber available (Quantum Fiber or CenturyLink, 940+ Mbps symmetric)
- **Good**: Gigabit cable available (Xfinity 2 Gbps down) but no residential fiber at specific address
- **Adequate**: Cable available but under 500 Mbps
- **Poor**: DSL only or no broadband options
