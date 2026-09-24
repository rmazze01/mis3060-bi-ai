# HW03 Validation

---

## 5A — Known-Answer Check: Earnings

**Company:** Microsoft Corporation (MSFT)
**Quarter:** Fiscal Q1 2026 (quarter ended September 30, 2025; 8-K filed 2025-10-29)
**Official source:** Microsoft 8-k

| Check | Official Source (Microsoft 8-k) | Your CSV | Match? |
|---|---|---|---|
| MSFT Fiscal Q1 2026 Revenue | $77,673 million | 77.7 billion | Yes (slight rounding difference: the script captured the headline figure, which the press release rounds to one decimal in billions) |
| MSFT Fiscal Q1 2026 EPS Diluted | $3.72 | 3.72 | Yes (exact match) |

### Regex fix (complete only if a value did not match or showed `NOT_FOUND`)

**Field affected:**

**Raw press release excerpt:**

```
N/A

```

**Before (original pattern):**

```python
N/A

```

**After (improved pattern):**

```python
N/A

```

**Did the fix resolve the discrepancy?**  
N/A

---

## 5B — Known-Answer Check: Executive Events

**Event checked (row from `executive_events.csv`):** Apple Inc. (AAPL), filed 2026-04-20: `departure`, Tim Cook, Chief Executive Officer, effective 2026-09-01
**News source (name + URL):** Apple Newsroom press release, "Tim Cook to become Apple Executive Chairman; John Ternus to become Apple CEO" (April 20, 2026): https://www.apple.com/newsroom/2026/04/tim-cook-to-become-apple-executive-chairman-john-ternus-to-become-apple-ceo/
Also reported by ABC News: https://abcnews.com/US/apple-ceo-tim-cook-stepping-john-ternus-set/story?id=132217743

| Check | News Source Confirms? | Notes |
|---|---|---|
| Person name and title | Yes | Press release confirms Tim Cook was Apple's Chief Executive Officer when the change was announced on April 20, 2026. |
| Event type (departure/appointment) | Partially | Cook did leave the CEO role, so "departure" is correct for that title. But he did not leave Apple: he became Executive Chairman of the Board at the same time. The more accurate label would be `both` (departure as CEO + appointment as Executive Chairman). The script likely missed the appointment half because Cook's new role is described with wording like "will become executive chairman," which isn't one of the script's appointment keywords. |
| Effective date | Yes | Press release states the transition takes effect September 1, 2026, which matches the CSV value 2026-09-01. |

---

## 5C — Cross-Validation: Earnings via Yahoo Finance

**Company / Quarter (same as 5A):** Microsoft Corporation (MSFT), Fiscal Q1 2026 (quarter ended September 30, 2025)
**Second source:** Yahoo Finance

**Prompt used:**
> "Write Python using yfinance to get the most recent quarterly revenue and net income for [ticker]."

**yfinance code:**

```python
import yfinance as yf

ticker = yf.Ticker("MSFT")
income = ticker.quarterly_income_stmt  # columns = quarter-end dates, newest first

# Most recent quarter
latest = income.columns[0]
revenue = income.loc["Total Revenue", latest]
net_income = income.loc["Net Income", latest]

print(f"MSFT most recent quarter (ended {latest.date()}):")
print(f"  Revenue:    ${revenue / 1e9:,.2f} billion")
print(f"  Net Income: ${net_income / 1e9:,.2f} billion")

# Quarter used in 5A/5C: fiscal Q1 2026 (ended September 30, 2025)
target = [c for c in income.columns if str(c.date()) == "2025-09-30"]
if target:
    q = target[0]
    print(f"\nMSFT fiscal Q1 2026 (ended {q.date()}):")
    print(f"  Revenue:    ${income.loc['Total Revenue', q] / 1e9:,.2f} billion")
    print(f"  Net Income: ${income.loc['Net Income', q] / 1e9:,.2f} billion")
else:
    print("\nQuarter ended 2025-09-30 not in yfinance's quarterly data.")
```

| Metric | From 8-K text extraction | From yfinance | Match? |
|---|---|---|---|
| Revenue | 77.7 billion | $77.67 billion | Yes (slight rounding difference) |
| Net Income | 27.7 billion | $27.75 billion | Yes (slight rounding difference) |

**If the sources disagree, most likely reason (period mismatch, metric definition difference, or extraction error):**
N/A — the sources agree. The small differences (77.7 vs. 77.67 billion revenue, 27.7 vs. 27.75 billion net income) are rounding, because the 8-K press release rounds to one decimal in billions.

---

## 5D — Pipeline Integrity Checks

| Check | Expected | Actual | Pass/Fail |
|---|---|---|---|
| `earnings_history.csv` row count | Up to 20 (5 companies × 4 quarters) | 20 (4 per company) | Pass |
| `executive_events.csv` row count | At least 0 (document actual) | 32 events from 19 filings | Pass |
| `corporate_events_timeline.csv` created | Yes | Yes (32 rows) | Pass |
| Rows with all three fields `"NOT_FOUND"` | 0 (investigate if > 0) | Earnings: 0 · Executive events: 3 | Pass (earnings) / Investigated (events) |

**Investigation notes (if any check failed):**

- **Earnings table:** No row has revenue, EPS and net income all `NOT_FOUND`. Revenue and diluted EPS were extracted for all 20 filings. Net income is `NOT_FOUND` for 12 of 20 rows (all AAPL, NVDA and WMT filings), because those press releases report net income only in their financial tables, not in a sentence the regex can match.
- **Executive events table:** 3 rows have `person_name`, `title` and `effective_date` all `NOT_FOUND` (and `event_type` is also `NOT_FOUND`):
  - MSFT, filed 2025-12-08
  - NVDA, filed 2026-03-06
  - JPM, filed 2026-01-22

  These are Item 5.02 filings where the script found no departure or appointment language, most likely because they only report compensation or employment-agreement changes. Specification B keeps them as `NOT_FOUND` rows on purpose so the filings are still accounted for.
- **Other data-quality issues found during review:** 3 event rows are extraction errors rather than real people: WMT "Non-Competition Agreements" (2026-01-16), WMT "Covenant Not" (2025-10-22), and NVDA "Nora Johnson" (2026-05-08), a duplicate of Suzanne Nora Johnson.
