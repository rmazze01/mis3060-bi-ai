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

## Part C

Answers to the design questions go here.
