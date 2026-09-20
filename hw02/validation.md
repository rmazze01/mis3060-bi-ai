### 2A — Known-Answer Benchmarks (8 points)

| Check | Expected | Your Script Produced | Match? | Notes |
|---|---|---|---|---|
| Dataset shape | (298772, 9) | (298772, 9) | Yes | |
| Null count — `security_id` | 101,597 | 101,597 | Yes | |
| Null count — `amount` | 0 | 0 | Yes | |
| Unique `txn_type` values | 6 | 6 | Yes | |
| Count of `Buy` transactions | 83,556 | 83,556 | Yes | |
| `txn_date` data type | object | datetime64[us] | No | See discrepancy note below. |
| Earliest `txn_date` | 2020-01-01 | 2020-01-01 | Yes | |
| Latest `txn_date` | 2024-12-30 | 2024-12-30 | Yes | |
| Duplicate `txn_id` count | 0 | 0 | Yes | |
| Mean `amount` | $54,075.17 | $54,075.17 | Yes | |
| Median `amount` | $41,220.48 | $41,220.49 | No | See discrepancy note below. |
| Skewness of `amount` | 1.15 | 1.15 (1.1463 unrounded) | Yes | |
| Correlation `shares`–`amount` | 0.65 | 0.65 | Yes | |
| Correlation `price`–`amount` | 0.64 | 0.64 | Yes | |
| Correlation `shares`–`price` | 0.00 | 0.00 | Yes | |
| Negative `shares` count (Buy only) | 836 | 836 | Yes | |
| Profile file created | Yes | Yes | Yes | |
| Chart files created (3) | Yes | Yes | Yes | |

---

## Discrepancy Notes

### 1. `txn_date` data type — object (expected) vs. datetime64[us] (produced)

**Discrepancy:** `hw02_eda.py` loads the data with `pd.read_csv(DATA_PATH, parse_dates=["txn_date"])`. That `parse_dates` argument tells pandas to convert `txn_date` from its raw string form into a `datetime64` type at load time, so `df.dtypes` reports `datetime64[us]` instead of `object`.

**Why the script does this on purpose:** step 8 of the spec requires printing the earliest and latest `txn_date`. Parsing the column to a real datetime type lets `.min()` and `.max()` sort correctly and lets `.date()` format the output cleanly. If the column were left as raw text (`object`), min/max would do a string comparison, which happens to give the same answer here (because the dates are formatted `YYYY-MM-DD`, which sorts identically as text or as a date) but is not reliable in general.

**Investigation (Claude Cowork conversation):** to confirm this was the cause and not a data problem, I reloaded the same CSV without the `parse_dates` argument in the same Claude Cowork session used to build the script:

```
>>> import pandas as pd
>>> df = pd.read_csv("fact_transactions.csv")
>>> df["txn_date"].dtype
dtype('O')   # i.e. object / string — matches the expected answer key
```

This confirms the raw column is indeed `object` on load, and the `datetime64[us]` result is a direct, intentional effect of the `parse_dates=["txn_date"]` argument in the script — not a bug or a data issue. If the assignment requires the profiling step to reflect the file's *raw* dtypes, the fix is to check dtypes with a separate `pd.read_csv()` call (without `parse_dates`) before doing the date parsing needed for step 8, or to parse dates into a new column instead of overwriting `txn_date`.

### 2. Median `amount` — $41,220.48 (expected) vs. $41,220.49 (produced)

**Discrepancy:** the script prints the median using Python f-string formatting: `f"{amount_median:,.2f}"`, which produced $41,220.49. The expected answer key has $41,220.48 — a one-cent difference.

**Investigation (Claude Cowork conversation):** I checked the exact underlying value in the same session:

```
>>> med = df["amount"].median()
>>> med
41220.485
>>> round(med, 2)
41220.48
>>> import numpy as np; np.round(med, 2)
41220.48
>>> f"{med:.2f}"
'41220.49'
>>> import decimal; decimal.Decimal(med)
Decimal('41220.485000000000582076609134674072265625')
```

The true median sits exactly on a rounding boundary: $41,220.485. Python's `round()` and NumPy's `round()` both use "round half to even" (banker's rounding) and round the tie down to $41,220.48, since 8 is already even. Python's string-formatting operator (`:.2f`, used in the script) instead looks at the closest 64-bit floating-point representation of that value — which, due to binary floating-point imprecision, is stored microscopically *above* the true .485 tie (41220.485000000000582...) — and rounds it up to $41,220.49.

Both results are numerically defensible; they disagree only because two different, both-valid rounding rules were applied to a value that sits exactly on a rounding boundary. This is not a data error. If the assignment's answer key was generated with `round()`/NumPy rounding, the script can be changed to use `round(amount_median, 2)` before formatting (with `:,.2f` for the comma) to match it exactly.



## 2B — Claude Conversation Validation

### 1. Did Claude's predicted outputs (Prompt 1) match what you actually saw in the terminal (Prompt 2)? List any discrepancies.

Yes, on every printed value — shape, dtypes, null counts, descriptive statistics, transaction-type frequency table, unique entity counts, date range, duplicate count, mean/median/skewness, the two grouped summary tables, the correlation matrix and top-3 pairs, and the shares-by-type table were all identical between Claude's Prompt 1 walkthrough and the terminal output pasted in Prompt 2. (Claude had pulled the real values from the already-saved `hw02_profile.txt` for the walkthrough rather than guessing, so an exact match was expected.)

Two discrepancies worth noting:

- **Source data path.** The pre-existing `hw02_profile.txt` that Claude read for Prompt 1 recorded `Source data: /home/claude/project/02_Data/raw/fact_transactions.csv` — a Linux-style path — and Claude flagged that as something to double-check. The fresh terminal output pasted in Prompt 2 showed the correct `Loaded data from: C:\MIS3060\HW2\02_Data\raw\fact_transactions.csv`. So the discrepancy resolved itself: the odd path was left over from an earlier/different run of the script, not a problem with the live Windows run.
- **Matplotlib deprecation warning.** Prompt 1 did not predict the `MatplotlibDeprecationWarning: vert: bool was deprecated...` line that appeared on the box plot in Prompt 2's output. That warning depends on the exact Matplotlib version installed locally, which isn't knowable just from reading the script's source code — so it wasn't something Claude could have predicted in advance.

### 2. What did Claude flag as potentially unexpected or worth investigating (from Prompt 2)?

In priority order:

1. 836 `Buy` transactions (about 1% of all Buys) have negative `shares`, with a minimum of -499.63 — but `Sell` and `Dividend` never go negative. Since `Sell` already exists as its own category, Claude flagged this as ambiguous: it could be a legitimate trade reversal/cancellation, or a mislabeling issue.
2. Advisory Fee has a mean amount of $7,375.17 but a median of only $859.12 — an 8.5x gap, far wider than any other transaction type — suggesting a small number of unusually large fee transactions are pulling the average up.
3. `client_id` values range up to 3,192 but only 2,700 unique client IDs actually appear in the data, meaning roughly 492 IDs in that range never transacted — unlike `advisor_id` and `security_id`, which are both fully dense with no gaps.
4. `price`, `shares`, and `security_id` all cap out right around 500, which Claude called a sign the dataset is likely synthetically generated with hard-coded bounds rather than pulled from real market activity.

### 3. Did Claude mention the 101,597 null values in `security_id`? What explanation did it give?

Yes. Claude noted that `security_id`, `shares`, and `price` are each missing in exactly 101,597 rows, and that this number matches exactly the combined count of Deposit (35,981) + Advisory Fee (35,766) + Withdrawal (29,850) transactions. Its explanation was that this is structural, not a data-quality problem: those three transaction types don't involve buying or selling a security, so there's nothing to record in those columns for them.

### 4. Did Claude flag the `txn_date` column as a concern? Why would that matter for a time-series analysis?

No — Claude did not flag `txn_date` as a concern in either prompt. The only note it made was that the date range ends on 2024-12-30 rather than 12-31, which it called a minor curiosity rather than something to investigate. Claude did not check for missing dates within the range, weekend/weekday clustering, or uneven distribution of transactions across months or years.

This matters for time-series analysis because `min()`/`max()` only confirms the outer boundaries of the date range — it says nothing about whether every period in between is actually represented. If certain months, weeks, or weekdays are under- or over-represented, any trend, growth-rate, or seasonality calculation built on `txn_date` could be skewed without it being obvious from the date range alone. Before running a time-series analysis on this data, it would be worth resampling by month (or week) and checking transaction counts over time for gaps or irregular clustering, rather than relying on the earliest/latest date check alone.

### 5. Open your three chart files. Does what you see in each image match Claude's explanation of that section of the output? Note any differences.

### hist_amount.png 
The chart my script generated closely mirrored what Claude expected. Claude predicted my histogram would have 50 bins, a red vertical dashed line at the mean (54,075.17) and a solid green line at the median (41,220.49). It also predicted the histogram would skew left. All of these characteristics were in my histogram. One thing I noticed was that Claude did not mention the headers, axis titles, and legend that my code also generated when I ran it.

### box_amount_by_type.png
Claude also gave a very similar explanation to what my code generated for this box plot. Claude predicted my code would generate a box plot with one box per transaction type, ordered by highest to lowest median amount. In addition, Claude predicted that the 'Advistory Fee' box would be compressed compared to the others. All of these characteristics were in my box plot. Like the histogram, I noticed that Claude did not mention headings and axis titles. Claude also did not mention any specific means but my box chart only had yellow lines to mark the means and not specific numbers. 

### scatter_shares_amount.png
Unlike the box chart and histogram, Claude did correctly call out the axis titles for this scatterplot. Claude also predicted that points would be colored by transaction type, but did not mention the legend on the chart that described what each color meant. The upward trend Claude mentioned also matched what I saw in my graph. Finally, Claude predicted that advisory fee/deposit/withdrawl would not have any points because they had no shares which matched my graph.



### 6. Paste one follow-up question you asked Claude, and Claude's answer.

### My question:  
 Do you know which of the generated charts from that script would have legends in them?  
### Claude's Response:   
Yes — looking back at the charting section of hw02_eda.py:

hist_amount.png — has a legend. ax.legend() is called, showing the two labeled vertical lines: "Mean: 54,075.17" and "Median: 41,220.49".
box_amount_by_type.png — no legend. The box plot uses tick_labels=type_order to label each box directly on the y-axis (the transaction type names), so there's no separate legend needed.
scatter_shares_amount.png — has a legend. ax.legend(markerscale=2, fontsize=8) is called to label each color by its txn_type value, since the points are colored by category with plt.cm.tab10.

So two of the three charts (histogram and scatter) should show a legend; the box plot relies on axis labels instead.    
### Question 6 Conclusion   
Claude correctly predicted which two charts had legends (the histogram and scatterplot) and which did not (box chart)  

### 2C - Business Check and Cross-Validation
### Business-Reasonableness Questions
1) The three transaction types I would expect to have no security are advisory fee, deposit, and withdrawls. Advisory fees are usually paid to the client's financial advisor or a financial services company for securities expertise rather than a purchase or selling of stock. Deposits and withdrawls are simply adding or subtracting from an investment account balance, no securities are bought or sold. The counts for these 3 transaction types add to the total null 101,597: 35,981 + 29,850 + 35,766.   
2) If a wealth management firm has more Buys than Sells over a five-year period, the firm may have gained more clients than they lost or clients are holding onto securities to avoid tax consequences. As a result, clients are holding onto/buying more securities than they are selling, resulting in more Buys for the firm over a five-year period.  
3) I found this question interesting because when I created my script with Claude, Claude classified txt_date as a date and not an object. If the code classified txt_date as a string and not a date, the code would likely have issues because Python cannot subtract strings from each other. The code would likely fail or hallucinate if you tried to subtract strings from each other because they are classified as text and not a number.  
4) According to VIP Wealth Advisors, the average wealth management advisor has around 150 clients, putting 108 clients per advisor at Wildcat not too far off average. While 108 is plausible, it is also important to consider the complexitity of each client. For example, advisors working with very high net-worth clients usually work for much fewer clients than an advisor serving clients with lower net-worths.   
5) Two plausible reasons a buy transaction might have a negative value is it is a legitamate reversal entry or it is a user data entry error. To determine which scenario is more likely, I would look for positive and negative rows that make up offsetting pairs. For example, if there was a positive transaction for 200 shares on 2/1/2026 and a negative transaction for -200 shares on 2/1/2026, I would be more confident the negative value is due to a legitimate reversal. If a negative transaction cannot be matched to a positive transaction, I would be more convinced there was a data entry error.  
### Cross Validation
6) Prompt A: 83,556  
Prompt B: 83,556   
7) The resulted agreed from both scripts.   
8) Verifying a count by subtraction rather than direct filter because it can catch labeling errors. For example, if you sorted by "Buy" you would only get a count of rows with txn_type "Buy". However if you used the subtraction method and took out "Sell", "Deposit", "Withdrawl", "Dividend", and "Advisory Fee" you would get both rows with "Buy" and possibly rows that were meant to be "Buy" but had a data entry error (ex: "buy" or "By"). While using both the direct filter and subtraction methods are best to gain more assurance over the results, the subtraction method helps capture data entry errors the direct filter method would not. 


