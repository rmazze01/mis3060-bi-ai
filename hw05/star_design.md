# HW5: Star Schema Design, Wildcat Capital
**Rose Mazzeo · MIS3060**

## Part A: Keys

| Table | Type | Primary key | Foreign keys (column → table[column]) |
|---|---|---|---|
| dim_advisor | Dimension | `advisor_id` | — |
| dim_benchmark | Dimension | `benchmark_id` | — |
| dim_client | Dimension | `client_id` | `advisor_id` → dim_advisor[advisor_id] |
| dim_date | Dimension | `date_id` | — |
| dim_security | Dimension | `security_id` | `benchmark_id` → dim_benchmark[benchmark_id] |
| fact_fees | Fact | `fee_id` | `client_id` → dim_client[client_id]<br>`advisor_id` → dim_advisor[advisor_id]<br>`fee_date` → dim_date[date] |
| fact_portfolio_snapshot | Fact | `snapshot_id` | `client_id` → dim_client[client_id]<br>`advisor_id` → dim_advisor[advisor_id]<br>`benchmark_id` → dim_benchmark[benchmark_id]<br>`snapshot_date` → dim_date[date] |
| fact_transactions | Fact | `txn_id` | `client_id` → dim_client[client_id]<br>`advisor_id` → dim_advisor[advisor_id]<br>`security_id` → dim_security[security_id] (**can be blank**)<br>`txn_date` → dim_date[date] |

That is 13 foreign keys in total: 2 inside dimension tables (`dim_client` and `dim_security`) and 11 in the fact tables.

### Notes

- **Fact dates match `dim_date[date]`, not `dim_date[date_id]`.** `fee_date`, `snapshot_date` and `txn_date` are calendar dates stored as `YYYY-MM-DD`. The fact tables contain no `date_id` column at all. `dim_date[date]` is unique (1,827 distinct values, one per day from 2020-01-01 to 2024-12-31), so it works as the "one" side of the relationship even though `date_id` is the primary key.
- **Dimension-to-dimension keys.** `dim_client[advisor_id]` points to `dim_advisor`, and `dim_security[benchmark_id]` points to `dim_benchmark`. These make parts of the model snowflaked, not a pure star (revisited in Part E, question d).
- **The one foreign key that can legitimately be blank is `fact_transactions[security_id]`.** It is empty on 101,528 of 298,572 rows (34.0%). These are exactly the Deposit (35,956), Withdrawal (29,830) and Advisory Fee (35,742) rows. Those are cash movements and fee debits, and they involve no security. `shares` and `price` are blank on the same rows. Every Buy, Sell and Dividend row has a security. A blank here is expected structure, not a broken link.
- **Every other foreign key is never blank.** Each one has a value on every row.
- **`advisor_id` appears in `dim_client` and in all three fact tables.** It is a foreign key in each. On every fact row it equals the advisor of that row's client, so the fact-level copies are redundant with `dim_client`. This creates two paths to `dim_advisor` (revisited in Part E, question b).
- **`fact_portfolio_snapshot[benchmark_id]` is a direct foreign key to `dim_benchmark`.** `dim_security` also points to `dim_benchmark`, so there are two separate routes to the benchmark table.

### How I checked

I profiled all eight CSVs and verified:
- Each primary key is unique and never blank, and its row count matches the handout (25 / 8 / 2,500 / 1,827 / 500 / 122,197 / 129,547 / 298,572).
- For each of the 13 foreign keys, every non-blank value exists in the parent key: **0 orphans** in all 13.
- Every fact date falls inside `dim_date` (2020-01-01 to 2024-12-31).
- On all three fact tables, `advisor_id` agrees with `dim_client[advisor_id]` for the same client on 100% of rows.

## Part B: Grain

**fact_fees:** One row represents one fee charged to one client in one month, with its fee type, the AUM it was based on, the rate in basis points and the dollar amount.

**fact_portfolio_snapshot:** One row represents one client's account at the start of one month, with its AUM, year-to-date return, benchmark return, alpha and cash percentage at that date.

**fact_transactions:** One row represents one transaction by one client on one date, either a trade (Buy or Sell) or dividend in a single security, or a cash movement (Deposit, Withdrawal or Advisory Fee) with no security.

### Uniqueness checks

- **fact_fees:** (`client_id`, `fee_date`) has 0 duplicates, so a client has at most one fee row per month, and each such row holds a single fee type. `fee_date` is always the 1st of the month (60 distinct months).
- **fact_portfolio_snapshot:** (`client_id`, `snapshot_date`) has 0 duplicates. `snapshot_date` is always the 1st of the month (60 distinct months), and each client has one account type and one benchmark throughout.
- **fact_transactions:** this table has **no natural key**. 1,238 rows share the same (`client_id`, `txn_date`, `txn_type`, `security_id`) but none of them has the same amount, so they are separate transactions (for example two deposits by one client on one day). Only `txn_id` is unique, so the grain is "one transaction", not "one client per day per type".

## Part C: Measures

How I classified each column: I asked what the total means if the value is added (1) across clients in one month, (2) across months for one client, and (3) both.
- **Additive:** the total is meaningful along every dimension.
- **Semi-additive:** the total is meaningful across clients but not across months, because it is a balance (the same money is counted again every month).
- **Non-additive:** the total is never meaningful, because the value is a rate, ratio, price or percentage.

### C1. Numeric fact columns that are measures (11)

| Column | Class | Across clients (one month) | Across months (one client) | What it means for summing and averaging |
|---|---|---|---|---|
| `fact_fees.amount` | Additive | Yes: fees paid by those clients | Yes: fees paid over the period | A monthly dollar flow, so it can be summed over any slice. |
| `fact_fees.aum_basis` | Semi-additive | Yes: AUM of those clients that month | **No** | A balance equal to that month's snapshot AUM; sum it across clients within one month but take the last value or the average across months (adding all 60 months gives $538.5B). |
| `fact_fees.bps_charged` | Non-additive | No | No | A rate in basis points, so never sum it; average it weighted by `aum_basis`, or recompute it as amount ÷ aum_basis × 12 × 10,000. |
| `fact_portfolio_snapshot.aum` | Semi-additive | Yes: firm AUM that month ($12.7B in Dec 2024) | **No** (all 60 months summed = $566.7B, about 45 times a single month) | A balance at the start of each month, so sum it across clients within one month and use the last month's value or the average across months, never the sum. |
| `fact_portfolio_snapshot.return_ytd` | Non-additive | No | No | A cumulative year-to-date percentage that restarts each January, so never sum it; average it AUM-weighted within one month and leave out `is_return_suspect` rows. |
| `fact_portfolio_snapshot.benchmark_return_ytd` | Non-additive | No | No | A percentage that is identical for every client on the same benchmark and month (1 distinct value in each of the 180 benchmark-months), so summing across clients just multiplies it by the client count. |
| `fact_portfolio_snapshot.active_alpha_ytd` | Non-additive | No | No | The difference of two percentages (return minus benchmark), so it cannot be summed; average it AUM-weighted like `return_ytd`. |
| `fact_portfolio_snapshot.cash_pct` | Non-additive | No | No | A share of the portfolio (1% to 8%), so never sum it; average it AUM-weighted, or compute cash dollars as `aum` × `cash_pct`, which is semi-additive like AUM. |
| `fact_transactions.amount` | Additive, within one `txn_type` | Yes | Yes | Dollars of one kind of activity add up, but all six types are stored as positive numbers, so a plain sum of everything ($16.15B) mixes buys, sells, deposits, withdrawals, dividends and fees; filter or sign it by `txn_type` first (deposits minus withdrawals = $0.33B net). |
| `fact_transactions.shares` | Additive, within one security | Yes | Yes | Share counts add up for the same security, but Buy and Sell are both positive (net position needs a sign by type) and shares of different securities should not be added together. |
| `fact_transactions.price` | Non-additive | No | No | A price per share, so never sum it; use amount ÷ shares or a share-weighted average. |

**Two cautions on these measures**
- **Dividend amounts.** `fact_transactions.amount` equals `shares × price` on 100% of Dividend rows, and the median Dividend ($48,816) is about the same size as the median Buy ($47,889). So a Dividend amount looks like the value of the position, not the income paid. Treat Dividend totals with care.
- **Fee coverage.** `fact_fees` has no fee row for 5.7% of snapshot months (7,350), so fee totals and `aum_basis` cover only the months that have a fee row.

### C2. Numeric fact columns that are not measures (15)

| Table | Keys (identifiers) | Date parts | Flags |
|---|---|---|---|
| `fact_fees` | `fee_id`, `client_id`, `advisor_id` | — | — |
| `fact_portfolio_snapshot` | `snapshot_id`, `client_id`, `advisor_id`, `benchmark_id` | `year`, `month` | `is_return_suspect` |
| `fact_transactions` | `txn_id`, `client_id`, `advisor_id`, `security_id` | — | `is_post_departure_txn` |

- **Keys** are labels: the sum of client numbers means nothing, so count them (distinct count of `client_id`) instead.
- **Date parts** `year` and `month` repeat what `dim_date` already provides, so slice by `dim_date` and not by these.
- **Flags** are 0/1 categories used to filter rows; summing one only counts the flagged rows.

### C3. Numeric dimension attributes that should never be summed

| Table | Column | Why not |
|---|---|---|
| `dim_advisor` | `years_experience` | An advisor trait; a total of years has no meaning, so use average, min or max. |
| `dim_advisor` | `aum_target_mm` | A per-advisor goal in $ millions that repeats on every fact row; summed through fee rows it gives 13,791,550 instead of the true 2,825 total target. |
| `dim_client` | `age` | A person's age; the sum of ages is meaningless, so use the average (54.7). |
| `dim_client` | `initial_aum` | A balance at the date the client joined, not current AUM; summed through the snapshot table it counts each client once per month ($492.9B, 52.6 times the real $9.37B). |
| `dim_security` | `expense_ratio_bps` | A fund fee rate; use an average (weighted by holding), never a sum. |
| `dim_date` | `year`, `quarter`, `month`, `week_of_year` | Calendar labels used to group and slice. |
| `dim_date` | `is_month_end`, `is_quarter_end`, `is_year_end`, `is_trading_day` | 0/1 flags used to filter. |

The key columns of the dimension tables (`advisor_id`, `benchmark_id`, `client_id`, `date_id`, `security_id`) are identifiers and are never summed either. `dim_client.zip_code` is stored as text, so it is not numeric. `dim_benchmark` has no numeric attributes other than its key.

## Part E: Relationships and design questions

The model has 8 tables and 10 relationships. All 10 are many-to-one, single direction and active: `dim_client[advisor_id]` → `dim_advisor`, `dim_security[benchmark_id]` → `dim_benchmark`, `client_id` from each of the three fact tables → `dim_client`, `fact_portfolio_snapshot[benchmark_id]` → `dim_benchmark`, `fact_transactions[security_id]` → `dim_security`, and each fact's date column → `dim_date[date]`. `dim_date` is marked as the date table.

**(a) Why some transactions have no `security_id`, and is that a defect?**
A blank `security_id` appears on 101,528 of the 298,572 transaction rows (34.0%). They are exactly the Deposit (35,956), Withdrawal (29,830) and Advisory Fee (35,742) rows. These are cash movements and fee debits, so no security is involved, and `shares` and `price` are blank on the same rows. Every Buy, Sell and Dividend row has a security. This is not a defect: the blank is correct and every non-blank value matches a row in `dim_security` (0 orphans). I did not fill the blanks with a made-up value, since that would invent a fake security. In Power BI the relationship `fact_transactions[security_id]` → `dim_security[security_id]` stays active, and the cash rows show up under a `(Blank)` ticker. That `(Blank)` row held 3,573,887,227.67 of amount in my test table. The consequence is that any visual sliced by security or ticker has a `(Blank)` member, so it has to be read as "cash and fees, not a security", and security-level totals should not be expected to add up to the whole table.

**(b) Which `advisor_id` relationship(s) did I keep active, and why?**
I kept only the path `dim_advisor` → `dim_client` → fact table: `dim_client[advisor_id]` → `dim_advisor[advisor_id]` plus `client_id` from each fact to `dim_client`, all active. I deleted the three direct relationships from `advisor_id` on the fact tables to `dim_advisor`. Power BI allows only one active path between two tables, and with both the direct link and the link through `dim_client` there are two routes from an advisor to each fact table. Power BI then either marks one inactive or filters ambiguously, which is what I saw in my first attempt, when the advisor links were active and the client links were inactive. The direct copies add no information: on every row of all three fact tables, `advisor_id` equals the advisor of that row's client (100%, checked by `01_keys.py`). Going through `dim_client` gives the same answer and one clear route. The `advisor_id` columns still exist in the fact tables; they just have no relationship. In the slicer test, picking an advisor filtered all three fact tables.

**(c) Which column did I join the date dimension on, and why?**
I joined on `dim_date[date]`, matching `fee_date`, `snapshot_date` and `txn_date`. The fact tables store calendar dates (`YYYY-MM-DD`) and contain no `date_id` column at all, so a join on `date_id` was not possible, and the facts would have to be changed to carry a key they do not have. `dim_date[date]` works as the "one" side because it is unique (1,827 distinct values, one per day from 2020-01-01 to 2024-12-31) and every fact date falls inside that range with 0 orphans. `date_id` stays as the primary key of the table but is not used in any relationship. Each fact has exactly one date column, so each has one active relationship to `dim_date`. Marking `dim_date` as the date table (on the `date` column) lets Power BI treat it as the model's calendar.

**(d) Star or snowflake: does any dimension connect to another dimension, and did I keep it?**
Yes, two. `dim_client[advisor_id]` points to `dim_advisor`, and `dim_security[benchmark_id]` points to `dim_benchmark`. Because of these, the model is mostly a star with two snowflaked branches, not a pure star. I kept both. The client-to-advisor link is the route that advisor filters use to reach the fact tables (see question b), so removing it would cut advisors off from the facts. The security-to-benchmark link is the only way to reach a benchmark from `fact_transactions`. It does not conflict with the direct link from `fact_portfolio_snapshot` to `dim_benchmark`, because those are two different fact tables, so there is no second path from the same benchmark to the same fact table. A benchmark filter should therefore reach the snapshot directly and the transactions through the security, but cash and fee rows have no security, so they belong to no benchmark. The alternative would be to flatten the model by copying advisor attributes into `dim_client` and benchmark attributes into `dim_security`. With only 25 advisors and 8 benchmarks that is cheap, but it repeats the same advisor and benchmark values on thousands of rows, and separate dimensions store each advisor and benchmark only once, so a correction is made in one place.
