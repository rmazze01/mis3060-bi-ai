# Clean data - README
HW4 for MIS3060. Produced by `scripts/02_clean.py` from the raw Wildcat Capital extract. The raw files were not modified (SHA-256 checked before and after). Every change is traceable in `data/audit/`.

## 1. What is in this folder
Eight CSV files with the **same names and same columns** as the raw tables. Four 0/1 flag columns were added at the end of three tables (section 4).

| Table | Raw rows | Clean rows | Quarantined |
|---|---:|---:|---:|
| `dim_advisor` | 25 | 25 | 0 |
| `dim_client` | 2,525 | 2,525 | 0 |
| `dim_date` | 1,827 | 1,827 | 0 |
| `dim_security` | 500 | 500 | 0 |
| `dim_benchmark` | 8 | 8 | 0 |
| `fact_fees` | 122,197 | 122,197 | 0 |
| `fact_portfolio_snapshot` | 129,547 | 129,547 | 0 |
| `fact_transactions` | 298,772 | 298,572 | 200 |

Raw rows = clean rows + quarantined rows holds for every table. Audit files: `data/audit/cleaning_log.csv` (what was done and why), `data/audit/value_changes.csv` (every changed cell, old vs new), `data/audit/quarantine_fact_transactions_orphan_client.csv` (removed rows, all original columns + raw row number + reason).

## 2. Relationships between tables
Star-schema layout: dimensions `dim_advisor`, `dim_client`, `dim_security`, `dim_benchmark`, `dim_date`; facts `fact_fees` (client x month), `fact_portfolio_snapshot` (client x month), `fact_transactions` (one row per transaction). Ten ID-based and three date relationships; all resolve with **0 orphans** on the clean tables.

| Child column | Parent column | Cardinality | Key presence |
|---|---|---|---|
| `dim_client.advisor_id` | `dim_advisor.advisor_id` | many-to-one | required |
| `dim_security.benchmark_id` | `dim_benchmark.benchmark_id` | many-to-one | required |
| `fact_fees.client_id` | `dim_client.client_id` | many-to-one | required |
| `fact_fees.advisor_id` | `dim_advisor.advisor_id` | many-to-one | required |
| `fact_portfolio_snapshot.client_id` | `dim_client.client_id` | many-to-one | required |
| `fact_portfolio_snapshot.advisor_id` | `dim_advisor.advisor_id` | many-to-one | required |
| `fact_portfolio_snapshot.benchmark_id` | `dim_benchmark.benchmark_id` | many-to-one | required |
| `fact_transactions.client_id` | `dim_client.client_id` | many-to-one | required |
| `fact_transactions.advisor_id` | `dim_advisor.advisor_id` | many-to-one | required |
| `fact_transactions.security_id` | `dim_security.security_id` | many-to-one | nullable (blank for cash-flow rows) |
| `fact_fees.fee_date` | `dim_date.date` | many-to-one | required |
| `fact_portfolio_snapshot.snapshot_date` | `dim_date.date` | many-to-one | required |
| `fact_transactions.txn_date` | `dim_date.date` | many-to-one | required |

The three date relationships join to `dim_date.date` (text `YYYY-MM-DD`; `date_id` is the surrogate key). `fact_transactions.security_id` is blank by design for Deposit, Withdrawal and Advisory Fee rows, so the relationship must allow blank keys.

## 3. Column-type settings for a BI tool
Import every column as **text first**, then set these types explicitly (do not trust auto-detect): IDs as whole numbers, money and rates as decimals, dates as Date. Keep `zip_code` as **Text** (232 ZIP codes start with 0). `is_active` and `is_etf` hold the text `True`/`False`. The text `None` in `dim_advisor.certifications` is a real value ("no certification"), not a missing value - do not let the tool convert it to null. Empty cells (e.g. `sector` for ETFs, `risk_profile` when flagged) are genuine blanks.

**`dim_advisor`** (key: `advisor_id`)

| Column | BI type |
|---|---|
| `advisor_id` | Whole number |
| `first_name` | Text |
| `last_name` | Text |
| `region` | Text |
| `years_experience` | Whole number |
| `aum_target_mm` | Whole number |
| `certifications` | Text |

**`dim_client`** (key: `client_id`)

| Column | BI type |
|---|---|
| `client_id` | Whole number |
| `first_name` | Text |
| `last_name` | Text |
| `age` | Whole number |
| `city` | Text |
| `state` | Text |
| `zip_code` | Text (keep leading zeros) |
| `risk_profile` | Text |
| `client_tier` | Text |
| `primary_account_type` | Text |
| `initial_aum` | Decimal number |
| `client_since` | Date |
| `advisor_id` | Whole number |
| `is_active` | True/False (text 'True'/'False') |
| `flag_risk_profile_missing` | Whole number (0/1) |

**`dim_date`** (key: `date_id`)

| Column | BI type |
|---|---|
| `date_id` | Whole number |
| `date` | Date |
| `year` | Whole number |
| `quarter` | Whole number |
| `month` | Whole number |
| `month_name` | Text |
| `week_of_year` | Whole number |
| `day_of_week` | Text |
| `is_month_end` | Whole number (0/1) |
| `is_quarter_end` | Whole number (0/1) |
| `is_year_end` | Whole number (0/1) |
| `is_trading_day` | Whole number (0/1) |

**`dim_security`** (key: `security_id`)

| Column | BI type |
|---|---|
| `security_id` | Whole number |
| `ticker` | Text |
| `name` | Text |
| `asset_class` | Text |
| `sector` | Text |
| `benchmark_id` | Whole number |
| `is_etf` | True/False (text 'True'/'False') |
| `expense_ratio_bps` | Decimal number |

**`dim_benchmark`** (key: `benchmark_id`)

| Column | BI type |
|---|---|
| `benchmark_id` | Whole number |
| `name` | Text |
| `asset_class` | Text |
| `ticker_proxy` | Text |

**`fact_fees`** (key: `fee_id`)

| Column | BI type |
|---|---|
| `fee_id` | Whole number |
| `client_id` | Whole number |
| `advisor_id` | Whole number |
| `fee_date` | Date |
| `fee_type` | Text |
| `aum_basis` | Decimal number |
| `bps_charged` | Decimal number |
| `amount` | Decimal number |
| `flag_aum_basis_at_floor` | Whole number (0/1) |

**`fact_portfolio_snapshot`** (key: `snapshot_id`)

| Column | BI type |
|---|---|
| `snapshot_id` | Whole number |
| `client_id` | Whole number |
| `advisor_id` | Whole number |
| `benchmark_id` | Whole number |
| `snapshot_date` | Date |
| `year` | Whole number |
| `month` | Whole number |
| `aum` | Decimal number |
| `return_ytd` | Decimal number |
| `benchmark_return_ytd` | Decimal number |
| `active_alpha_ytd` | Decimal number |
| `cash_pct` | Decimal number |
| `account_type` | Text |
| `flag_return_ytd_outlier` | Whole number (0/1) |
| `flag_aum_at_floor` | Whole number (0/1) |

**`fact_transactions`** (key: `txn_id`)

| Column | BI type |
|---|---|
| `txn_id` | Whole number |
| `client_id` | Whole number |
| `advisor_id` | Whole number |
| `security_id` | Whole number |
| `txn_date` | Date |
| `txn_type` | Text |
| `shares` | Decimal number |
| `price` | Decimal number |
| `amount` | Decimal number |

## 4. Flag columns added (0/1; the original value is never changed)
| Column | Table | Rows flagged | Meaning |
|---|---|---:|---|
| `flag_return_ytd_outlier` | `fact_portfolio_snapshot` | 312 | `return_ytd` above +500% (40 clients). Return and AUM history disagree; exclude from averages |
| `flag_aum_at_floor` | `fact_portfolio_snapshot` | 420 | `aum` is exactly 1,000.00 - an upstream minimum; true AUM unknown |
| `flag_aum_basis_at_floor` | `fact_fees` | 386 | `aum_basis` is exactly 1,000.00 (same client-months as the flagged snapshots) |
| `flag_risk_profile_missing` | `dim_client` | 76 | `risk_profile` is blank; not filled because the evidence for "Balanced" may be circular |

## 5. Fixes applied (see `cleaning_log.csv` and `value_changes.csv`)
- **D01** 200 transactions quarantined: `client_id` not in `dim_client` (total $10,888,495).
- **D02** `fact_transactions.security_id` converted from `45.0` to `45` (text match with `dim_security` 0% -> 100%).
- **D05** negative `shares` on Buy rows converted to absolute value; `amount = shares x price` now holds on every row.
- **D03** `return_ytd` percent text (`9.28%`) converted to a decimal fraction (`0.0928`), reconciled to `benchmark_return_ytd + active_alpha_ytd`.
- **D04** `dim_client.state` full names standardized to USPS codes.

## 6. Known limitations (chosen not to fix, with reasons)
| Limitation | Size | Why it was left |
|---|---|---|
| Flagged but uncorrected returns above +500% | 312 rows | No other column gives the correct return; correcting would invent data |
| AUM floor at 1,000 | 420 snapshot / 386 fee rows | True AUM is unknown; value kept so snapshot and fee tables agree |
| Blank `risk_profile` | 76 clients | A wrong fill is worse than a visible blank; confirm with the advisor |
| Buy/Sell dated on weekends | 40,630 of 143,218 rows | Same share (~28%) for every transaction type, so it is a property of the whole extract; no source for the right date |
| Advisory fee debits (transactions) do not match `fact_fees` | $263,709,737 vs $204,675,583 | The tables disagree broadly and neither is known to be the source of truth |
| Snapshot months with no fee row | 7,350 | No evidence of what the fee should be; billing gaps can be real |
| `fee_type` changes month to month | 57.5% of steps | `amount` reconciles, but the label cannot be corrected; do not split revenue by fee type |
| Duplicated security names | 3 pairs | Different ids, tickers and attributes: distinct securities, not duplicates |
| One fee rate above 100 bps (100.38) | 1 row | The 100 bps ceiling was an assumption; the amount reconciles |
| Clients, benchmarks with no facts | 25 clients | Valid reference data; client counts differ between the dimension and the facts |
| Blank `sector`/`expense_ratio_bps`; blank `security_id`/`shares`/`price` on cash flows | structural | Blanks follow `is_etf` and the transaction type exactly; filling would invent data |
