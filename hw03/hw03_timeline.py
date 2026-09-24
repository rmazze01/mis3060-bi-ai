# =============================================================================
# Script:      hw03_timeline.py
# Purpose:     Corporate Events Timeline. Joins the executive events table
#              (Item 5.02) to the earnings table (Item 2.02) and answers the
#              business question: do executive changes tend to be filed before
#              or after a company's earnings announcements?
# Inputs:      hw03/earnings_history.csv   (from hw03_earnings.py)
#              hw03/executive_events.csv   (from hw03_executives.py)
# Output:      hw03/corporate_events_timeline.csv
# Author:      Rose Mazzeo (MIS3060, Villanova), generated with Claude Cowork
# Generated:   2026-09-24
#
# Third-party libraries: pandas
#   Install with:  pip install pandas
#
# Definitions used in this script:
#   days_to_nearest_earnings = absolute number of days between the executive
#       event's filing_date and the closest earnings filing_date for the same
#       company (earlier or later). If two earnings filings are equally close,
#       the earlier one is used.
#   event_timing =
#       'same week'       if days_to_nearest_earnings <= 7
#       'before earnings' if the event was filed before that earnings filing
#       'after earnings'  if the event was filed after that earnings filing
#   ('same week' takes priority because the prompt defines it as any event
#    within 7 days of an earnings filing, on either side.)
# =============================================================================

import os

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EARNINGS_CSV = os.path.join(SCRIPT_DIR, "earnings_history.csv")
EVENTS_CSV = os.path.join(SCRIPT_DIR, "executive_events.csv")
OUTPUT_CSV = os.path.join(SCRIPT_DIR, "corporate_events_timeline.csv")

SAME_WEEK_DAYS = 7

# -----------------------------------------------------------------------------
# Load both tables. Read everything as text so CIKs keep their leading zeros
# and "NOT_FOUND" values stay exactly as written.
# -----------------------------------------------------------------------------
earnings = pd.read_csv(EARNINGS_CSV, dtype=str, keep_default_na=False)
events = pd.read_csv(EVENTS_CSV, dtype=str, keep_default_na=False)

earnings["filing_date_dt"] = pd.to_datetime(earnings["filing_date"])
events["filing_date_dt"] = pd.to_datetime(events["filing_date"])

print(f"Loaded {len(earnings)} earnings filings and {len(events)} executive events.")

# Earnings columns to carry into the combined table. Columns shared with the
# events table (company, ticker, cik) are kept once; the earnings filing date
# gets its own name so it isn't confused with the event's filing_date.
EARNINGS_COLUMNS = {
    "filing_date": "earnings_filing_date",
    "period": "earnings_period",
    "revenue_reported": "revenue_reported",
    "eps_diluted": "eps_diluted",
    "net_income": "net_income",
}


# -----------------------------------------------------------------------------
# Steps 1 + 2: find the nearest earnings filing for each event, compute
# days_to_nearest_earnings, and categorize event_timing.
# -----------------------------------------------------------------------------
def classify(signed_days):
    """signed_days = event date minus earnings date (negative = event first)."""
    if abs(signed_days) <= SAME_WEEK_DAYS:
        return "same week"
    return "before earnings" if signed_days < 0 else "after earnings"


combined_rows = []
for _, event in events.iterrows():
    company_earnings = earnings[earnings["ticker"] == event["ticker"]]

    row = {col: event[col] for col in events.columns if col != "filing_date_dt"}

    if company_earnings.empty:
        # No earnings rows to compare against: keep the event, mark the gap.
        for new_name in EARNINGS_COLUMNS.values():
            row[new_name] = "NOT_FOUND"
        row["days_to_nearest_earnings"] = "NOT_FOUND"
        row["event_timing"] = "NOT_FOUND"
        combined_rows.append(row)
        continue

    # Signed distance to every earnings filing for this company.
    signed = (event["filing_date_dt"] - company_earnings["filing_date_dt"]).dt.days
    # Nearest by absolute distance; on a tie, prefer the earlier earnings date.
    ranked = company_earnings.assign(signed=signed, abs_days=signed.abs()) \
                             .sort_values(["abs_days", "filing_date_dt"])
    nearest = ranked.iloc[0]

    for old_name, new_name in EARNINGS_COLUMNS.items():
        row[new_name] = nearest[old_name]
    row["days_to_nearest_earnings"] = int(nearest["abs_days"])
    row["event_timing"] = classify(int(nearest["signed"]))
    combined_rows.append(row)

timeline = pd.DataFrame(combined_rows)

# -----------------------------------------------------------------------------
# Step 3: save the combined table.
# -----------------------------------------------------------------------------
output_columns = (
    [c for c in events.columns if c != "filing_date_dt"]
    + list(EARNINGS_COLUMNS.values())
    + ["days_to_nearest_earnings", "event_timing"]
)
timeline = timeline[output_columns]
timeline.to_csv(OUTPUT_CSV, index=False)
print(f"Saved {len(timeline)} rows to {OUTPUT_CSV}")

# -----------------------------------------------------------------------------
# Step 4: per-company summary.
# -----------------------------------------------------------------------------
print("\n" + "=" * 78)
print("EXECUTIVE EVENTS RELATIVE TO THE NEAREST EARNINGS ANNOUNCEMENT")
print("=" * 78)

company_order = list(dict.fromkeys(list(earnings["ticker"]) + list(events["ticker"])))
for ticker in company_order:
    company_rows = timeline[timeline["ticker"] == ticker].sort_values("filing_date")
    name_source = company_rows if not company_rows.empty else earnings[earnings["ticker"] == ticker]
    company_name = name_source["company"].iloc[0]
    print(f"\n{company_name} ({ticker})")

    if company_rows.empty:
        print("  No executive events in past 12 months")
        continue

    for _, r in company_rows.iterrows():
        if r["event_type"] == "NOT_FOUND":
            who = "Item 5.02 filing (no departure/appointment extracted)"
        else:
            title = "" if r["title"] == "NOT_FOUND" else f", {r['title']}"
            who = f"{r['event_type']}: {r['person_name']}{title}"
        print(f"  {r['filing_date']} | {who}")
        print(f"      -> {r['event_timing']} "
              f"({r['days_to_nearest_earnings']} days from {r['earnings_period']} "
              f"earnings filed {r['earnings_filing_date']})")

# -----------------------------------------------------------------------------
# Step 5: final count across all five companies.
# -----------------------------------------------------------------------------
counts = timeline["event_timing"].value_counts()
print("\n" + "=" * 78)
print("FINAL COUNT (all companies)")
print("=" * 78)
for label in ["before earnings", "after earnings", "same week", "NOT_FOUND"]:
    if label in counts or label != "NOT_FOUND":
        print(f"  {label:<16} {int(counts.get(label, 0))}")
print(f"  {'total':<16} {len(timeline)}")
