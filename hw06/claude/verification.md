# Verification

## Measure tested
`Top 10 Client Share (Claude)`, the measure from the Claude chat in `dax_session.md`. It ranks each client's AUM at the last snapshot date in the filter, sums the top 10, and divides by the total of those client balances.

It iterates over `dim_client[client_id]` rather than the `client_id` column in `fact_portfolio_snapshot`. `dim_client` has one row per client and holds `client_tier`, so the tier filter acts on the same table the measure iterates over, while the snapshot column repeats once per month. Clients with no snapshot in the period get a blank AUM, which the measure drops with `FILTER ... NOT ISBLANK`, so they can't affect the top 10 or the total.

## Did it run as written?
Not at first. The first version used the variable name `LastDate`, which is the name of the built-in DAX function `LASTDATE`, and the formula showed a squiggle error. Claude renamed the variable to `EndDate` but left one reference inside `CALCULATE` still reading `= LastDate`, so it still errored. I sent Claude a screenshot, it found the missed line (follow-up #2 in `dax_session.md`), and after that the measure ran. Only the variable name changed; the logic is the same as Claude's first draft.

## What the tests returned
- **Grand total:** 0.061589.
- **By year (all years):** 2020 0.070411, 2021 0.063754, 2022 0.055309, 2023 0.060379, 2024 0.061589.
- **By tier, 2024:** HNW 0.031397, Retail 0.018348, UHNW 0.081264.
- **2024, all tiers:** Ending AUM 12,729,572,078.86, which matches pandas exactly.
- **UHNW Dec 2024 manual check:** a separate query with no measure logic. Top 10 AUM 784,005,019.49; share 0.08126426752227993.

## Which reconciliation rows prove it
The Part A measure `Top 10 Client Share` is reconciled in `reports/measure_reconciliation.csv` (83 of 83 rows match). The rows that cover the same numbers are `Top 10 Client Share | Grand total` (6.16%) and `Top 10 Client Share | Tier HNW | Year 2024`, `Tier Retail | Year 2024` and `Tier UHNW | Year 2024` (3.14%, 1.83%, 8.13%). The Claude measure returns the same values as those rows. The by-year values above also equal the pandas Top 10 share for each year.

## Edge cases
1. **Grand total (no filter):** 0.061589, equal to the 2024 value, because the top 10 is read at the last snapshot, not summed across months.
2. **Year 2022:** 0.055309, the lowest year, matching pandas.
3. **2024 tier table:** all three tiers match. UHNW holds all 10 of the largest clients, so its share (8.13%) is higher than the all-tiers share (6.16%).
4. **Single date (Dec 2024, UHNW):** the manual check divides the top 10 by the UHNW total at that date (9,647,598,426.64) and gets the same 8.13%.

## Limitation
The manual check's denominator (9,647,598,426.64) was typed into the query by the Claude chat. I confirmed it independently with a separate sum query in DAX query view (it returned 9647598426.64) and in pandas (244 UHNW clients at Dec 2024).

## Claims checked
1. **Confirmed in Power BI:** Claude said `LastDate` was flagged because it matches the built-in `LASTDATE` function, and that renaming the variable would clear the error. The squiggle only cleared after the missed `= LastDate` reference was also renamed, so the claim was right, but Claude's first fix was incomplete.
2. **Confirmed in pandas (run in a Claude session):** Claude said clients are ranked by their balance at the last snapshot date in the filter. A pandas check across all 20 year-and-tier combinations, using that date for both the top 10 and the total, gave the same share as the measure in every case.

## Result
The Claude measure matches the independent calculation and my Part A measure.

## Queries I ran
Paste each into DAX query view in `hw06.pbix` to reproduce the numbers above. The first three read the measure from the model.

By year (all years):
```dax
EVALUATE SUMMARIZECOLUMNS ( dim_date[year], "Top 10 Share", FORMAT ( [Top 10 Client Share (Claude)], "0.000000" ) ) ORDER BY dim_date[year]
```

Grand total:
```dax
EVALUATE ROW ( "Grand total", FORMAT ( [Top 10 Client Share (Claude)], "0.000000" ) )
```

By tier, 2024:
```dax
EVALUATE SUMMARIZECOLUMNS ( dim_date[year], dim_client[client_tier], KEEPFILTERS ( FILTER ( VALUES ( dim_date[year] ), dim_date[year] = 2024 ) ), "Top 10 Share", FORMAT ( [Top 10 Client Share (Claude)], "0.000000" ) ) ORDER BY dim_client[client_tier]
```

2024, all tiers, with Ending AUM (equivalent form of the saved tab "measure by year (2024)", which defined the measure inline):
```dax
EVALUATE SUMMARIZECOLUMNS ( dim_date[year], FILTER ( ALL ( dim_date[year] ), dim_date[year] = 2024 ), "Ending AUM", [Ending AUM], "Top 10 Share", [Top 10 Client Share (Claude)] )
```

Independent manual check, UHNW, Dec 2024 (no measure logic; the denominator is typed in):
```dax
EVALUATE
VAR d = DATE ( 2024, 12, 1 )
VAR Clients =
    CALCULATETABLE (
        ADDCOLUMNS (
            VALUES ( dim_client[client_id] ),
            "@AUM", CALCULATE ( SUM ( fact_portfolio_snapshot[aum] ), fact_portfolio_snapshot[snapshot_date] = d )
        ),
        dim_client[client_tier] = "UHNW"
    )
VAR Top10 = TOPN ( 10, FILTER ( Clients, NOT ISBLANK ( [@AUM] ) ), [@AUM], DESC )
RETURN
    ROW ( "Top10 AUM", SUMX ( Top10, [@AUM] ), "Top10 share", DIVIDE ( SUMX ( Top10, [@AUM] ), 9647598426.64 ) )
```

Check on that denominator:
```dax
EVALUATE ROW ( "UHNW Dec 2024 AUM", CALCULATE ( SUM ( fact_portfolio_snapshot[aum] ), dim_client[client_tier] = "UHNW", fact_portfolio_snapshot[snapshot_date] = DATE ( 2024, 12, 1 ) ) )
```
