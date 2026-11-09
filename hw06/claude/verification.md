# Verification

## Measure tested
`Top 10 Client Share (Claude)`, the measure from the Claude chat in `dax_session.md`. It ranks each client's AUM at the last snapshot date in the filter, sums the top 10, and divides by the total of those client balances.

It iterates over `dim_client[client_id]` rather than the `client_id` column in `fact_portfolio_snapshot`. `dim_client` has one row per client and holds `client_tier`, so the tier filter acts on the same table the measure iterates over, while the snapshot column repeats once per month. Clients with no snapshot in the period get a blank AUM, which the measure drops with `FILTER ... NOT ISBLANK`, so they can't affect the top 10 or the total.

## Did it run as written?
Not at first. The first version used the variable name `LastDate`, which is the name of the built-in DAX function `LASTDATE`, and the formula showed a squiggle error. Claude renamed the variable to `EndDate` but left one reference inside `CALCULATE` still reading `= LastDate`, so it still errored. I sent Claude a screenshot, it found the missed line (follow-up #2 in `dax_session.md`), and after that the measure ran. Only the variable name changed; the logic is the same as Claude's first draft.

## What the tests returned
- **Measure by year (2024):** Ending AUM 12,729,572,078.86, which matches pandas exactly. Top 10 Share displays as 0.06 (0.0616 at full precision).
- **Measure by tier (2024):** HNW 0.031397, Retail 0.018348, UHNW 0.081264.
- **UHNW Dec 2024 manual check:** a separate query with no measure logic. Top 10 AUM 784,005,019.49; share 0.08126426752227993.

## Reconciliation evidence
The Part A measure `Top 10 Client Share` was reconciled in `reports/measure_reconciliation.csv` (83 of 83 rows match). The 2024 tier rows there (HNW 3.14%, Retail 1.83%, UHNW 8.13%) equal the values returned by the Claude measure above, to four decimals.

## Edge cases
1. **Tier filter:** UHNW holds all 10 of the largest clients, so the UHNW share (8.13%) is higher than the all-tiers share (6.16%). The measure responds to the tier filter and the manual check agrees.
2. **Single date (Dec 2024):** the top 10 is chosen from balances at one snapshot, not summed across months.

## Limitation
The manual check's denominator (9,647,598,426.64) was typed into the query by the Claude chat. I confirmed it independently with a separate sum query in DAX query view (it returned 9647598426.64) and in pandas (244 UHNW clients at Dec 2024).

## One Claude claim checked
Claude said clients are ranked by their balance at the last snapshot date in the filter. I checked this against a pandas calculation across all 20 year-and-tier combinations. The ranking and the share were the same in every case. The claim holds on this data.

## Result
The Claude measure matches the independent calculation and my Part A measure.
