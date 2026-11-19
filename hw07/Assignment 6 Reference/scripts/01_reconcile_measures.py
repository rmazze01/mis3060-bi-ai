"""
HW6 Part B: reconcile the Power BI DAX measures against an independent pandas calculation.

What it does
  1. Recomputes every measure from the Wildcat Capital Clean CSVs with pandas only
     (nothing is read from Power BI for this step).
  2. Reads the Power BI numbers from reports/powerbi_values.csv (columns: measure, slice, value).
  3. Writes reports/measure_reconciliation.csv with columns:
         measure, slice, powerbi_value, pandas_value, abs_diff, match

Run from the hw06 folder:
    python scripts/01_reconcile_measures.py

Tolerances: 0.01 for currency (and counts / basis points), 0.0001 for ratios.
Alpha Signal is text and must match exactly.

Strict checks (a row never passes by accident):
  - every required (measure, slice) row must exist in powerbi_values.csv; a missing row is a
    mismatch, even if the pandas value is blank
  - a Power BI value that is not a number (e.g. "19.58%", "(Blank)", "#ERROR") is a mismatch,
    except for Alpha Signal, which is text; an empty cell counts as blank
  - duplicate (measure, slice) rows that disagree stop the script
  - the script stops if powerbi_values.csv is missing or if a table name matches more than one CSV
  - the exit code is 1 if any row does not match, 0 if all match
"""

import re
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

BASE = Path(__file__).resolve().parents[1]          # the hw06 folder
DATA_DIR = BASE / "WildcatCapitalClean"
PBI_FILE = BASE / "reports" / "powerbi_values.csv"
OUT_FILE = BASE / "reports" / "measure_reconciliation.csv"

TOL_CURRENCY = 0.01
TOL_RATIO = 0.0001

# measure name -> kind of tolerance
MEASURE_KIND = {
    "AUM (naive SUM)": "currency",
    "Ending AUM": "currency",
    "Ending Clients": "currency",         # a count, compared at 0.01
    "Avg AUM per Client": "currency",
    "Ending AUM LY": "currency",
    "AUM YoY %": "ratio",
    "Ending AUM PM": "currency",
    "AUM MoM %": "ratio",
    "Avg Monthly AUM": "currency",
    "Fee Yield (bps)": "currency",        # basis points, compared at 0.01
    "Organic Growth Rate": "ratio",
    "AUM-Weighted Alpha": "ratio",
    "Alpha Signal": "text",
    "Top 10 Client Share": "ratio",
}

YEARS = [2020, 2021, 2022, 2023, 2024]
TIERS = ["HNW", "Retail", "UHNW"]

GRAND_MEASURES = list(MEASURE_KIND.keys())
YEAR_MEASURES = ["Ending AUM", "Ending AUM LY", "AUM YoY %", "Avg Monthly AUM",
                 "Fee Yield (bps)", "Organic Growth Rate", "AUM-Weighted Alpha", "Alpha Signal"]
TIER_MEASURES = ["Ending AUM", "Avg AUM per Client", "Ending AUM LY", "AUM YoY %",
                 "Fee Yield (bps)", "Organic Growth Rate", "AUM-Weighted Alpha",
                 "Alpha Signal", "Top 10 Client Share"]
DEC_MEASURES = ["Ending AUM PM", "AUM MoM %"]


# ---------------------------------------------------------------- load data
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


def attach_tier(df, client, name):
    """Join client_tier onto a fact table. client_id must be unique in dim_client
    (many_to_one); facts whose client_id is not in dim_client are reported."""
    out = df.merge(client, on="client_id", how="left", validate="many_to_one")
    orphans = int(out["client_tier"].isna().sum())
    if orphans:
        print("WARNING: %d rows in %s have a client_id that is not in dim_client; they have no "
              "tier and are left out of the tier slices." % (orphans, name))
    return out


def load_all():
    client = load_csv("dim_client")[["client_id", "client_tier"]]
    dates = load_csv("dim_date")
    dates["date"] = pd.to_datetime(dates["date"])

    snap = load_csv("fact_portfolio_snapshot")
    snap["snapshot_date"] = pd.to_datetime(snap["snapshot_date"])
    snap = attach_tier(snap, client, "fact_portfolio_snapshot")

    fees = load_csv("fact_fees")
    fees["fee_date"] = pd.to_datetime(fees["fee_date"])
    fees = attach_tier(fees, client, "fact_fees")

    txn = load_csv("fact_transactions")
    txn["txn_date"] = pd.to_datetime(txn["txn_date"])
    txn = attach_tier(txn, client, "fact_transactions")
    return dates, snap, fees, txn


DATES, SNAP, FEES, TXN = load_all()
ALL_DATES = pd.DatetimeIndex(sorted(DATES["date"].unique()))


# ------------------------------------------------------------------ helpers
def pick(df, date_col, dates, tier):
    """Rows of df inside the date window (None = no date filter) and client tier (None = all)."""
    out = df
    if dates is not None:
        out = out[out[date_col].isin(dates)]
    if tier is not None:
        out = out[out["client_tier"] == tier]
    return out


def shifted(dates, offset):
    """Shift a set of calendar dates (like SAMEPERIODLASTYEAR / DATEADD) and keep only
    dates that exist in dim_date. dates=None means 'every date in dim_date'."""
    base = ALL_DATES if dates is None else dates
    moved = pd.DatetimeIndex(base + offset)
    return moved.intersection(ALL_DATES)


def ending(dates, tier):
    """(ending AUM, ending clients) at the last snapshot inside the window."""
    d = pick(SNAP, "snapshot_date", dates, tier)
    if d.empty:
        return np.nan, np.nan
    last = d["snapshot_date"].max()
    at_last = d[d["snapshot_date"] == last]
    return float(at_last["aum"].sum()), float(at_last["client_id"].nunique())


def safe_div(a, b):
    if a is None or b is None or pd.isna(a) or pd.isna(b) or b == 0:
        return np.nan
    return a / b


def net_flows(dates, tier):
    t = pick(TXN, "txn_date", dates, tier)
    dep = t.loc[t["txn_type"] == "Deposit", "amount"].sum()
    wd = t.loc[t["txn_type"] == "Withdrawal", "amount"].sum()
    return float(dep - wd)


def alpha_signal(alpha):
    if pd.isna(alpha):
        return None
    if alpha >= 0.02:
        return "Outperforming"
    if alpha <= -0.02:
        return "Lagging"
    return "In line"


def compute_measures(dates, tier):
    """All 14 measures for one slice. Independent of Power BI."""
    snap = pick(SNAP, "snapshot_date", dates, tier)
    fees = pick(FEES, "fee_date", dates, tier)

    end_aum, end_clients = ending(dates, tier)
    ly_aum, _ = ending(shifted(dates, pd.DateOffset(years=-1)), tier)
    pm_aum, _ = ending(shifted(dates, pd.DateOffset(months=-1)), tier)

    n_snapshots = snap["snapshot_date"].nunique()
    sum_aum = float(snap["aum"].sum())

    # AUM-weighted alpha: last snapshot, suspect returns excluded, weighted by aum
    alpha = np.nan
    top10 = np.nan
    if not snap.empty:
        last = snap["snapshot_date"].max()
        rows = snap[(snap["snapshot_date"] == last) & (snap["is_return_suspect"] == 0)]
        alpha = safe_div((rows["aum"] * rows["active_alpha_ytd"]).sum(), rows["aum"].sum())

        # Top 10 client share = share of Ending AUM held by the 10 largest clients.
        # Numerator and denominator are both read at the slice's last snapshot date, so a
        # client who left earlier in the window is in neither.
        at_last = snap[snap["snapshot_date"] == last]
        per_client = at_last.groupby("client_id")["aum"].sum()
        top10 = safe_div(per_client.nlargest(10).sum(), end_aum)

    return {
        "AUM (naive SUM)": sum_aum,
        "Ending AUM": end_aum,
        "Ending Clients": end_clients,
        "Avg AUM per Client": safe_div(end_aum, end_clients),
        "Ending AUM LY": ly_aum,
        "AUM YoY %": safe_div(end_aum - ly_aum, ly_aum),
        "Ending AUM PM": pm_aum,
        "AUM MoM %": safe_div(end_aum - pm_aum, pm_aum),
        "Avg Monthly AUM": safe_div(sum_aum, n_snapshots),
        "Fee Yield (bps)": safe_div(float(fees["amount"].sum()) * 12 * 10000, sum_aum),
        "Organic Growth Rate": safe_div(net_flows(dates, tier), ly_aum),
        "AUM-Weighted Alpha": alpha,
        "Alpha Signal": alpha_signal(alpha),
        "Top 10 Client Share": top10,
    }


# --------------------------------------------------------- required slices
def build_pandas_rows():
    rows = []

    def add(slice_name, values, measures):
        for m in measures:
            rows.append({"measure": m, "slice": slice_name, "pandas_value": values[m]})

    add("Grand total", compute_measures(None, None), GRAND_MEASURES)

    for y in YEARS:
        window = pd.DatetimeIndex(DATES.loc[DATES["year"] == y, "date"])
        add("Year %d" % y, compute_measures(window, None), YEAR_MEASURES)

    window_2024 = pd.DatetimeIndex(DATES.loc[DATES["year"] == 2024, "date"])
    for t in TIERS:
        add("Tier %s | Year 2024" % t, compute_measures(window_2024, t), TIER_MEASURES)

    window_dec = pd.DatetimeIndex(
        DATES.loc[(DATES["year"] == 2024) & (DATES["month"] == 12), "date"])
    add("Dec 2024", compute_measures(window_dec, None), DEC_MEASURES)

    return pd.DataFrame(rows)


# ---------------------------------------------------------- Power BI values
def load_powerbi_values():
    if not PBI_FILE.exists():
        sys.exit("ERROR: %s not found. Export the Power BI values first (see README). "
                 "Nothing was written." % PBI_FILE)

    # DAX query view copies results as tab-separated text; a saved CSV uses commas.
    # Decide from the header line instead of letting pandas guess.
    with open(PBI_FILE, "r", encoding="utf-8-sig") as fh:
        header_line = fh.readline()
    delimiter = "\t" if "\t" in header_line else ","
    raw = pd.read_csv(PBI_FILE, sep=delimiter, dtype=str, encoding="utf-8-sig",
                      keep_default_na=False)
    raw.columns = [c.strip().strip("[]\"'").lower() for c in raw.columns]
    for needed in ("measure", "slice", "value"):
        if needed not in raw.columns:
            sys.exit("powerbi_values.csv needs columns measure, slice, value. Found: %s"
                     % list(raw.columns))

    raw = raw[["measure", "slice", "value"]].copy()
    for c in raw.columns:
        raw[c] = raw[c].astype("string").str.strip().str.strip("\"'")
    raw = raw.rename(columns={"value": "powerbi_value"})

    dupes = raw.duplicated(["measure", "slice"], keep=False)
    if dupes.any():
        conflicts = raw[dupes].groupby(["measure", "slice"])["powerbi_value"].nunique()
        conflicts = conflicts[conflicts > 1]
        if len(conflicts):
            sys.exit("ERROR: powerbi_values.csv has the same (measure, slice) with different "
                     "values:\n%s" % conflicts.index.to_frame(index=False).to_string(index=False))
        print("WARNING: %d identical duplicate rows in powerbi_values.csv; using one of each."
              % int(raw.duplicated(["measure", "slice"], keep="first").sum()))
        raw = raw.drop_duplicates(["measure", "slice"], keep="first")
    return raw


def to_number(v):
    """Return float for numeric text, NaN for blank, otherwise the text itself."""
    if v is None or pd.isna(v) or str(v).strip() == "":
        return np.nan
    try:
        # A value like "19.58%" is NOT converted: it stays text and is reported as a mismatch,
        # instead of being silently read as 19.58 instead of 0.1958.
        return float(str(v).replace(",", "").replace("$", ""))
    except ValueError:
        return str(v)


# ---------------------------------------------------------------- reconcile
def compare(measure, pbi, pdv, row_present):
    """pbi: float, NaN (empty cell) or text. row_present: False if the row is not in
    powerbi_values.csv at all, which is always a mismatch."""
    if not row_present:
        return np.nan, False

    kind = MEASURE_KIND[measure]
    if kind == "text":
        a = None if (isinstance(pbi, float) and np.isnan(pbi)) else pbi
        b = None if (pdv is None or (isinstance(pdv, float) and np.isnan(pdv))) else pdv
        return np.nan, a == b

    if isinstance(pbi, str):
        return np.nan, False         # non-numeric text such as "19.58%" or "#ERROR"
    pbi_missing = pd.isna(pbi)
    pdv_missing = pdv is None or pd.isna(pdv)
    if pbi_missing and pdv_missing:
        return np.nan, True          # both blank (e.g. YoY for 2020)
    if pbi_missing or pdv_missing:
        return np.nan, False
    diff = abs(float(pbi) - float(pdv))
    tol = TOL_RATIO if kind == "ratio" else TOL_CURRENCY
    return diff, bool(diff <= tol)


def main():
    pandas_rows = build_pandas_rows()
    pbi = load_powerbi_values()
    merged = pandas_rows.merge(pbi, on=["measure", "slice"], how="left", indicator=True)

    out_rows = []
    for _, r in merged.iterrows():
        pbi_val = to_number(r.get("powerbi_value"))
        pdv = r["pandas_value"]
        present = r["_merge"] == "both"
        diff, ok = compare(r["measure"], pbi_val, pdv, present)
        out_rows.append({
            "measure": r["measure"],
            "slice": r["slice"],
            "powerbi_value": pbi_val,
            "pandas_value": pdv if (pdv is None or isinstance(pdv, str)) else round(float(pdv), 8),
            "abs_diff": diff if pd.isna(diff) else round(diff, 8),
            "match": ok,
        })

    out = pd.DataFrame(out_rows,
                       columns=["measure", "slice", "powerbi_value", "pandas_value", "abs_diff", "match"])
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_FILE, index=False)

    n_match = int(out["match"].sum())
    print("Wrote %s" % OUT_FILE)
    print("%d rows, %d match, %d do not match" % (len(out), n_match, len(out) - n_match))

    extra = pbi.merge(pandas_rows[["measure", "slice"]], on=["measure", "slice"],
                      how="left", indicator=True)
    extra = extra[extra["_merge"] == "left_only"]
    if len(extra):
        print("NOTE: %d rows in powerbi_values.csv were not used (not a required slice)." % len(extra))

    missing = merged[merged["_merge"] != "both"][["measure", "slice"]]
    if len(missing):
        print("\nRows missing from powerbi_values.csv (counted as not matching):")
        print(missing.to_string(index=False))

    bad = out[~out["match"]]
    if len(bad):
        print("\nRows that do not match:")
        print(bad.to_string(index=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
