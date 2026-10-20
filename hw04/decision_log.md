# HW4 Decision Log — Wildcat Capital data cleaning
**MIS3060 Business Intelligence with AI** · Written before `02_clean.py` · Audit run: 2026-10-20 (`reports/dq_summary_raw.csv`, 594 checks: 36 FAIL, 558 PASS)

> **How to use this file.** This is the specification for `scripts/02_clean.py`. Each entry says what is wrong, what to do, how to prove the fix worked, and what could go wrong. When cleaning code is generated, it is generated *from these entries*, one transformation per entry, in the order in section 3. Evidence numbers come from `reports/dq_summary_raw.csv` and from verification queries run on the raw tables; finding IDs (F###) refer to that run.

## 1. Global rules (apply to every entry)
- Read every file as text: `dtype=str, keep_default_na=False`. Convert columns on purpose, never by parser default.
- Same file names, same columns. Added columns are 0/1 flags only, prefixed `flag_`.
- Raw files are never modified. Nothing is deleted silently: removed rows go to `data/audit/quarantine_*.csv`, and for every table **raw rows = clean rows + quarantined rows** (asserted).
- After each transformation: print rows affected, show a before/after check, and `assert` the after-state.
- Never invent data. Where a value cannot be corrected from other columns or tables, flag it.
- Counts quoted in the entries are from the raw audit. The cleaning script quarantines the 200 orphan transactions first, so some of its counts are slightly lower where rows belonged to that set (for example 835 Buy rows corrected instead of 836, and 197,044 `security_id` values converted instead of 197,175).

## 2. Summary of decisions

| ID | Table.column | Issue | Decision |
|---|---|---|---|
| D01 | fact_transactions.client_id | 200 orphan clients | **Quarantine** 200 rows |
| D02 | fact_transactions.security_id | stored as `45.0` | **Convert** to integer text |
| D03 | fact_portfolio_snapshot.return_ytd | 300 values like `9.28%` | **Convert** to decimal fraction |
| D04 | dim_client.state | 78 full state names | **Standardize** to USPS codes |
| D05 | fact_transactions.shares | 836 negative shares on Buy | **Convert** sign (absolute value) |
| D06 | fact_portfolio_snapshot.return_ytd / active_alpha_ytd | 312 returns above +500% | **Flag**, do not change |
| D07 | fact_portfolio_snapshot.aum, fact_fees.aum_basis | pile-up at exactly 1,000 | **Flag**, do not change |
| D08 | dim_client.risk_profile | 76 blanks | **Flag**, do not fill |
| D09 | dim_security.sector, expense_ratio_bps | blanks follow `is_etf` | **Leave as is** (structure) |
| D10 | fact_transactions.security_id, shares, price | blank on cash-flow rows | **Leave as is** (structure) |
| D11 | dim_advisor.certifications | literal text `None` | **Leave as is** |
| D12 | dim_security.name | 3 duplicated names | **Leave as is** |
| D13 | fact_fees.bps_charged | one value 100.38 | **Leave as is** |
| D14 | dim_client / dim_benchmark | members with no facts | **Leave as is** |
| D15 | fact_transactions.txn_date | 28% of trades on weekends | **Leave as is**, document |
| D16 | fact_transactions vs fact_fees | advisory-fee totals disagree | **Leave as is**, document |
| D17 | fact_portfolio_snapshot | 7,350 months with no fee row | **Leave as is**, document |
| D18 | fact_fees.fee_type | changes month to month | **Leave as is**, document |
| D19 | all tables | checks that passed | **No action** |

Added flag columns: `dim_client.flag_risk_profile_missing`, `fact_portfolio_snapshot.flag_return_ytd_outlier`, `fact_portfolio_snapshot.flag_aum_at_floor`, `fact_fees.flag_aum_basis_at_floor`.

---

## 3. Execution order for `02_clean.py` (and why)
1. **D01 quarantine orphan transactions first.** Later steps and the foreign-key re-check then run on the rows that are staying. Expect `fact_transactions`: 298,772 raw = 298,572 clean + 200 quarantined.
2. **D02 normalize `security_id`** (needs to happen before any join to `dim_security`). Counts after step 1 will be lower than the raw 197,175 because 131 of the quarantined rows are Buy/Sell/Dividend rows that carry a security.
3. **D05 fix negative Buy shares** (then reconcile `amount = shares × price`).
4. **D03 convert `return_ytd` percent text** (then reconcile with `benchmark_return_ytd + active_alpha_ytd`). Must come before D06 because D06's threshold only works on numbers.
5. **D04 standardize state codes.**
6. **D06, D07, D08 add flag columns** (flags are computed from the already-repaired values).
7. Re-run the full audit on the clean tables and prove `raw = clean + quarantined` for all eight tables.

---

## 4. Defects we act on

### D01 — Orphan transactions (client does not exist)
| Field | Entry |
|---|---|
| **Table / column** | `fact_transactions.client_id` |
| **Evidence** | 200 rows (0.067%) have a `client_id` that is not in `dim_client` (F007). IDs range 2,702–3,192 while `dim_client` ends at 2,525; every orphan ID appears exactly once, none appears in `fact_fees` or `fact_portfolio_snapshot`, and all have a valid `advisor_id`. Types: Buy 58, Dividend 38, Sell 35, Deposit 25, Advisory Fee 24, Withdrawal 20; total amount $10,888,495; dates 2020-02-18 to 2024-12-19. |
| **Dimension violated** | Referential Integrity |
| **Decision** | **Quarantine** all 200 rows to `data/audit/quarantine_fact_transactions_orphan_client.csv` (all raw columns plus a `reason` column). Remove from the clean table. |
| **Justification** | The transaction cannot be tied to any client, so it cannot appear in any client-level report, and it would break the transaction→client relationship in the Power BI star schema (assignment 5). We cannot repair the key: the IDs are not near any existing client ID and do not appear in any other table, so guessing a client would be inventing data. Keeping the rows in a quarantine file preserves them and lets us prove nothing was lost. |
| **Risk** | If these are real clients who were simply missing from the client extract, removing them understates firm-wide transaction volume by $10.9M (200 of 298,772 rows). Mitigation: the quarantine file holds every column, so the rows can be restored if the missing clients are found. |
| **Verification** | `assert` 0 orphan `client_id` in the clean table; `assert 298,772 == 298,572 + 200`; `assert` quarantine rows are exactly the raw rows whose `client_id` is not in `dim_client`. |

### D02 — `security_id` stored in float format
| Field | Entry |
|---|---|
| **Table / column** | `fact_transactions.security_id` |
| **Evidence** | 197,175 of 298,772 rows hold values like `45.0` (F004). Compared as text against `dim_security.security_id` the match rate is **0.0%** (F008). After removing the trailing `.0` the match rate is 100.0% (0 orphans). No value has a decimal part other than `.0`. |
| **Dimension violated** | Validity, Consistency, Referential Integrity |
| **Decision** | **Convert** to integer text (`45.0` → `45`). Keep the 101,597 blanks as blank (see D10). |
| **Justification** | The value is an ID, not a quantity; the `.0` is a formatting artifact of the source system. Left alone, every join from transactions to securities silently returns nothing. The conversion loses no information because every value is a whole number. |
| **Risk** | Very low. If a value had a real decimal part, trimming `.0` would not apply to it — the code only trims an exact `.0` and asserts nothing else changes. |
| **Verification** | Before: 0% of non-blank values match `dim_security`. After: `assert` 100% match, `assert` no value contains a `.`, `assert` blank count unchanged. |

### D03 — Percent text in a numeric column
| Field | Entry |
|---|---|
| **Table / column** | `fact_portfolio_snapshot.return_ytd` |
| **Evidence** | 300 of 129,547 rows (0.232%) are text like `9.28%` (F002, F003); the other 129,247 rows are decimal fractions such as `0.082790`. The 300 rows are spread across all five years and all five account types. |
| **Dimension violated** | Validity, Consistency |
| **Decision** | **Convert**: strip the `%`, divide by 100, store as a decimal fraction. Log every change in `value_changes.csv` (old text → new number). |
| **Justification** | A BI tool treats the whole column as text if even one `%` row remains, so every return calculation fails. The scale is not assumed: dividing by 100 makes `return_ytd` match `benchmark_return_ytd + active_alpha_ytd` on all 300 rows (max difference 0.00005, which is the rounding limit of a 2-decimal percent). Treating the value as already in percent points would be off by up to 1,158. |
| **Risk** | If a few of the 300 had a different true value, the reconciliation tolerance (±0.00005) could hide an error of that size — immaterial for a return. |
| **Verification** | `assert` all 300 converted values satisfy `abs(return_ytd − (benchmark_return_ytd + active_alpha_ytd)) ≤ 0.000051` (the observed maximum is about 0.00005, the rounding limit of a 2-decimal percent, plus 6-decimal rounding in the two reference columns); `assert` no `%` remains; the column then parses 100% as float. |

### D04 — State: codes mixed with full names
| Field | Entry |
|---|---|
| **Table / column** | `dim_client.state` |
| **Evidence** | 78 of 2,525 rows (3.1%) hold a full name instead of a 2-letter code (F001, F009): Pennsylvania 25, Florida 15, New York 14, New Jersey 13, California 5, Illinois 4, Texas 2. All seven states are already present as codes in the same column. |
| **Dimension violated** | Consistency, Validity |
| **Decision** | **Standardize** to USPS codes with an explicit seven-entry mapping (PA, FL, NY, NJ, CA, IL, TX). Log all 78 changes. |
| **Justification** | Grouping by state in a report would show "PA" and "Pennsylvania" as two states. The mapping is unambiguous, so no information is invented. |
| **Risk** | Low. Zip codes cannot confirm the state (zip prefixes are unrelated to state in this extract), so the fix rests on the name→code mapping alone. A mapping typo would be caught by the assertion below. |
| **Verification** | `assert` 100% of `state` values are in the USPS list afterwards; per-state totals equal raw code count + raw full-name count (e.g. PA = 414 + 25 = 439). |

### D05 — Negative shares on Buy rows
| Field | Entry |
|---|---|
| **Table / column** | `fact_transactions.shares` (with `amount`, `price`) |
| **Evidence** | 836 rows have negative `shares` (F006); all are `Buy` (spread over 692 clients). No Sell, Dividend or other row is ever negative. For all 836, `amount = shares × price` fails with the sign but matches within $1.00 using the absolute value (F005); 0 rows fail the absolute-value test. `amount` is positive on every row. |
| **Dimension violated** | Consistency, Accuracy/Plausibility |
| **Decision** | **Convert**: set `shares = abs(shares)` on those Buy rows. Log all changes. |
| **Justification** | In this table the transaction type carries the direction (Buy vs Sell) and shares are otherwise always positive, so a negative Buy is a sign error, not a different kind of event. The stored `amount` is already right; only the share count disagrees. Position and cost-basis calculations that sum shares would be wrong without this fix. |
| **Risk** | If the negative sign was intended (e.g. a reversed trade), then positive shares would overstate holdings. Mitigation: `amount` is positive for these rows and reconciles to the absolute value, which points to sign noise rather than a reversal. |
| **Verification** | `assert` no negative `shares` remain; `assert` `abs(shares × price − amount) ≤ 1.00` for every row with shares and price; the number of rows changed equals the number of negative Buy rows present after D01 (≤ 836; the script prints the actual count). |

### D06 — Returns above +500%
| Field | Entry |
|---|---|
| **Table / column** | `fact_portfolio_snapshot.return_ytd` and `active_alpha_ytd` |
| **Evidence** | After D03 conversion, **312** rows have `return_ytd` > 5.0 (500%), belonging to 40 clients, all Retail (the audit's 311 excluded the 300 text rows). Sensitivity: >200% 472 rows, >300% 373, >500% 312, >1000% 261 — no natural gap. `active_alpha_ytd` > 6 on 285 rows (F011). These accounts are **not** tiny: median AUM $42.5k (max $200k); only 6% are under $10k and none is at the 1,000 floor. Their AUM is a median 47% of the client's initial AUM; client 81 fell from about $75k to $27k in Oct 2020 yet shows a later `return_ytd` of 806%. The return and the AUM history contradict each other. |
| **Dimension violated** | Accuracy/Plausibility, Consistency |
| **Decision** | **Flag** with `flag_return_ytd_outlier` = 1 where converted `return_ytd` > 5.0. Do not change the value. `active_alpha_ytd` is not changed or flagged separately: it equals `return_ytd − benchmark_return_ytd` on every row (0 mismatches), so the same flag covers it. |
| **Justification** | A gain of more than 500% in a year on a Retail account of this size is not plausible, but we cannot work out the correct return from the other columns, because they disagree with it. Correcting it would be guessing. Flagging lets an analyst exclude these rows from averages without us discarding data. The 500% threshold is a judgment call (see sensitivity above). |
| **Risk** | Too low a threshold hides real extreme performance; too high lets bad values distort averages. Averages of `return_ytd` and alpha across the book are unreliable until these 312 rows are excluded or explained. Returns below −90% (498 rows, 249 of them at the AUM floor) are *not* flagged: they are consistent with AUM having collapsed. |
| **Verification** | `assert` flagged count equals the count of converted `return_ytd` > 5.0; `assert` no flagged row has changed value versus the raw file (apart from D03). |

### D07 — AUM pile-up at exactly 1,000
| Field | Entry |
|---|---|
| **Table / column** | `fact_portfolio_snapshot.aum` (420 rows), `fact_fees.aum_basis` (386 rows) |
| **Evidence** | No value is below 1,000 in either column (F015, F016). 420 snapshot rows are *exactly* 1,000.00, compared with 405 rows across the whole next $100 (1,000–1,100): a minimum applied upstream. 92 clients are affected, often for consecutive months (median 4, max 20). Median return on these rows is −94%. The fee table matches the snapshot on all 386 shared rows (`aum_basis = aum`), so the two tables agree. |
| **Dimension violated** | Accuracy/Plausibility |
| **Decision** | **Flag**: `flag_aum_at_floor` (snapshot) and `flag_aum_basis_at_floor` (fees) = 1 where the value is exactly 1,000. Do not change the values. |
| **Justification** | The true AUM of these accounts is unknown (it may be lower than 1,000), so the real number cannot be restored. Leaving the value and flagging it keeps the tables consistent with each other and lets AUM totals, fee-rate analysis and returns exclude the floor rows where it matters. |
| **Risk** | Totals include a small amount of possibly floor-inflated AUM (420 rows × $1,000 = $0.42M in total, immaterial to firm totals but material to per-account returns). Fee amounts and returns on floor rows are not meaningful. |
| **Verification** | `assert` flag count = 420 / 386 (before any quarantine, since neither table loses rows); `assert` flagged rows have `aum = 1000`; `assert` the values are unchanged from raw. |

### D08 — Blank risk profile
| Field | Entry |
|---|---|
| **Table / column** | `dim_client.risk_profile` |
| **Evidence** | 76 of 2,525 blank (3.01%) (F013). 75 of them have snapshots and all 75 use benchmark 3. Among the 2,449 clients with a profile, each profile maps to exactly one benchmark and benchmark 3 is *only* ever used by "Balanced" (757 of 757). Client 2510 has no facts at all. Blanks occur in all tiers (Retail 49, HNW 18, UHNW 9). |
| **Dimension violated** | Completeness |
| **Decision** | **Flag**: `flag_risk_profile_missing` = 1 on all 76. Leave the value blank. Do **not** fill with "Balanced". |
| **Justification** | The benchmark pattern suggests "Balanced", but it may not be independent evidence: if the system assigned benchmark 3 as a default when the profile was missing, the blanks could be any profile. A risk profile drives suitability and reporting, so a wrong fill is worse than a visible blank. A flag lets the committee see exactly which 76 need to be confirmed with the advisor. |
| **Risk** | Reports by risk profile exclude or group 76 clients (3%) as "blank". If "Balanced" was in fact correct, those clients are under-reported in that group. |
| **Verification** | `assert` flag count = number of blank `risk_profile` values = 76; `assert` no `risk_profile` value was changed. |

---

## 5. Looks odd, but we leave it alone

### D09 — Blank sector and expense ratio on securities
| Field | Entry |
|---|---|
| **Table / column** | `dim_security.sector`, `dim_security.expense_ratio_bps` |
| **Evidence** | 219 blank sectors (43.8%) and 281 blank expense ratios (56.2%) (F022, F023). Blank `sector` ⇔ `is_etf = True` and blank `expense_ratio_bps` ⇔ `is_etf = False`; **0 rows** break either rule. |
| **Dimension violated** | None. This is structure, not a defect (Completeness would flag it). |
| **Decision** | **Leave as is.** |
| **Justification** | ETFs have no single sector; non-ETF securities (stocks, bonds) have no expense ratio. The blanks are exact, not random. Filling them would invent data. |
| **Risk** | A BI tool will show "(Blank)" for ETFs in sector charts; document this in `README_clean.md` as an expected category. |

### D10 — Blank security, shares and price on cash-flow transactions
| Field | Entry |
|---|---|
| **Table / column** | `fact_transactions.security_id`, `shares`, `price` |
| **Evidence** | 101,597 rows (34.0%) are blank in all three columns (F024–F026, F033). They are exactly the Deposit (35,981), Withdrawal (29,850) and Advisory Fee (35,766) rows; every Buy/Sell/Dividend row has all three present (0 exceptions). |
| **Dimension violated** | None (structure). |
| **Decision** | **Leave as is.** Keep the foreign key nullable. |
| **Justification** | A deposit or fee debit involves no security, share count or price. Filling them would be wrong. |
| **Risk** | In Power BI, the relationship to `dim_security` must allow blank keys. Documented in `README_clean.md`. |

### D11 — Literal "None" in certifications
| Field | Entry |
|---|---|
| **Table / column** | `dim_advisor.certifications` |
| **Evidence** | 6 of 25 advisors have the text `None` (F020); it is one of the six expected values. |
| **Dimension violated** | None. |
| **Decision** | **Leave as is.** |
| **Justification** | It means "no certification", a legitimate category, and it is not a missing value. This is exactly the value `pd.read_csv` would have turned into `NaN` by default. |
| **Risk** | If a BI tool imports the column and treats "None" as null, it will mis-count advisors without certifications. Documented as a column-type note. |

### D12 — Duplicated security names
| Field | Entry |
|---|---|
| **Table / column** | `dim_security.name` |
| **Evidence** | 3 names appear twice (F014): "Jones Inc Fund", "Davis PLC Fund", "Graham Group Inc.". In each pair the ticker, security_id, asset class or sector, benchmark and (for ETFs) expense ratio differ. All six securities are traded (276–408 transactions each). |
| **Dimension violated** | Uniqueness (apparent only). |
| **Decision** | **Leave as is.** |
| **Justification** | The IDs and tickers are unique and the attributes differ, so these are distinct securities that share a name, not duplicate rows. Merging them would corrupt the trade history of both. |
| **Risk** | Name-based lookups or visuals could confuse them; users should select by ticker. |

### D13 — One fee rate of 100.38 bps
| Field | Entry |
|---|---|
| **Table / column** | `fact_fees.bps_charged` |
| **Evidence** | One row (fee 68809) has 100.38 bps (F010); the next highest values are 99.88, 99.54, 99.18. Its `amount` of $90.68 equals `aum_basis × bps / 10,000 / 12` exactly. |
| **Dimension violated** | Accuracy/Plausibility (only against my own 100 bps assumption). |
| **Decision** | **Leave as is.** |
| **Justification** | The 100 bps ceiling was my assumption, not a rule from the source; the value sits in a continuous distribution and the amount reconciles. |
| **Risk** | If the firm's maximum fee really is 100 bps, one fee is overcharged by about $0.34. |

### D14 — Dimension members with no facts
| Field | Entry |
|---|---|
| **Table / column** | `dim_client` (IDs 2501–2525), `dim_benchmark` (IDs 2, 4, 5, 6, 7 unused in snapshots; 6, 8 unused by securities) |
| **Evidence** | 25 clients (0.99%) appear in no fee, snapshot or transaction row (F030–F032, F034): 24 active, signed 2015–2022, $49.1M initial AUM, all with valid advisors. 5 of 8 benchmarks are not used by any snapshot (F028–F029). |
| **Dimension violated** | None (reverse integrity, not a broken join). |
| **Decision** | **Leave as is.** |
| **Justification** | A dimension may contain members with no activity (new clients, benchmarks kept for later). Deleting them would remove valid reference data. |
| **Risk** | Client counts from the dimension (2,525) exceed clients with activity (2,500). State which count each report uses. |

### D15 — Trades on weekends
| Field | Entry |
|---|---|
| **Table / column** | `fact_transactions.txn_date` |
| **Evidence** | 40,649 of 143,311 Buy/Sell rows (28.4%) fall on a day flagged non-trading (F018); all of them are weekends. The share is the same for every transaction type (Buy 28.4%, Sell 28.3%, Deposit 28.1%, Withdrawal 28.2%, Dividend 28.8%, Advisory Fee 28.9%), close to the 2/7 you get from dates spread evenly over the week. |
| **Dimension violated** | Accuracy/Plausibility |
| **Decision** | **Leave as is**; list under known limitations. |
| **Justification** | Dates look evenly distributed across the calendar regardless of transaction type, so this is a property of the whole extract, not isolated bad rows, and there is no information that says which date is right. Flagging 40k rows would add noise, and changing dates would invent data. |
| **Risk** | Analysis of trading by weekday, or reconciliation to market prices, will be misleading. |

### D16 — Advisory fee debits do not match the fee table
| Field | Entry |
|---|---|
| **Table / column** | `fact_transactions` (Advisory Fee) vs `fact_fees` |
| **Evidence** | Total Advisory Fee debits are $263.8M vs $204.7M in `fact_fees` (F019). On a per-client-per-year basis, 94.9% (9,865 of 10,396) are more than 5% apart. The transaction table has 35,766 fee debits vs 32,370 "Advisory" rows in the fee table. |
| **Dimension violated** | Consistency, Accuracy |
| **Decision** | **Leave as is**; list under known limitations. |
| **Justification** | The tables disagree broadly, not on a handful of rows, and nothing tells us which is the source of truth. Overwriting either would be a guess. |
| **Risk** | Fee revenue reported from the two tables will differ by about $59M; the committee must be told which table each figure comes from. |

### D17 — Snapshot months with no fee row
| Field | Entry |
|---|---|
| **Table / column** | `fact_portfolio_snapshot` vs `fact_fees` |
| **Evidence** | 7,350 snapshots (5.7%) have no matching fee row (F036). Every fee row *does* have a snapshot with the same AUM (0 mismatches). The missing-fee months are not explained by size (median AUM $438k vs $485k overall; 0.5% at the floor), year, or first/last month of the client (2.4% / 1.3%). |
| **Dimension violated** | Completeness (possible) |
| **Decision** | **Leave as is**; list under known limitations. |
| **Justification** | There is no evidence of what the fee should have been, and billing gaps can be real. |
| **Risk** | Fee revenue could be understated for these months; don't annualize fees from this table without checking. |

### D18 — Fee type changes from month to month
| Field | Entry |
|---|---|
| **Table / column** | `fact_fees.fee_type` |
| **Evidence** | Each client-month has exactly one fee row, and its type changes in 57.5% of month-to-month transitions; 2,292 of 2,500 clients are charged all four types at some point. `bps_charged` is stable within a client (median std 3.0 bps) and follows tier (Retail avg 88, HNW 65, UHNW 38). |
| **Dimension violated** | Consistency (possible) |
| **Decision** | **Leave as is**; list under known limitations. |
| **Justification** | The `amount` reconciles for every row, so the money is right; the `fee_type` label cannot be corrected without a source. |
| **Risk** | Revenue split by fee type is unreliable; use total fees by client or month instead. |

---

## 6. Checks that passed — no action (D19)
All of the following were tested on the raw tables and **passed with 0 violations**, so they are deliberately left untouched (evidence in `dq_summary_raw.csv`, `status = PASS`):
- Primary keys are unique and never blank in all eight tables; no exact duplicate rows ignoring the key; no near-duplicate clients, advisors, fees, snapshots or transactions.
- All other foreign keys resolve (client→advisor, security→benchmark, fees and snapshots→client/advisor/benchmark, transactions→advisor, all three date relationships). The only breaks are D01 and D02.
- `dim_date` is complete (1,827 days, no gaps) and every derived column (year, month, quarter, week, day name, month/quarter/year-end flags) agrees with its date.
- `fact_fees.amount = aum_basis × bps / 10,000 / 12` (within one cent) on all 122,197 rows; `aum_basis` equals the snapshot AUM for the same client-month on every row.
- `active_alpha_ytd = return_ytd − benchmark_return_ytd` on every numeric row; `year`/`month` match `snapshot_date`.
- Fact `advisor_id` equals the client's advisor of record in all three fact tables; snapshot `account_type` equals the client's `primary_account_type`.
- Client tier agrees with `initial_aum` (Retail < $500k, HNW < $5M, UHNW above); no client was under 18 at account opening.
- No activity is dated before the client's `client_since` month (a day-level comparison would falsely flag 858 fees and 930 snapshots, because they are dated the 1st of the month).
- ZIP codes are 5 digits with leading zeros preserved (232 start with 0) — the reason for reading as text.
- No leading/trailing whitespace, control characters or case variants in any column.

---

## 7. Known limitations to carry into `README_clean.md` and the business report
D09–D10 (blank categories), D11 (literal "None"), D15 (weekend trades), D16 (fee totals disagree between tables), D17 (missing fee months), D18 (unreliable fee type), plus the effect of D06/D07/D08 (flagged, not corrected).
