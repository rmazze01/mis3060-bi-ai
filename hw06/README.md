# HW6: DAX Measure Library (hw06)

Wildcat Capital AUM and performance measures in Power BI, reconciled to an independent pandas calculation.

## Structure

```
hw06/
  README.md
  HW06_DAX_Measure_Library.md        assignment spec
  WildcatCapitalClean/               the cleaned CSVs (not committed: *.csv is in .gitignore)
  powerbi/
    hw06.pbix                        posted model + _Measures table + Measures report page
    measures.md                      Part A documentation (Part C answers are added here)
    export_values_query.dax          DAX query that exports the Power BI values for Part B
  scripts/
    01_reconcile_measures.py         Part B reconciliation
  reports/
    powerbi_values.csv               Power BI numbers (columns: measure, slice, value)
    measure_reconciliation.csv       Part B output
  claude/                            Part D files
```

`reports/*.csv` are force-added to git (`git add -f`) because `.gitignore` ignores CSVs outside the top level of `hw06/`.

## How to run Part B

1. In Power BI Desktop, open DAX query view, paste `powerbi/export_values_query.dax`, and click Run (83 rows).
2. Copy the results into `reports/powerbi_values.csv` (header: `measure`, `slice`, `value`; tab- or comma-separated both work).
3. In Git Bash:

```bash
cd /c/MIS3060/mis3060-bi-ai
source .venv/Scripts/activate
cd hw06
python scripts/01_reconcile_measures.py
```

The script recomputes every measure in pandas from `WildcatCapitalClean/` (nothing is read from Power BI for that step), compares it to `reports/powerbi_values.csv`, and writes `reports/measure_reconciliation.csv` with columns `measure, slice, powerbi_value, pandas_value, abs_diff, match`.

Tolerances: 0.01 for currency (also used for `Ending Clients` and `Fee Yield (bps)`), 0.0001 for ratios, exact match for `Alpha Signal`. Both-blank rows (for example `AUM YoY %` in 2020, which has no prior year) count as a match.

The pandas side reproduces how `SAMEPERIODLASTYEAR` and `DATEADD` work: the dates in the current filter are shifted back one year or one month and only dates that exist in `dim_date` are kept, then the last snapshot in that shifted window is used.

## Part B result

83 rows reconciled: every measure at the grand total, measures 1, 4, 6-10 by year, measures 1, 3, 4, 7-11 by client tier for 2024, and measure 5 for December 2024, plus `AUM (naive SUM)` and its pandas twin. **83 rows, 83 match, 0 do not match.** Because nothing mismatched, there was no side to correct.

## Claude Code review of `01_reconcile_measures.py`

The script was reviewed before the commit. This review was done in the same Claude session that drafted the script, so it is not an independent run.

| Flagged | What I did |
|---|---|
| Delimiter was guessed by pandas (`sep=None`), which can misread a pasted export | Fixed: the script reads the header line and uses tab if present, otherwise comma |
| If two data files matched a table name (for example `dim_date.csv` and `dim_date (1).csv`), the first was used silently | Fixed: the script prints a warning and says which file it used |
| A value such as `19.58%` would be read as 19.58 instead of 0.1958 | Fixed: percent signs are no longer stripped, so such a value is reported as a mismatch |

No correctness problems were found. After the fixes the script was re-tested with tab- and comma-separated input, with deliberately wrong values (flagged correctly), and with a duplicate data file, and it still reports 83 of 83 on the real export.

## Notes on the Measures report page

The four summary measures (`Ending AUM`, `Ending Clients`, `Avg AUM per Client`, `Top 10 Client Share`) are shown as one single-measure table each, not as card visuals. In the Apporto Power BI Desktop session, card and KPI visuals displayed blank, even after recreating them, trying a new page, and restarting Power BI. Table visuals and DAX query view returned the correct values for the same measures, so the measures themselves are not affected. Only the visual type was changed.
