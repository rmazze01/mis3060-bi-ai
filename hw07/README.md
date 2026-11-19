# HW7: Where Did 2024 Growth Come From? A Two-Page Wildcat Dashboard (hw07)

Two-page Power BI report on Wildcat Capital's 2024 AUM growth (net flows vs. market change, by client tier and region), with pandas checks of every number.

## Structure

```
hw07/
  README.md
  HW07_Dashboard_Growth_Drivers.md   assignment spec
  design_plan.md
  design/                            wireframes
    prototypes/                      Claude visual prototypes
  scripts/
    00_make_extract.py
    01_reconcile_kpis.py
  data/
    growth_extract.csv
    README.md                        balance vs. flow label for each column
  dashboard/
    hw07.pbix
    page1.png
    page2.png
  reports/
    powerbi_values.csv
    kpi_reconciliation.csv
  claude/
    design_critique.md
    before.png
    after.png
  executive_summary.md
  Assignment 6 Reference/            copied from hw06, see below
```

## Assignment 6 Reference

`Assignment 6 Reference/` is a copy of the `hw06` files that HW7 builds on. It keeps the same folder layout as `hw06`, so the HW6 script's relative paths still work.

| Folder | What it holds | Used for |
|---|---|---|
| `WildcatCapitalClean/` | `dim_advisor`, `dim_client`, `dim_date (1)`, `fact_fees`, `fact_portfolio_snapshot`, `fact_transactions (1)` (CSV) | Source data for `scripts/00_make_extract.py` and `scripts/01_reconcile_kpis.py` |
| `scripts/` | `01_reconcile_measures.py` | Base for `scripts/01_reconcile_kpis.py` |
| `powerbi/` | `measures.md`, `export_values_query.dax` | Measure definitions (including `Net Flows`) and the DAX export query |
| `reports/` | `powerbi_values.csv`, `measure_reconciliation.csv` | Format and tolerances to match |
| `README.md` | The HW6 README | Reference |

**The CSV files in this folder are not committed to git.** `.gitignore` excludes `*.csv` except directly inside a `hw*/` folder, so everything under `Assignment 6 Reference/WildcatCapitalClean/` and `Assignment 6 Reference/reports/` stays on disk only. This avoids committing a second copy of the `hw06` data. The scripts read these files, so to run HW7 on a fresh clone, copy the HW6 `WildcatCapitalClean/` CSVs into `Assignment 6 Reference/WildcatCapitalClean/` first (the same files as `hw06/WildcatCapitalClean/`).

## How to run

All commands run from the `hw07` folder in Git Bash. The scripts read the CSVs in `Assignment 6 Reference/WildcatCapitalClean/` (see above).

1. **Build the extract** (pandas only, nothing from Power BI): `python scripts/00_make_extract.py` writes `data/growth_extract.csv` (75 rows).
2. **Open `dashboard/hw07.pbix`** in Power BI Desktop. The year slicer is saved on 2024.
3. **Export the Power BI values.** In DAX query view, run `dashboard/export_values_query.dax` (43 rows, all 2024). Copy the result into `reports/powerbi_values.csv` (columns `measure`, `slice`, `value`, tab-separated, as in Assignment 6).
4. **Reconcile:** `python scripts/01_reconcile_kpis.py` writes `reports/kpi_reconciliation.csv` (`measure, slice, powerbi_value, pandas_value, abs_diff, match`) and runs the extract check. Tolerance is 0.01 for currency, counts and basis points, 0.0001 for ratios; Alpha Signal must match exactly. The exit code is 1 if anything does not match.

The measures behind the report are in `dashboard/add_measures.dax` (the ICE 12 measures plus `Market Change`) and `dashboard/alt_text_measures.dax` (the dynamic alt text). `reports/*.csv` and `data/growth_extract.csv` need `git add -f`, because `.gitignore` excludes CSVs.

## Claude Code review of `00_make_extract.py`

Claude Code recomputed the extract from the raw CSVs without using the script. It confirmed that December AUM per year and net flows match (2024: ending AUM 12,729,572,078.86, net flows 77,513,055), that there are 75 rows and no empty cells, and that the code does what the definition says. Its findings were mainly about the definition. I checked each number against the CSVs before acting on it.

| # | Severity | What Claude Code flagged | What I did |
|---|---|---|---|
| 1 | High | `market_change` includes money from clients who joined or left. New clients have an opening balance but no Deposit, and closed clients' balances just stop. Joiners were 1,059.7M (310 clients) in 2021 and 1,128.6M (343) in 2022; leavers were 400.4M (175) in 2023; none in 2024. About 58% of the 2021 market change is new-client money, and the 2022 market loss is closer to −1.9B than −0.78B | Verified. Kept the definition the assignment gives, and documented it in `data/README.md` ("What market_change does and does not mean") and in the Page 1 caveat, which says that none joined or left in 2024. It does not affect the 2024 numbers |
| 2 | Medium | Snapshots are all dated the 1st, so "December" is 1 December, while net flows cover 1 January to 31 December. Market change is off by this December's flows minus last December's (about +1.4M in 2024, −4.7M in 2023) | Verified (December flows 5.1, 6.1, 7.7, 3.0, 4.4M). Documented as a balance "as of 1 December" in `data/README.md`. The extract and Power BI use the same convention, so they reconcile |
| 3 | Low–medium | 2,410 transactions are dated after a client's last snapshot (278 deposits, 238 withdrawals, net +1.56M, all in 2023). They count in net flows although the AUM is gone | Verified. Documented. None in 2024 |
| 4 | Low | Advisory fees get a sign of 0, so "market change" is after fees (62.2M of fee transactions in 2024) | Verified. Documented, and the Page 1 caveat says fees are included in Market Change |
| 5 | Medium | The end-of-script firm-level check reuses the same data, filter and strings, so it cannot catch a changed `txn_type` spelling, dropped clients, or errors in `ending_aum_ly` or `market_change` | Changed. The script now stops if Deposit or Withdrawal rows are missing or net flows are all zero, stops on a `client_id` that is not in `dim_client` (it only printed a warning before), checks that `ending_aum_ly` equals the prior year's `ending_aum`, and checks the `market_change` identity |
| 6 | Low | Hard-coded `YEARS` would silently drop a 2025 row | Changed. The script stops if the data has a year outside 2020–2024 |
| 7 | Low | `fillna(0.0)` on `ending_aum` would turn a missing balance into zero AUM | Changed. A year, tier and region cell with no December balance is now an error. Only net flows is filled with 0, because no deposits or withdrawals in a cell is a real zero |
| 8 | Low | Region comes from `dim_client.advisor_id`, and the fact tables carry their own `advisor_id` | Checked: they agree on every row (0 differences in snapshots and transactions), so the extract matches either model relationship. It would only differ if a client changed advisors |
| 9 | Low | Each column is rounded separately after `market_change` is computed, so the identity can be off by 0.01 in the CSV | Not changed. The identity is checked before rounding, and the 0.01 note is in `data/README.md`. Harmless, but a re-check in Excel could differ by a cent |

Claude Code also found the dimension tables clean: no duplicate client or advisor IDs, no missing advisors, and no missing or negative AUM.

## Claude Code review of `01_reconcile_kpis.py`

Claude Code found no logic errors and nothing that contradicted the three definitions (Net Flows, Market Change, region from the client's advisor), and all 43 rows matched. It flagged five places where a check could not fail on this data or a future data problem would pass silently. I checked each claim against the CSVs before changing anything (tiers and regions equal the script's lists; transaction types are Advisory Fee, Buy, Deposit, Dividend, Sell, Withdrawal; the smallest Deposit and Withdrawal amounts are 505.66 and 506.77; no fact row has an advisor different from its client's).

| # | What Claude Code flagged | What I did |
|---|---|---|
| 1 | The region check cannot tell whether Power BI uses the client's advisor or the transaction's advisor, because the two never differ in this data | Documented. The script now prints how many fact rows differ (0 in both fact tables), so the limitation is on record: the region rows would reconcile under either relationship |
| 2 | A blank in Power BI plus a blank in pandas counted as a match, including a blank Alpha Signal | Changed. A blank on either side, or both, is a mismatch, since every required 2024 row has data |
| 3 | The tier and region lists were hard-coded and not checked against the data or against the firm total | Changed. The script stops if the data's tiers or regions differ from its lists, or if the tier rows or the region rows do not add up to the firm total for Ending AUM, Ending AUM LY and Net Flows |
| 4 | Net Flows depends on the exact spelling of `Deposit` and `Withdrawal`, and on positive amounts | Changed. The script stops on any `txn_type` outside the six known values and on any Deposit or Withdrawal amount of 0 or less |
| 5 | The extract check counted 15 rows but not which tier and region pairs they were | Changed. It now requires exactly one 2024 row for each of the 15 tier and region pairs |

I tested the changes by breaking things on purpose: a wrong region flow, a percent sign in a value, a blank Alpha Signal and a duplicated extract pair each made the script exit with an error. Re-running on the real values still gives 43 of 43.

## Extract check

`growth_extract.csv` is built from the CSVs, not from Power BI. The 2024 rows were summed to tier and to region and compared with the tier and region rows of `reports/kpi_reconciliation.csv` for Ending AUM, Ending AUM LY, Net Flows and Market Change (3 tiers and 5 regions, 4 measures each).

**Result: 32 comparisons, 32 match, 0 do not match** (tolerance 0.01). The check also confirms the 2024 rows are exactly one per tier and region (15 rows).

## Filter audit

_To be filled in (Part D, item 4)._
