# HW5: Modeling the Wildcat Capital Data as a Star Schema in Power BI

**Rose Mazzeo · MIS3060**

This folder holds my answers and evidence for HW5. The written answers (Parts A, B, C, E and F) are in `star_design.md`. The Power BI model (Part D) is in `powerbi/`. Two read-only Python scripts prove the key and grain claims in code.

## Structure

```
hw05/
├── README.md                  this file
├── star_design.md             Parts A (keys), B (grain), C (measures), E (design questions), F (reflection)
├── scripts/
│   ├── 01_keys.py             Part A evidence: primary keys, foreign keys, orphans, blank keys
│   └── 02_grain.py            Part B evidence: grain keys, minimality, monthly dates, transaction key
├── powerbi/
│   ├── hw05.pbix              Part D: the Power BI model (about 21.8 MB)
│   └── model_view.png         Part D: screenshot of the Model view
└── *.csv                      the eight Wildcat tables (inputs; unchanged)
```

The `.pbix` is about 21.8 MB, under GitHub's 100 MB limit, so it is in the repo and not on Brightspace.

## The model in one paragraph

Eight tables, 10 relationships, all many-to-one, single direction and active. Three fact tables (`fact_fees`, `fact_portfolio_snapshot`, `fact_transactions`) join to `dim_client` on `client_id` and to `dim_date[date]` on their own date column. `fact_transactions[security_id]` joins to `dim_security`, and `fact_portfolio_snapshot[benchmark_id]` joins to `dim_benchmark`. Two dimension-to-dimension links remain: `dim_client` → `dim_advisor` and `dim_security` → `dim_benchmark`. The three direct `advisor_id` links from the facts to `dim_advisor` were deleted so that each fact has one path to the advisor. `dim_date` is marked as the date table. The reasons are in `star_design.md`, Part E.

## How to run

### The scripts (Parts A and B)

Both scripts only read the CSVs; they never change a file. They need Python 3 and pandas.

PowerShell, from the repo root `mis3060-bi-ai`:
```powershell
.\.venv\Scripts\Activate.ps1
cd hw05
pip install pandas
python scripts/01_keys.py
python scripts/02_grain.py
```

Git Bash: use `source .venv/Scripts/activate` instead of the activation line.

Each check prints `PASS` or `FAIL`. The last line is `ALL CHECKS PASSED` and the exit code is 0 when everything is fine. To keep the output for evidence, add `> keys_output.txt` or `> grain_output.txt`. By default the scripts read the CSVs in the folder above `scripts/`; `--data-dir <folder>` points them somewhere else. File names such as `dim_client (2).csv` are handled, because the `(2)` is stripped.

What they check:
- `01_keys.py`: row counts match the handout; every primary key is unique, never blank and a whole number; all 13 foreign keys have 0 orphans; the only blank foreign key is `fact_transactions[security_id]` and it is blank exactly on Deposit, Withdrawal and Advisory Fee rows; the fact tables hold no `date_id`; fact `advisor_id` equals the client's advisor on every row.
- `02_grain.py`: the grain key of `fact_fees` (`client_id`, `fee_date`) and `fact_portfolio_snapshot` (`client_id`, `snapshot_date`) is unique and minimal; dates are always the 1st of a month; `fact_transactions` has no natural key, so only `txn_id` is unique (1,238 rows repeat the client, date, type and security but none shares an amount).

### The Power BI model (Part D)

1. Open `powerbi/hw05.pbix` in Power BI Desktop. The data is already loaded and nothing needs refreshing; if Power BI asks for the CSV location, point it at the `hw05` folder.
2. Open **Model view** to see the 10 relationships, and **Manage relationships** for cardinality, direction and Active status.
3. The report page has a row-count card for each of the eight tables (they match the handout), a table showing the `(Blank)` ticker, and slicers for advisor, client tier and year that filter all three fact tables.
4. `powerbi/model_view.png` is a screenshot of the Model view.

## Claude Code findings

Claude Code reviewed the scripts and `star_design.md` before they were committed. It re-ran both scripts on the CSVs and recomputed the figures quoted in the write-up. Findings:

- **Scripts:** both pass (all checks, exit code 0).
- **Numbers confirmed against the data:** 101,528 blank `security_id` rows split as 35,956 Deposit, 29,830 Withdrawal and 35,742 Advisory Fee; deposits minus withdrawals = $0.327B; all six transaction types summed = $16.15B; AUM for December 2024 = $12.73B against $566.7B for all 60 months summed; `dim_date[date]` has 1,827 unique values.
- **Corrected during the work:** the first Power BI model had the `advisor_id` links from the facts active and the `client_id` links inactive, with no date relationships. This was fixed as described above.
- **Data issues found that I left alone** (the handout says not to change the tables in this assignment, and none of them affects the keys or grain):
  - 75 clients have the risk profile `Unknown`.
  - 7,350 snapshot months (5.7%) have no fee row, so fee totals cover only recorded fees.
  - Advisory Fee debits in `fact_transactions` do not reconcile to `fact_fees` for any client-month, so the two tables should not be compared as if they were the same money.
  - Dividend `amount` equals `shares × price` on every Dividend row, so it looks like the value of a position and not the income paid.
  - `fact_transactions` has no natural key (see above).
- **Limits of the review:** Claude Code cannot run Power BI, so the model itself was checked from my screenshots and my own slicer and row-count tests. The two visuals described as answerable in Part F (monthly fees by fee type; AUM by month and risk profile) are reasoned from the model and the Part C classifications. I did not build them.
- **One point to note:** Part F proposes a new `net_cash_flow` column and a `dim_txn_type` table. This is only a recommendation; the model submitted has no new columns or tables, as the handout requires.
