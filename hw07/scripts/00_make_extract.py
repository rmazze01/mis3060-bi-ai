"""
HW7 Part A, item 5: build data/growth_extract.csv with pandas (nothing is read from Power BI).

Grain: one row per year x client tier x region (5 x 3 x 5 = 75 rows).
Region is the region of the client's advisor: dim_client[advisor_id] -> dim_advisor[region].

Columns
  year, client_tier, region
  ending_aum      BALANCE. Sum of aum on the December snapshot of that year.
  ending_aum_ly   BALANCE. The same balance one year earlier (blank for the first year).
  net_flows       FLOW.    Deposits minus withdrawals summed over the calendar year
                           (same definition as the Power BI [Net Flows] measure).
  market_change   ending_aum - ending_aum_ly - net_flows (blank for the first year).

Source files: the same CSVs the Assignment 6 script reads, kept in
"Assignment 6 Reference/WildcatCapitalClean/".

Run from the hw07 folder (Git Bash):
    python scripts/00_make_extract.py

Checks (the script stops with an error if one fails):
  - exactly 75 rows, no duplicate year/tier/region
  - exactly one December snapshot date per year
  - every client has an advisor, and every advisor has a region
  - every snapshot and transaction row belongs to a client in dim_client (no rows are dropped)
  - the data has no years outside 2020-2024, and txn_type has both "Deposit" and "Withdrawal"
  - every year/tier/region cell has a December balance (no cell is silently filled with 0)
  - the extract's firm-level totals equal an independent calculation without the tier/region split
  - ending_aum_ly equals the prior year's ending_aum, and the market_change identity holds
  - net flows are not zero for every row

Definition notes (see data/README.md): market_change is a residual. It also contains money from clients
who joined or left (2021-2023; none in 2024), flows booked after a client's last snapshot, and is after
advisory fees. The December balance is the 1 December snapshot, because snapshots are dated the 1st.
"""

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]                     # the hw07 folder
DATA_DIR = BASE / "Assignment 6 Reference" / "WildcatCapitalClean"
OUT_FILE = BASE / "data" / "growth_extract.csv"

YEARS = [2020, 2021, 2022, 2023, 2024]
TIERS = ["HNW", "Retail", "UHNW"]
REGIONS = ["Mid-Atlantic", "Midwest", "Northeast", "Southeast", "West"]
KEYS = ["year", "client_tier", "region"]


def load_csv(prefix):
    """Find <prefix>.csv or <prefix> (n).csv in the data folder (e.g. 'dim_date (1).csv').
    More than one match is an error, because the script cannot tell which one Power BI loaded."""
    pattern = re.compile(r"^%s( \(\d+\))?\.csv$" % re.escape(prefix))
    matches = sorted(p for p in DATA_DIR.glob("*.csv") if pattern.match(p.name))
    if not matches:
        sys.exit("ERROR: could not find %s.csv (or '%s (1).csv') in %s" % (prefix, prefix, DATA_DIR))
    if len(matches) > 1:
        sys.exit("ERROR: %d files match the table %s (%s). Keep only the one Power BI loaded."
                 % (len(matches), prefix, ", ".join(m.name for m in matches)))
    return pd.read_csv(matches[0])


def build_client_lookup():
    """client_id -> client_tier, region (region comes from the client's advisor)."""
    client = load_csv("dim_client")[["client_id", "client_tier", "advisor_id"]]
    advisor = load_csv("dim_advisor")[["advisor_id", "region"]]
    out = client.merge(advisor, on="advisor_id", how="left", validate="many_to_one")
    if out["region"].isna().any():
        sys.exit("ERROR: %d clients have no advisor or an advisor with no region."
                 % int(out["region"].isna().sum()))
    return out[["client_id", "client_tier", "region"]]


def attach(df, lookup, name):
    out = df.merge(lookup, on="client_id", how="left", validate="many_to_one")
    orphans = int(out["client_tier"].isna().sum())
    if orphans:
        sys.exit("ERROR: %d rows in %s have a client_id that is not in dim_client." % (orphans, name))
    return out


def december_balances(snap):
    """BALANCE: AUM on the December snapshot of each year, by tier and region."""
    snap = snap.copy()
    snap["snapshot_date"] = pd.to_datetime(snap["snapshot_date"])
    dec = snap[snap["snapshot_date"].dt.month == 12]
    dates_per_year = dec.groupby(dec["snapshot_date"].dt.year)["snapshot_date"].nunique()
    if not (dates_per_year.reindex(YEARS) == 1).all():
        sys.exit("ERROR: expected exactly one December snapshot date per year, found:\n%s"
                 % dates_per_year.to_string())
    dec = dec.assign(year=dec["snapshot_date"].dt.year)
    return dec.groupby(KEYS)["aum"].sum().rename("ending_aum")


def yearly_net_flows(txn):
    """FLOW: deposits minus withdrawals summed over the calendar year, by tier and region."""
    txn = txn.copy()
    txn["year"] = pd.to_datetime(txn["txn_date"]).dt.year
    signed = np.where(txn["txn_type"] == "Deposit", txn["amount"],
                      np.where(txn["txn_type"] == "Withdrawal", -txn["amount"], 0.0))
    txn = txn.assign(signed_amount=signed)
    return txn.groupby(KEYS)["signed_amount"].sum().rename("net_flows")


def main():
    lookup = build_client_lookup()

    snap = attach(load_csv("fact_portfolio_snapshot")[["client_id", "snapshot_date", "aum"]],
                  lookup, "fact_portfolio_snapshot")
    txn = attach(load_csv("fact_transactions")[["client_id", "txn_date", "txn_type", "amount"]],
                 lookup, "fact_transactions")

    # Input checks: years in range, and the transaction types the flow definition relies on.
    snap_years = set(pd.to_datetime(snap["snapshot_date"]).dt.year)
    txn_years = set(pd.to_datetime(txn["txn_date"]).dt.year)
    extra_years = sorted((snap_years | txn_years) - set(YEARS))
    if extra_years:
        sys.exit("ERROR: the data has years outside %s: %s. Update YEARS." % (YEARS, extra_years))
    missing_types = {"Deposit", "Withdrawal"} - set(txn["txn_type"])
    if missing_types:
        sys.exit("ERROR: txn_type has no %s rows. Found: %s"
                 % (sorted(missing_types), sorted(txn["txn_type"].unique())))

    # Full grid: 75 rows. A cell with no December balance is an error, not a zero.
    # A cell with no deposits or withdrawals in a year is a real zero flow.
    grid = pd.MultiIndex.from_product([YEARS, TIERS, REGIONS], names=KEYS)
    out = pd.DataFrame(index=grid)
    out = out.join(december_balances(snap)).join(yearly_net_flows(txn))
    no_balance = out[out["ending_aum"].isna()]
    if len(no_balance):
        sys.exit("ERROR: %d year/tier/region cells have no December balance:\n%s"
                 % (len(no_balance), no_balance.index.to_frame(index=False).to_string(index=False)))
    out["net_flows"] = out["net_flows"].fillna(0.0)

    # Prior-year balance: the same tier and region, one year earlier. First year stays blank.
    prior = out["ending_aum"].copy()
    prior.index = pd.MultiIndex.from_arrays(
        [prior.index.get_level_values("year") + 1,
         prior.index.get_level_values("client_tier"),
         prior.index.get_level_values("region")], names=KEYS)
    out["ending_aum_ly"] = prior.reindex(out.index)
    out["market_change"] = out["ending_aum"] - out["ending_aum_ly"] - out["net_flows"]

    out = out.reset_index()[KEYS + ["ending_aum", "ending_aum_ly", "net_flows", "market_change"]]

    # ---- checks
    if len(out) != 75 or out.duplicated(KEYS).any():
        sys.exit("ERROR: expected 75 unique year/tier/region rows, got %d." % len(out))

    # Independent firm-level check (no tier/region split): December balance and net flows per year.
    snap_d = snap.assign(d=pd.to_datetime(snap["snapshot_date"]))
    firm_aum = (snap_d[snap_d["d"].dt.month == 12].groupby(snap_d["d"].dt.year)["aum"].sum())
    t = txn.assign(y=pd.to_datetime(txn["txn_date"]).dt.year)
    firm_flows = (t[t["txn_type"] == "Deposit"].groupby("y")["amount"].sum()
                  .sub(t[t["txn_type"] == "Withdrawal"].groupby("y")["amount"].sum(), fill_value=0))
    by_year = out.groupby("year")[["ending_aum", "net_flows"]].sum()
    for y in YEARS:
        if abs(by_year.loc[y, "ending_aum"] - firm_aum[y]) > 0.01:
            sys.exit("ERROR: ending_aum for %d does not add up to the firm total." % y)
        if abs(by_year.loc[y, "net_flows"] - firm_flows[y]) > 0.01:
            sys.exit("ERROR: net_flows for %d does not add up to the firm total." % y)

    # The prior-year column must be the previous year's balance, and the identity must hold.
    check = out.set_index(KEYS)
    for y in YEARS[1:]:
        prev = out[out["year"] == y - 1].set_index(["client_tier", "region"])["ending_aum"]
        cur = out[out["year"] == y].set_index(["client_tier", "region"])["ending_aum_ly"]
        if not np.allclose(cur.reindex(prev.index), prev, atol=0.005):
            sys.exit("ERROR: ending_aum_ly for %d is not the %d ending_aum." % (y, y - 1))
    later = check[check.index.get_level_values("year") > YEARS[0]]
    identity = later["ending_aum"] - later["ending_aum_ly"] - later["net_flows"] - later["market_change"]
    if identity.abs().max() > 0.005:
        sys.exit("ERROR: market_change does not equal ending_aum - ending_aum_ly - net_flows.")
    first = check[check.index.get_level_values("year") == YEARS[0]]
    if first[["ending_aum_ly", "market_change"]].notna().any().any():
        sys.exit("ERROR: the first year should have blank ending_aum_ly and market_change.")
    if (out["net_flows"] == 0).all():
        sys.exit("ERROR: net_flows is zero in every row.")

    out_rounded = out.copy()
    for c in ["ending_aum", "ending_aum_ly", "net_flows", "market_change"]:
        out_rounded[c] = out_rounded[c].round(2)
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    out_rounded.to_csv(OUT_FILE, index=False)       # blanks are written as empty cells

    print("Wrote %s (%d rows)" % (OUT_FILE, len(out_rounded)))
    y24 = out[out["year"] == 2024]
    print("2024 firm total: ending_aum %.2f | ending_aum_ly %.2f | net_flows %.2f | market_change %.2f"
          % (y24["ending_aum"].sum(), y24["ending_aum_ly"].sum(),
             y24["net_flows"].sum(), y24["market_change"].sum()))
    print("All checks passed.")


if __name__ == "__main__":
    main()
