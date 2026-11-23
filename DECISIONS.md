# Decisions

## Decision: compare B's value with A's total_value
- Rejected: compare with base_value
- Why: B's values equal A's total_value (base + adjustment) on almost every row I checked

## Decision: a blank B value is NULL and flagged as VALUE_MISMATCH
- Rejected: treat blank as 0
- Why: 0 is a real amount; blank means unknown

## Decision: two entries that sum to A's total are a split, not an error
- Rejected: flag every record with 2+ entries as a duplicate
- Why: "part 2 of 2" rows add up to A's total; entries that do not sum to the total are DUPLICATE_IN_B

## Decision: a VOIDED record in A is not expected in B
- Rejected: flagging it as MISSING_IN_B
- Why: a voided event should not exist in B; if B still has an entry it is flagged VOIDED_IN_B

## Decision: location and date differences are also disagreements
- Rejected: only the four required reasons
- Why: A and B disagree even when the value matches, so I added LOCATION_MISMATCH and DATE_MISMATCH

## Decision: the cross-org row hides the other org's location
- Rejected: showing both locations to ORG-A
- Why: that would reveal an ORG-B location, so the other org's location is returned as null

## Decision: SQLite, DecimalField, plain-text location ids
- Rejected: float money, foreign keys
- Why: Decimal compares money exactly, and orphan rows still import

## Decision: React (Vite) table screen using a dev proxy to the Django API
- Rejected: calling the API directly from the browser (CORS errors)
- Why: the proxy in vite.config.js forwards /api to Django, so no CORS changes were needed. A plain HTML page is also still served at the backend's root