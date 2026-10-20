# HW4 — Cleaning the Wildcat Capital Data
**MIS3060 Business Intelligence with AI · Villanova University · Rose Mazzeo**

Python programs that audit eight warehouse tables, repair what can be repaired without inventing data, flag what cannot, and prove each fix. The raw files are never modified. Full reasoning is in `decision_log.md`; the committee-facing summary is `reports/cleaning_report.md`.

## 1. Structure

```
hw04/
├── README.md                      this file
├── decision_log.md                Part B  19 entries: 8 acted on, 10 left alone, 1 passed-checks
├── scripts/
│   ├── 01_profile.py              Part A  generic profiler + 594 checks in 4 groups
│   ├── 02_clean.py                Part C  one asserted step per decision, quarantine, audit trail
│   └── 03_validate.py             Part D  reusable RI function, rules, reconciliations, IQR, scorecard
├── data/
│   ├── clean/                     8 clean tables (same names, same columns, + 4 flag columns) + README_clean.md
│   └── audit/                     cleaning_log.csv, value_changes.csv, quarantine_fact_transactions_orphan_client.csv
└── reports/
    ├── profile_raw.csv            Part A  75 columns profiled
    ├── dq_summary_raw.csv         Part A  594 checks (36 FAIL: 8 ERROR, 11 WARN, 17 INFO)
    ├── data_quality_scorecard.csv Part D  8 tables x {raw, clean}
    ├── ri_results.csv             Part D  13 relationships x {raw, clean}
    ├── validation_detail.csv      Part D  every rule, reconciliation, judgment flag, IQR result
    └── cleaning_report.md         Part E  report for the portfolio committee
```
The raw CSVs (for example `dim_advisor (1).csv`) sit in the `hw04` folder and are not part of the submission.

## 2. How to run
Windows, VS Code. PowerShell shown; in Git Bash use `source .venv/Scripts/activate`.

```
cd C:\MIS3060\mis3060-bi-ai
python --version                    # developed and run on Python 3.12
python -m venv .venv                # once
.venv\Scripts\Activate.ps1          # prompt should start with (.venv)
pip install pandas                  # once
cd hw04
python scripts/01_profile.py        # Part A -> reports/profile_raw.csv, dq_summary_raw.csv   (about a minute in testing)
python scripts/02_clean.py          # Part C -> data/clean/, data/audit/                      (seconds)
python scripts/03_validate.py       # Part D -> reports/data_quality_scorecard.csv + 2 more   (seconds)
```
Run them in this order (`03_validate.py` reads `data/clean/`). The scripts find the raw CSVs automatically (the `hw04` folder, `Wildcat Capital/`, or `data/raw/`), accept names like `dim_advisor (1).csv`, and take `--data-dir "path"` to override. Every file is read as text (`dtype=str, keep_default_na=False`) and converted on purpose. `02_clean.py` stops with an `AssertionError` if any fix does not do what the decision log claims.

## 3. Results at a glance
| | Raw | Clean |
|---|---:|---:|
| fact_transactions rows | 298,772 | 298,572 (+ 200 quarantined, $10,888,495) |
| fact_transactions referential match | 81.95% | 100% |
| fact_transactions type validity | 90.545% | 100% |
| fact_transactions rule pass | 99.92% | 100% |
| dim_client rule pass | 99.69% | 100% |
| fact_portfolio_snapshot type validity | 99.981% | 100% |
| Orphan rows across the 13 relationships | 197,375 (200 client + 197,175 security) | 0 |

Values changed: 198,257, every one logged in `data/audit/value_changes.csv`. For all eight tables, raw rows = clean rows + quarantined rows. Flagged and left uncorrected: 312 returns above +500%, 420 snapshot and 386 fee records at exactly $1,000 of assets, 76 blank risk profiles. Details and known limitations: `data/clean/README_clean.md`.

## 4. Process and AI use
Scripts and documents were drafted with Claude, run and debugged in VS Code, and each was tested against the real data before commit. The decision log was written before the cleaning code and is the specification for it. Every figure in the report was checked against the script output and the log.

## 5. Code review findings and actions
These come from testing the scripts against the data, a read-through with Claude (static check for unused code), and a read-only review of all three scripts by Claude Code in VS Code (no files edited, scripts not run). I checked each finding against the code before acting. No high-severity problems were reported, and none of the changes below altered any output: after the fixes I reran all three scripts and every report, clean table and audit file was byte-identical to the previous run.

| # | Script | Finding | Action |
|---|---|---|---|
| 1 | `02_clean.py` | Own testing: the first run stopped on the alpha assertion (1e-5 was too strict for the 300 converted percent rows, which are only precise to the rounding of a 2-decimal percent). | **Fixed.** Strict 1e-5 on originally numeric rows; ≤ 0.000051 on converted rows. |
| 2 | `01_profile.py` | Own testing: explanatory text on the share/amount finding said the amounts would not match even with absolute shares, which is backwards. | **Fixed** before the committed run. |
| 3 | `01_profile.py` | Own review: two finding strings overclaimed ("near −100%"; "usually on tiny-AUM accounts", disproved by the data). | **Fixed.** Reworded; `dq_summary_raw.csv` regenerated. |
| 4 | `decision_log.md` | Own review: D03 tolerance 0.0000501 vs 0.000051 in code; some audit counts are raw-extract figures (836, 197,175) while clean-stage counts are lower (835, 197,044) because 200 rows were quarantined. | **Fixed.** Log states 0.000051 and explains the count difference. |
| 5 | `02_clean.py` | **Claude Code, medium:** the D03 and D06 reconciliation asserts used `.max()` / `.min()`, which skip NaN, so an unparseable benchmark or alpha value would pass unchecked. Same for the AUM-floor `min()` checks and for `num()` coercing unparseable shares / price / amount to NaN. | **Fixed.** Asserts now use `(...).all()` and first require that every value parses. |
| 6 | `02_clean.py` | **Claude Code, medium:** `--data-dir` pointed at `data/clean` or `data/audit` would overwrite the inputs; the hash check only notices afterwards. | **Fixed.** The script stops before writing (tested). |
| 7 | all three | **Claude Code, medium:** `find_file` silently picked one file when several matched (for example `dim_date (1).csv` and `(2)`). | **Fixed.** The script now stops and lists the matches. |
| 8 | `02_clean.py` | **Claude Code, low:** D05 only asserted 0 < n ≤ 836; D06 "flagged values unchanged" had no explicit assert; a no-op `.rename` was left in. | **Fixed.** D05 expects exactly 835; explicit D06 assert added; `.rename` removed. |
| 9 | `decision_log.md` | **Claude Code, low:** the log said the quarantine file has a `reason` column (it is `quarantine_reason` plus `raw_row_number`) and said the full audit is re-run in step 7 (that happens in `03_validate.py`). | **Fixed.** Wording corrected. |
| 10 | `01_profile.py`, `02_clean.py` | Unused arguments `df_map`, `allow_null`, `project_rel` and an unused `numpy` import. | **Fixed.** Removed. |
| 11 | `03_validate.py` | **Claude Code, low:** the RI function trims keys before matching and does not report duplicate dimension keys; `pcts.fillna(0)` hides NaN. | **Accepted.** The data has no whitespace or duplicate keys; revisit when the function is reused in Assignment 5. |
| 12 | `01_profile.py` | **Claude Code, low–medium:** a table missing from the config raises `KeyError`; some dates and one `dim_client` rule are hard-coded in group 2–4 checks; `str.match` with `$` anchors. | **Accepted.** Profiling itself is generic; the business-rule checks name their tables on purpose. No effect on results. |
| 13 | `02_clean.py` | **Claude Code, low:** PROOF 2 compares counts of changed cells, not the exact cells; the log notes for D12, D15 and D18 are fixed text. | **Accepted.** Every write goes through one logging function; the evidence for those entries is in `decision_log.md`. |
| 14 | `02_clean.py` | Expected audit counts (200, 300, 78, 312, 420, 386, 76, 197,044, 835) are hard-coded, so the script stops on a different extract. | **Accepted.** Intentional fail-safe. |
| 15 | all | Tested with pandas 3.0.5; `lineterminator=` needs pandas 1.5+, and the scripts need Python 3.10+. pandas 2.x untested. | **Accepted**, noted. |

## 6. Version control
One or more commits per part, each with a message that says what changed. Because `.gitignore` contains `*.csv`, the CSV deliverables were added with `git add -f`.
