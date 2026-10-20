# Wildcat Capital Data Cleaning Report

**To:** Portfolio Committee  **From:** Rose Mazzeo  **Date:** October 20, 2026
**Scope:** Eight warehouse tables (five dimension, three fact) · MIS3060 HW4

## 1. Executive summary

The Wildcat Capital data extract had never been checked, so we audited all eight tables with 594 automated checks; 36 failed (8 ERROR, 11 WARN, 17 INFO). Of 19 documented decisions, eight led to a repair, a quarantine or a flag. Ten findings were deliberately left alone because they reflect how the business records its data, or because the correct value cannot be determined from the data. One entry records the checks that passed.

The effect is concentrated in the transaction table. After cleaning, every one of the 13 table relationships (ten ID-based, three date-based) has zero orphan records. Transaction referential match rose from 81.95% to 100%, and type validity from 90.545% to 100%. 200 transactions worth $10,888,495 that could not be tied to any client were moved to a quarantine file, not deleted. For every table, raw rows equal clean rows plus quarantined rows, and all 198,257 changed values are logged cell by cell.

Clean does not mean complete. Four items were flagged and not corrected because the data does not support a correction: 312 implausible returns, 420 portfolio snapshots and 386 fee records pinned at exactly $1,000 of assets, and 76 clients with no risk profile. The committee should read those figures with the flags in view (section 5).

## 2. What was changed

| # | Issue | Table.column | Rows | Action | Proof the fix worked |
|---|---|---|---:|---|---|
| 1 | Transactions for clients that do not exist | fact_transactions.client_id | 200 | Quarantined ($10,888,495) | 0 orphans afterwards; 298,772 raw = 298,572 clean + 200 |
| 2 | Security IDs stored as text like "45.0" | fact_transactions.security_id | 197,044 | Converted to "45" | Match to dim_security 0% → 100% |
| 3 | Negative share counts on Buy trades | fact_transactions.shares | 835 | Sign corrected | amount = shares × price on every row |
| 4 | Returns stored as text like "9.28%" | fact_portfolio_snapshot.return_ytd | 300 | Converted to a decimal | Matches benchmark return + alpha (max difference 0.00005) |
| 5 | State names mixed with state codes | dim_client.state | 78 | Standardized to 2-letter codes | 100% valid codes |
| 6 | Returns above +500% | fact_portfolio_snapshot.return_ytd | 312 | Flagged, value unchanged | Flag count equals recount |
| 7 | Assets pinned at exactly $1,000 | snapshot aum / fee aum_basis | 420 / 386 | Flagged, value unchanged | Every flagged fee row sits on a flagged snapshot month |
| 8 | Blank risk profile | dim_client.risk_profile | 76 | Flagged, left blank | Flag count equals blank count |

Rows 2 and 3 show fewer rows than the raw audit (197,175 and 836) because 131 and 1 of those rows belonged to the 200 quarantined transactions.

## 3. Data quality scorecard, before and after

| Table | Measure | Raw | Clean |
|---|---|---:|---:|
| fact_transactions | Referential match | 81.95% | 100% |
| fact_transactions | Type validity | 90.545% | 100% |
| fact_transactions | Rule pass | 99.92% | 100% |
| dim_client | Rule pass | 99.69% | 100% |
| fact_portfolio_snapshot | Type validity | 99.981% | 100% |

The other five tables scored the same in both stages, and key uniqueness is 100% in all of them. Completeness did not change, because blanks were flagged and not filled. Rule pass covers natural business bounds and cross-table reconciliations; judgment thresholds (such as +500%) are reported separately and are not in the score.

## 4. Key judgment calls

**4.1 Quarantine the 200 orphan transactions.** The client IDs run from 2,702 to 3,192, each appears once, and none appears in any other table, so there is no client to attach them to. Guessing a client would invent data, and keeping them would break every client-level report. *Risk:* if these clients exist and were simply missing from the client extract, we understate transaction volume by $10.9 million (200 of 298,772 rows). *Mitigation:* the quarantine file keeps every column, so the rows can be restored.

**4.2 Flag the 312 extreme returns; do not correct them.** They belong to 40 clients, all Retail, and a return above 500% in a year is not plausible. But the supporting data contradicts the return: the affected accounts hold a median 47% of their starting assets. With no source to compute the correct figure, any "fix" would be a guess. The 500% cut-off is a judgment call: 472 rows exceed 200%, 373 exceed 300%, 312 exceed 500% and 261 exceed 1,000%, with no natural break. *Risk:* averages of return and alpha are unreliable until these rows are excluded or explained; too low a cut-off would hide genuine outperformance.

**4.3 Do not fill the 76 blank risk profiles.** 75 of the 76 clients use benchmark 3, which every one of the 757 "Balanced" clients also uses and no other profile uses, so "Balanced" is a tempting fill. But the system may simply assign benchmark 3 whenever the profile is missing, which would make the evidence circular. Risk profile drives suitability reporting, and a wrong fill is worse than a visible blank. *Risk:* 76 clients (3.01%) are blank in risk-profile reports; if "Balanced" was in fact correct, that group is under-reported. Confirming these with the advisors resolves it.

## 5. Limitations

- **Flagged, not corrected:** 312 extreme returns; 420 snapshot and 386 fee records at exactly $1,000 (92 clients; median return on those snapshots −94%); 76 blank risk profiles. The true values are unknown.
- **Fee totals disagree between tables.** In the raw extract, advisory-fee debits in the transaction table total $263.8 million against $204.7 million in the fee table (about $59 million apart), and 9,865 of 10,396 client-years differ by more than 5%. Neither table can be called the source of truth; revenue reports should state which table they use.
- **Weekend trades.** 40,649 of 143,311 Buy and Sell rows (28.4%) fall on a non-trading day, at the same rate for every transaction type, which points to the extract and not to individual errors. Do not analyze trading by weekday.
- **Fee type is unreliable.** The fee type changes in 57.5% of month-to-month steps for the same client, although amounts reconcile. Do not split revenue by fee type.
- **Missing fees.** 7,350 snapshot months (5.7%) have no fee record; the cause is unknown.
- **Unused clients.** 25 clients have no snapshots, fees or transactions, so client counts differ between the client list and the activity tables.

Full evidence for every decision is in `decision_log.md`; cell-level changes are in `data/audit/value_changes.csv`.

---
*AI-assisted report — reviewed for factual accuracy on October 20, 2026 by Rose Mazzeo*
