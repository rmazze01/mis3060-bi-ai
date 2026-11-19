# data/ — growth_extract.csv

Built by `scripts/00_make_extract.py` with pandas, from the Wildcat Capital Clean CSVs in `Assignment 6 Reference/WildcatCapitalClean/` (the same files the Assignment 6 script reads). Nothing is read from Power BI.

**Grain:** one row per year × client tier × region = 75 rows (2020–2024 × HNW, Retail, UHNW × Mid-Atlantic, Midwest, Northeast, Southeast, West).
**Region:** the region of the client's advisor (`dim_client[advisor_id]` → `dim_advisor[region]`).

## Columns

| Column | Type | What it is | Can it be added across years? |
|---|---|---|---|
| `year` | key | Calendar year | n/a |
| `client_tier` | key | `dim_client[client_tier]` (HNW, Retail, UHNW) | n/a |
| `region` | key | `dim_advisor[region]` of the client's advisor | n/a |
| `ending_aum` | **balance** | AUM on the December snapshot of that year (point in time) | **No.** Adding 2023 and 2024 counts the same money twice. Add across tiers and regions within one year only. |
| `ending_aum_ly` | **balance** | The same balance one year earlier (the prior year's December `ending_aum`). Blank for 2020, the first year | **No**, same reason |
| `net_flows` | **flow** | Deposits minus withdrawals, summed over the calendar year (same definition as the Power BI `Net Flows` measure) | **Yes.** It can be summed across years, tiers and regions |
| `market_change` | **flow** (derived) | `ending_aum − ending_aum_ly − net_flows`: the part of the year's AUM change not explained by net new money. It is a residual, so it includes investment performance, fees and other cash effects. Blank for 2020 | **Yes**, because it is a change over a year |

## Notes

- The first year (2020) keeps its rows, with `ending_aum_ly` and `market_change` left blank (there is no 2019 balance).
- Snapshots are dated the first of each month, so the "December snapshot" is the 1 December snapshot of that year.
- Clients who left before a given December have no snapshot that month, so they are not in that year's `ending_aum`.
- Within a year, `ending_aum`, `net_flows` and `market_change` add up across tiers and regions to the firm totals. The script checks this for every year before writing the file.
