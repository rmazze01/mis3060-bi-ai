# HW6 Measure Library (Part A)

All measures live in the `_Measures` table of `powerbi/hw06.pbix`. Base measures from the ICEs:

```DAX
Total Fees = SUM ( fact_fees[amount] )
```
```DAX
Net Flows = CALCULATE ( SUM ( fact_transactions[amount] ), fact_transactions[txn_type] = "Deposit" ) - CALCULATE ( SUM ( fact_transactions[amount] ), fact_transactions[txn_type] = "Withdrawal" )
```

`fact_portfolio_snapshot` has one row per client per month (60 snapshots, 2020-01-01 to 2024-12-01). `aum` is a balance and `active_alpha_ytd` is year-to-date. Pattern labels: **SUM** (a flow, safe to add), **last balance** (a stock, read at the last snapshot in the filter), **recompute-and-weight** (a ratio rebuilt from its parts, never summed or averaged).

## 0. AUM (naive SUM) (currency, 0 decimals)
```DAX
AUM (naive SUM) = SUM ( fact_portfolio_snapshot[aum] )
```
- **Pattern:** SUM, which is wrong for a balance. It is kept only to show the trap and is not on any report.
- **Meaning for a manager:** It adds 60 monthly balances together (about $566.7B against a real $12.7B), so it overstates AUM roughly 45 times.

## 1. Ending AUM (currency, 2 decimals)
```DAX
Ending AUM = CALCULATE ( SUM ( fact_portfolio_snapshot[aum] ), LASTNONBLANK ( dim_date[date], CALCULATE ( SUM ( fact_portfolio_snapshot[aum] ) ) ) )
```
- **Pattern:** last balance.
- **Meaning for a manager:** How much Wildcat manages at the most recent snapshot in whatever period is selected.

## 2. Ending Clients (whole number)
```DAX
Ending Clients = CALCULATE ( DISTINCTCOUNT ( fact_portfolio_snapshot[client_id] ), LASTNONBLANK ( dim_date[date], CALCULATE ( SUM ( fact_portfolio_snapshot[aum] ) ) ) )
```
- **Pattern:** last balance (a distinct count at the last snapshot).
- **Meaning for a manager:** How many clients Wildcat serves at the end of the period, not how many appeared at any time.

## 3. Avg AUM per Client (currency, 0 decimals)
```DAX
Avg AUM per Client = DIVIDE ( [Ending AUM], [Ending Clients] )
```
- **Pattern:** recompute-and-weight (a ratio rebuilt from Ending AUM and Ending Clients).
- **Meaning for a manager:** The typical relationship size, which shows whether growth comes from bigger accounts or more clients.

## 4. Ending AUM LY and AUM YoY % (currency, 0 decimals; percentage, 2 decimals)
```DAX
Ending AUM LY = CALCULATE ( [Ending AUM], SAMEPERIODLASTYEAR ( dim_date[date] ) )
```
```DAX
AUM YoY % = DIVIDE ( [Ending AUM] - [Ending AUM LY], [Ending AUM LY] )
```
- **Pattern:** last balance, shifted one year back. The YoY ratio is recomputed from the two balances.
- **Meaning for a manager:** How much the book grew over the last year, including market gains and net new money.

## 5. Ending AUM PM and AUM MoM % (currency, 0 decimals; percentage, 2 decimals)
```DAX
Ending AUM PM = CALCULATE ( [Ending AUM], DATEADD ( dim_date[date], -1, MONTH ) )
```
```DAX
AUM MoM % = DIVIDE ( [Ending AUM] - [Ending AUM PM], [Ending AUM PM] )
```
- **Pattern:** last balance, shifted one month back. The MoM ratio is recomputed from the two balances.
- **Meaning for a manager:** The month-to-month change in the book, useful for spotting sudden swings.

## 6. Avg Monthly AUM (currency, 0 decimals)
```DAX
Avg Monthly AUM = DIVIDE ( SUM ( fact_portfolio_snapshot[aum] ), DISTINCTCOUNT ( fact_portfolio_snapshot[snapshot_date] ) )
```
- **Pattern:** recompute-and-weight (the sum of balances divided by the number of snapshot dates).
- **Meaning for a manager:** The average size of the book over the period, which is the right base for judging fees earned during that period.

## 7. Fee Yield (bps) (decimal, 2 decimals)
```DAX
Fee Yield (bps) = DIVIDE ( [Total Fees] * 12 * 10000, SUM ( fact_portfolio_snapshot[aum] ) )
```
- **Pattern:** SUM of fees (a flow) over the sum of monthly balances, recomputed as a ratio. It uses two fact tables.
- **Meaning for a manager:** Annualized fees earned per dollar of AUM, so a falling yield means the firm earns less on each dollar it manages.

## 8. Organic Growth Rate (percentage, 2 decimals)
```DAX
Organic Growth Rate = DIVIDE ( [Net Flows], [Ending AUM LY] )
```
- **Pattern:** SUM of net flows (a flow) over last year's ending balance (last balance), recomputed as a ratio.
- **Meaning for a manager:** Growth from clients adding or withdrawing money, separate from market performance.

## 9. AUM-Weighted Alpha (percentage, 2 decimals)
```DAX
AUM-Weighted Alpha = CALCULATE ( DIVIDE ( SUMX ( fact_portfolio_snapshot, fact_portfolio_snapshot[aum] * fact_portfolio_snapshot[active_alpha_ytd] ), SUMX ( fact_portfolio_snapshot, fact_portfolio_snapshot[aum] ) ), fact_portfolio_snapshot[is_return_suspect] = 0, LASTNONBLANK ( dim_date[date], CALCULATE ( SUM ( fact_portfolio_snapshot[aum] ) ) ) )
```
- **Pattern:** recompute-and-weight. Alpha is weighted by AUM at the last snapshot, with suspect returns excluded.
- **Meaning for a manager:** How much clients' portfolios beat their benchmarks, with larger accounts counting more.

## 10. Alpha Signal (text)
```DAX
Alpha Signal = VAR Alpha = [AUM-Weighted Alpha] RETURN SWITCH ( TRUE (), ISBLANK ( Alpha ), BLANK (), Alpha >= 0.02, "Outperforming", Alpha <= -0.02, "Lagging", "In line" )
```
- **Pattern:** recompute-and-weight (a label derived from measure 9).
- **Meaning for a manager:** A quick read on whether a slice is beating, trailing or matching its benchmarks, with a 2% band around zero.

## 11. Top 10 Client Share (percentage, 2 decimals)
```DAX
Top 10 Client Share = DIVIDE ( SUMX ( TOPN ( 10, VALUES ( dim_client[client_id] ), [Ending AUM], DESC ), [Ending AUM] ), [Ending AUM] )
```
- **Pattern:** last balance, recomputed within the current filter. TOPN picks the 10 largest clients inside that filter.
- **Meaning for a manager:** How concentrated the book is in a handful of clients, which is a measure of revenue risk.

## Report page

The **Measures** page of `powerbi/hw06.pbix` has the four summary measures as single-measure tables (see `README.md`), a table by `dim_date[year]`, and a table by `dim_client[client_tier]` with a visual-level filter for 2024.

## Part C: design questions

All numbers below were computed in pandas from the Wildcat Capital Clean CSVs. Answer (a) was also checked in Power BI DAX query view.

### (a) Ending AUM versus the SUMX version, no filters

`Ending AUM` is **$12,729,572,078.86**. `SUMX ( VALUES ( dim_client[client_id] ), [Ending AUM] )` is **$13,149,297,713.80**, which is **$419,725,634.94** more. Power BI and pandas give the same two numbers.

`Ending AUM` reads one date, the last snapshot in the filter (2024-12-01), and adds every balance on it. Inside `SUMX`, each client is its own filter context, so `LASTNONBLANK` finds that client's own last snapshot. The 175 clients who left before December 2024 (13 last appear in 2022, 162 in 2023) each add their final balance, and those balances total exactly $419,725,634.94. The 2,325 clients still active contribute the same either way.

`Ending AUM` answers "How much do we manage today?" because a departed client's old balance is no longer managed assets. The SUMX version counts money that left the firm.

*Limitation:* "absent from the December 2024 snapshot" is treated as "left the firm." This agrees with `dim_client[is_active]` (175 inactive, 2,325 active), but the data gives no departure date or reason.

### (b) Fee Yield (bps) versus the ICE 9 Effective Fee Rate, 2024

The ICE 9 measure is `DIVIDE ( [Total Fees] * 12 * 10000, SUM ( fact_fees[aum_basis] ) )`. For 2024 it gives **45.53 bps**, and `Fee Yield (bps)` gives **43.15 bps**. The numerator is identical ($48,714,005.93 in fees), so the **2.38 bps gap comes entirely from the denominator**:

| | Denominator | Result |
|---|---|---|
| Effective Fee Rate | $128,385,303,527.10 (`fact_fees[aum_basis]`) | 45.53 |
| Fee Yield | $135,459,843,783.73 (`fact_portfolio_snapshot[aum]`) | 43.15 |

The $7,074,540,256.63 difference is the AUM of **1,684 of the 27,900 client-months (6.0%) that have a 2024 snapshot but no fee row**. Where a fee row exists, `aum_basis` equals the snapshot `aum` exactly (maximum difference 0.00, and no client-month has duplicate fee rows), and dividing by snapshot AUM on only the matched rows gives 45.53 again. The missing rows are spread across all months (91 to 172 a month), all tiers (Retail 1,054, HNW 472, UHNW 158) and 1,082 different clients.

This reveals that `fact_fees` does not cover every client-month on the snapshot. The ICE 9 rate silently drops uncovered AUM from its denominator, and Fee Yield keeps it.

*Limitation:* the data cannot say whether those months were fee-free or unrecorded. If unrecorded, the true yield is higher than 43.15 and the ICE 9 figure may be closer. If truly fee-free, 43.15 is the better measure of earnings per dollar managed. Billing would have to confirm.

### (c) Why read alpha only at the last snapshot, and why exclude suspect returns

`active_alpha_ytd` is year-to-date, so it is cumulative within a year and resets each January. The January value covers one month and the December value covers twelve, so averaging or pooling several months mixes incomparable periods and counts the same performance repeatedly. For 2024 the weighted alpha rises from about -0.01% in January to 1.45% in December, and pooling all 12 months gives only 0.32%. The last snapshot is the one point where each client's value covers the whole year.

At the December 2024 snapshot, 148 of 2,325 rows (6.4%) are flagged `is_return_suspect = 1`. They hold just $15.5M, 0.12% of AUM, but their alpha runs up to **+7,134%**, against a range of about -50% to +50% for the other rows.

| Same rows (2,177 non-suspect), December 2024 | Alpha |
|---|---:|
| AUM-weighted (the measure) | 1.45% |
| Simple mean of `active_alpha_ytd` | 0.88% |
| Weighted, suspects included | 1.67% |
| Simple mean, suspects included | 15.56% |

The simple mean on the same rows is 0.88%. The weighted value with suspects included is 1.67%. Weighting is robust, since the suspects are tiny in dollars and only move it 0.22 points, but the simple mean explodes to 15.56%. The weighted value also differs from the simple mean on clean rows (1.45% versus 0.88%) because larger clients had higher alpha.

*Limitations:* the data does not say why a return was flagged, so excluding them assumes they are errors, and a real extreme return would be dropped too. Weighting uses the year-end balance, not the average balance during the year. The signal is "In line" either way (1.45% or 1.67%), because the "Outperforming" band is 2%.

### (d) Organic growth by tier, 2024

| Tier | Organic Growth | AUM YoY % | Net flows | AUM increase | Flows' share of increase |
|---|---:|---:|---:|---:|---:|
| HNW | 1.18% | 19.64% | $25.2M | $418.4M | 6.0% |
| Retail | 9.87% | 19.13% | $44.2M | $85.7M | 51.6% |
| UHNW | 0.10% | 19.59% | $8.1M | $1,580.6M | 0.5% |

AUM grew about 19% in every tier, but organic growth is only 1.18% in HNW and 0.10% in UHNW. **Almost all of Wildcat's growth in 2024 came from the portfolios' own value changes, not from new money.** Retail is the one exception: its flows are about half of its dollar growth. Overall, net flows of $77.5M explain only 3.7% of the $2.08B increase, and UHNW provides $1.58B of it. No client joined or left during 2024 (the last new clients arrived in 2022 and the last departures were in 2023, and the year-end counts are identical at 687, 1,394 and 244), so existing clients drove all of it.

What it does **not** tell you:
- **The non-flow part is not split.** The remainder (change in AUM minus net flows) lumps market returns, reinvested income, fees and anything else. OGR does not say how much was market performance.
- **Net flows hide gross activity.** Deposits minus withdrawals can hide large offsetting movements, and say nothing about which clients made them.
- **Rates depend on base size.** Retail's 9.87% is on a small base ($448M), so a modest dollar amount gives a large rate. UHNW's tiny rate sits on a large base.
- **It is one year.** Other years are needed before calling it a pattern.

*Data check:* none of the 2024 deposits or withdrawals are flagged `is_post_departure_txn`, so that flag does not affect these results.
