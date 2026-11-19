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

_To be filled in after the scripts are written._

## Claude Code review of `00_make_extract.py`

_To be filled in._

## Claude Code review of `01_reconcile_kpis.py`

_To be filled in._

## Extract check

_To be filled in (Part D, item 3)._

## Filter audit

_To be filled in (Part D, item 4)._
