# Wildcat Capital: Where 2024 Growth Came From

Wildcat Capital's AUM rose 19.58% in 2024, from $10,644,971,737 to $12,729,572,079, a gain of $2,084.6M. Growth came overwhelmingly from market change, not new money. Market Change contributed $2,007.1M (96.3% of growth), while net flows added just $77.5M (3.7%), an organic growth rate of 0.73%.

By client tier, UHNW drove the dollar growth. It holds 75.8% of AUM and generated $1,572.5M of Market Change against only $8.1M of net flows (0.5% of its growth). HNW also grew mainly through market change ($393.1M, against $25.2M of net flows, 6.0% of its growth). Retail is the exception: it holds 4.2% of AUM yet brought in 57.0% of the firm's net flows ($44.2M), and net flows were 51.6% of its growth.

By region, the Northeast ($735.3M) and Mid-Atlantic ($621.0M) produced 65.1% of growth, followed by the Southeast ($496.0M), West ($171.8M) and Midwest ($60.5M).

Limitation: Market Change is a residual (change in AUM minus net flows), so it includes investment performance, fees and other cash effects and is not a measured market return. It cannot separate performance from fees.

## Audit table

Every number and claim in the summary, the Power BI measure behind it, and the row of `reports/kpi_reconciliation.csv` that supports it (written as *measure | slice*). All 43 rows in that file match pandas. "Derived" means computed from two or more reconciliation rows. The growth of a slice is `Ending AUM − Ending AUM LY` for that slice.

| # | Claim in the summary | Measure | Supporting reconciliation row(s) | Verdict |
|---|---|---|---|---|
| 1 | AUM rose 19.58% | `AUM YoY %` | AUM YoY % \| Year 2024 = 0.195830 | Correct |
| 2 | from $10,644,971,737 | `Ending AUM LY` | Ending AUM LY \| Year 2024 = 10,644,971,737.00 | Correct |
| 3 | to $12,729,572,079 | `Ending AUM` | Ending AUM \| Year 2024 = 12,729,572,078.86 | Correct |
| 4 | a gain of $2,084.6M | `Ending AUM` − `Ending AUM LY` | Derived from rows 2 and 3: 12,729,572,078.86 − 10,644,971,737.00 = 2,084,600,341.86 | Correct |
| 5 | Market Change $2,007.1M | `Market Change` | Market Change \| Year 2024 = 2,007,087,286.60 | Correct |
| 6 | 96.3% of growth | `Market Change` ÷ growth | Derived: 2,007,087,286.60 ÷ 2,084,600,341.86 = 96.28% | Correct |
| 7 | net flows $77.5M | `Net Flows` | Net Flows \| Year 2024 = 77,513,055.26 | Correct |
| 8 | 3.7% of growth | `Net Flows` ÷ growth | Derived: 77,513,055.26 ÷ 2,084,600,341.86 = 3.72% | Correct |
| 9 | organic growth rate 0.73% | `Organic Growth Rate` | Organic Growth Rate \| Year 2024 = 0.007282 | Correct |
| 10 | "Growth came overwhelmingly from market change, not new money" | `Market Change`, `Net Flows` | Rows 5 to 8 | **Corrected.** Claude's draft said "markets", which overstates a residual that also contains fees and cash effects. I changed it to "market change" |
| 11 | UHNW holds 75.8% of AUM | `Ending AUM` | Derived: Ending AUM \| Tier UHNW 9,647,598,426.64 ÷ Ending AUM \| Year 2024 12,729,572,078.86 = 75.79% | Correct |
| 12 | UHNW Market Change $1,572.5M | `Market Change` | Market Change \| Tier UHNW \| Year 2024 = 1,572,474,887.34 | Correct |
| 13 | UHNW net flows $8.1M | `Net Flows` | Net Flows \| Tier UHNW \| Year 2024 = 8,101,601.39 | Correct |
| 14 | 0.5% of UHNW's growth | `Net Flows` ÷ growth | Derived: 8,101,601.39 ÷ (9,647,598,426.64 − 8,067,021,937.91 = 1,580,576,488.73) = 0.51% | Correct |
| 15 | UHNW drove the dollar growth | `Ending AUM`, `Ending AUM LY` | Derived: UHNW growth 1,580.6M of 2,084.6M (75.8%), the largest of the three tiers | Correct |
| 16 | HNW Market Change $393.1M | `Market Change` | Market Change \| Tier HNW \| Year 2024 = 393,139,597.65 | Correct |
| 17 | HNW net flows $25.2M | `Net Flows` | Net Flows \| Tier HNW \| Year 2024 = 25,227,406.26 | Correct |
| 18 | 6.0% of HNW's growth | `Net Flows` ÷ growth | Derived: 25,227,406.26 ÷ (2,548,521,154.33 − 2,130,154,150.42 = 418,367,003.91) = 6.03% | Correct |
| 19 | HNW "grew mainly through market change" | `Market Change` ÷ growth | Derived: 393,139,597.65 ÷ 418,367,003.91 = 93.97% | Correct |
| 20 | Retail holds 4.2% of AUM | `Ending AUM` | Derived: Ending AUM \| Tier Retail 533,452,497.89 ÷ 12,729,572,078.86 = 4.19% | Correct |
| 21 | Retail brought in 57.0% of the firm's net flows | `Net Flows` | Derived: Net Flows \| Tier Retail 44,184,047.61 ÷ Net Flows \| Year 2024 77,513,055.26 = 57.00% | Correct |
| 22 | Retail net flows $44.2M | `Net Flows` | Net Flows \| Tier Retail \| Year 2024 = 44,184,047.61 | Correct |
| 23 | net flows were 51.6% of Retail's growth | `Net Flows` ÷ growth | Derived: 44,184,047.61 ÷ (533,452,497.89 − 447,795,648.67 = 85,656,849.22) = 51.58% | Correct |
| 24 | Retail is "the exception" | `Net Flows` ÷ growth | Rows 14, 18 and 23: the share of a tier's growth that came from net flows is 51.6% for Retail, against 6.0% for HNW and 0.5% for UHNW | Correct |
| 25 | Northeast $735.3M | `Ending AUM`, `Ending AUM LY` | Derived: Ending AUM \| Region Northeast 4,530,738,631.38 − Ending AUM LY 3,795,456,741.84 = 735,281,889.54 | Correct |
| 26 | Mid-Atlantic $621.0M | `Ending AUM`, `Ending AUM LY` | Derived: 3,763,923,872.00 − 3,142,940,677.46 = 620,983,194.54 | Correct |
| 27 | Northeast and Mid-Atlantic produced 65.1% of growth | `Ending AUM`, `Ending AUM LY` | Derived: (735,281,889.54 + 620,983,194.54) ÷ 2,084,600,341.86 = 65.06% | Correct |
| 28 | Southeast $496.0M | `Ending AUM`, `Ending AUM LY` | Derived: 3,064,446,334.69 − 2,568,402,938.22 = 496,043,396.47 | Correct |
| 29 | West $171.8M | `Ending AUM`, `Ending AUM LY` | Derived: 1,014,663,659.95 − 842,832,649.95 = 171,831,010.00 | Correct |
| 30 | Midwest $60.5M | `Ending AUM`, `Ending AUM LY` | Derived: 355,799,580.84 − 295,338,729.53 = 60,460,851.31 | Correct |
| 31 | the order: Southeast, West, then Midwest | `Ending AUM`, `Ending AUM LY` | Rows 28 to 30: 496.0M > 171.8M > 60.5M | Correct |
| 32 | Limitation: Market Change is a residual that includes performance, fees and other cash effects and is not a measured market return; it cannot separate performance from fees | `Market Change` | Definition `(Ending AUM − Ending AUM LY) − Net Flows`, in `data/README.md` and the caveat text box on Page 1. The rows above reconcile the values, not the meaning | Correct |

**Limitations not in the summary.** In 2021 to 2023, Market Change also contains balances of clients who joined or left (none joined or left in 2024), so the 2024 split is the cleanest year in the data. The balance is the 1 December snapshot, while net flows run from 1 January to 31 December. Both are explained in `data/README.md`.
