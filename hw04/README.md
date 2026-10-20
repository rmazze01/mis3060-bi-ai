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
These come from testing the scripts against the data and from a read-through of all three scripts with Claude (static check for unused code and syntax). They were not produced by a separate Claude Code session in VS Code.

| # | Script | Finding | Action |
|---|---|---|---|
| 1 | `02_clean.py` | First run stopped on its own assertion: the `active_alpha_ytd = return_ytd − benchmark_return_ytd` check (1e-5) was too strict for the 300 converted percent rows, which are only precise to the rounding of a 2-decimal percent. | **Fixed.** Strict 1e-5 on originally numeric rows; ≤ 0.000051 on converted rows. |
| 2 | `01_profile.py` | Explanatory text on the share/amount finding said the amounts would not match even with absolute shares, which is backwards. | **Fixed** before the committed run (now: "836 DO match when \|shares\| is used"). |
| 3 | `01_profile.py` | Two explanation strings overclaim: the AUM-floor finding says returns are "near −100%" (median is −94%, some are near 0), and the return finding says "usually on tiny-AUM accounts" (disproved: median AUM $42.5k, none at the floor). Text only; no check logic is affected. | **Open.** Wording to correct; requires rerunning and recommitting `dq_summary_raw.csv`. |
| 4 | `decision_log.md` | D03 states a tolerance of 0.0000501, but `02_clean.py` uses 0.000051 (true maximum difference is about 0.00005). Some audit-stage counts (836, 197,175, 40,649 of 143,311, $263.8M) are raw-extract figures; clean-stage counts are slightly lower because 200 rows were quarantined (835, 197,044). | **Open.** Explained in `reports/cleaning_report.md` and `data/clean/README_clean.md`; log wording could be aligned. |
| 5 | `03_validate.py` | The 836 negative-share Buy rows are counted by two different checks (`shares > 0` and `amount = shares × price`), so raw transaction rule pass counts one root cause twice (1,672 failed evaluations from 836 rows). | **Accepted.** The checks are legitimately different rules; documented here. |
| 6 | `02_clean.py` | Expected counts from the audit (200, 300, 78, 312, 420, 386, 76, 197,044) are hard-coded, so the script stops if run on a different extract. | **Accepted.** Intentional fail-safe. |
| 7 | all | Tested with pandas 3.0.5. The scripts use `lineterminator=` and so need pandas 1.5 or newer; pandas 2.x was not tested. | **Accepted**, noted. |
| 8 | `01_profile.py`, `02_clean.py` | Unused code: unused arguments `df_map` and `allow_null` (01), unused `numpy` import and `project_rel` argument (02). | **Open.** Harmless; no effect on results. |

## 6. Version control
One or more commits per part, each with a message that says what changed. Because `.gitignore` contains `*.csv`, the CSV deliverables were added with `git add -f`.
