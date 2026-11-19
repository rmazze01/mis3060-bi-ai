"""
HW7 Part D: reconcile the Power BI dashboard numbers against an independent pandas calculation.

What it does
  1. Recomputes every required value from the Wildcat Capital Clean CSVs with pandas only
     (nothing is read from Power BI for this step).
  2. Reads the Power BI numbers from reports/powerbi_values.csv (columns: measure, slice, value).
  3. Writes reports/kpi_reconciliation.csv with columns:
         measure, slice, powerbi_value, pandas_value, abs_diff, match
  4. Extract check: sums the 2024 rows of data/growth_extract.csv to tier and to region and
     compares them with the tier and region rows of kpi_reconciliation.csv.

Required slices (all 2024)
  Year 2024                    Page 1 cards at firm level
  Tier <HNW|Retail|UHNW>       flows/market split for each tier
  Region <5 regions>           flows/market split for each region (dim_advisor[region])
  Tier Retail                  also the five Page 2 cards (drill-through tier)

Run from the hw07 folder (Git Bash):
    python scripts/01_reconcile_kpis.py

Tolerances (same as Assignment 6): 0.01 for currency (and counts / basis points),
0.0001 for ratios. Alpha Signal is text and must match exactly.

Strict checks (a row never passes by accident):
  - every required (measure, slice) row must exist in powerbi_values.csv; a missing row is a
    mismatch, even if the pandas value is blank
  - a Power BI value that is not a number (e.g. "19.58%", "(Blank)", "#ERROR") is a mismatch,
    except for Alpha Signal, which is text; an empty cell counts as blank
  - duplicate (measure, slice) rows that disagree stop the script
  - a blank value counts as a mismatch, also when pandas is blank too (every required row has data)
  - the script stops if the tiers or regions in the data differ from its lists, if a tier split or
    region split does not add up to the firm total, if txn_type has an unknown spelling, or if a
    Deposit/Withdrawal amount is <= 0
  - it prints how many fact rows have an advisor_id different from the client's advisor
    (0 means the data cannot show which relationship the Power BI model uses for region)
  - the extract check also requires exactly one 2024 row per tier x region
  - the script stops if powerbi_values.csv is missing or if a table name matches more than one CSV
  - the exit code is 1 if any row, or the extract check, does not match; 0 if everything matches

Definitions (same as the Power BI measures)
  Net Flows     = Deposit - Withdrawal from fact_transactions over the calendar year
  Market Change = (Ending AUM - Ending AUM LY) - Net Flows
  Region        = region of the client's advisor (dim_client[advisor_id] -> dim_advisor[region])
"""

import re
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

BASE = Path(__file__).resolve().parents[1]          # the hw07 folder
DATA_DIR = BASE / "Assignment 6 Reference" / "WildcatCapitalClean"
PBI_FILE = BASE / "reports" / "powerbi_values.csv"
OUT_FILE = BASE / "reports" / "kpi_reconciliation.csv"
EXTRACT_FILE = BASE / "data" / "growth_extract.csv"

TOL_CURRENCY = 0.01
TOL_RATIO = 0.0001

# measure name -> kind of tolerance
MEASURE_KIND = {
    "Ending AUM": "currency",
    "Ending AUM LY": "currency",
    "AUM YoY %": "ratio",
    "Net Flows": "currency",
    "Market Change": "currency",
    "Organic Growth Rate": "ratio",
    "Ending Clients": "currency",         # a count, compared at 0.01
    "Avg AUM per Client": "currency",
    "Fee Yield (bps)": "currency",        # basis points, compared at 0.01
    "AUM-Weighted Alpha": "ratio",
    "Alpha Signal": "text",
}

YEAR = 2024
TIERS = ["HNW", "Retail", "UHNW"]
REGIONS = ["Mid-Atlantic", "Midwest", "Northeast", "Southeast", "West"]
DRILL_TIER = "Retail"                          # the tier whose Page 2 cards are reconciled

FIRM_MEASURES = ["Ending AUM", "Ending AUM LY", "AUM YoY %", "Net Flows", "Market Change",
                 "Organic Growth Rate"]
SPLIT_MEASURES = ["Ending AUM", "Ending AUM LY", "Net Flows", "Market Change"]
PAGE2_MEASURES = ["Ending Clients", "Avg AUM per Client", "Fee Yield (bps)",
                  "AUM-Weighted Alpha", "Alpha Signal"]    # Ending AUM is already in SPLIT_MEASURES


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


def build_client_lookup():
    """client_id -> client_tier, region (region comes from the client's advisor)."""
    client = load_csv("dim_client")[["client_id", "client_tier", "advisor_id"]]
    advisor = load_csv("dim_advisor")[["advisor_id", "region"]]
    out = client.merge(advisor, on="advisor_id", how="left", validate="many_to_one")
    if out["region"].isna().any():
        sys.exit("ERROR: %d clients have no advisor or an advisor with no region."
                 % int(out["region"].isna().sum()))
    # The tier and region lists drive every required row. If the data had a value outside them,
    # those clients would count in the firm total but never appear in any tier or region row.
    for col, expected in (("client_tier", TIERS), ("region", REGIONS)):
        found = sorted(out[col].unique())
        if found != sorted(expected):
            sys.exit("ERROR: %s values in the data %s do not equal the script's list %s."
                     % (col, found, sorted(expected)))
    return out[["client_id", "client_tier", "region"]]


def attach(df, lookup, name):
    """Join tier and region onto a fact table. client_id must be unique in the lookup
    (many_to_one). A fact row whose client_id is not in dim_client stops the script,
    because it would silently drop out of every tier and region slice."""
    out = df.merge(lookup, on="client_id", how="left", validate="many_to_one")
    orphans = int(out["client_tier"].isna().sum())
    if orphans:
        sys.exit("ERROR: %d rows in %s have a client_id that is not in dim_client." % (orphans, name))
    return out


def load_all():
    lookup = build_client_lookup()
    dates = load_csv("dim_date")
    dates["date"] = pd.to_datetime(dates["date"])

    snap = load_csv("fact_portfolio_snapshot")
    snap["snapshot_date"] = pd.to_datetime(snap["snapshot_date"])
    snap = attach(snap, lookup, "fact_portfolio_snapshot")

    fees = load_csv("fact_fees")
    fees["fee_date"] = pd.to_datetime(fees["fee_date"])
    fees = attach(fees, lookup, "fact_fees")

    txn = load_csv("fact_transactions")
    txn["txn_date"] = pd.to_datetime(txn["txn_date"])
    txn = attach(txn, lookup, "fact_transactions")

    # Net Flows relies on the exact spelling of two transaction types and on positive amounts.
    known_types = {"Advisory Fee", "Buy", "Deposit", "Dividend", "Sell", "Withdrawal"}
    unknown = sorted(set(txn["txn_type"]) - known_types)
    if unknown:
        sys.exit("ERROR: unexpected txn_type values %s. A misspelled Deposit or Withdrawal would be "
                 "left out of Net Flows and absorbed into Market Change." % unknown)
    missing_types = {"Deposit", "Withdrawal"} - set(txn["txn_type"])
    if missing_types:
        sys.exit("ERROR: txn_type has no %s rows. Found: %s"
                 % (sorted(missing_types), sorted(txn["txn_type"].unique())))
    flow_rows = txn[txn["txn_type"].isin(["Deposit", "Withdrawal"])]
    if (flow_rows["amount"] <= 0).any():
        sys.exit("ERROR: %d Deposit/Withdrawal rows have an amount <= 0. Net Flows = Deposit - "
                 "Withdrawal assumes both are positive." % int((flow_rows["amount"] <= 0).sum()))

    # Region comes from the client's advisor. Report whether the advisor on each fact row ever
    # differs from the client's advisor; if it never does, this script cannot tell which of the
    # two relationships the Power BI model uses.
    client_adv = load_csv("dim_client")[["client_id", "advisor_id"]]
    for name, df in (("fact_portfolio_snapshot", snap), ("fact_transactions", txn)):
        if "advisor_id" in df.columns:
            m = df[["client_id", "advisor_id"]].merge(client_adv, on="client_id",
                                                      suffixes=("", "_client"))
            print("Advisor check: %d rows in %s have an advisor_id different from the client's."
                  % (int((m["advisor_id"] != m["advisor_id_client"]).sum()), name))
    return dates, snap, fees, txn


DATES, SNAP, FEES, TXN = load_all()
ALL_DATES = pd.DatetimeIndex(sorted(DATES["date"].unique()))


# ------------------------------------------------------------------ helpers
def pick(df, date_col, dates, tier, region):
    """Rows of df inside the date window (None = no date filter), client tier and region."""
    out = df
    if dates is not None:
        out = out[out[date_col].isin(dates)]
    if tier is not None:
        out = out[out["client_tier"] == tier]
    if region is not None:
        out = out[out["region"] == region]
    return out


def shifted(dates, offset):
    """Shift a set of calendar dates (like SAMEPERIODLASTYEAR) and keep only dates that exist
    in dim_date."""
    moved = pd.DatetimeIndex(dates + offset)
    return moved.intersection(ALL_DATES)


def ending(dates, tier, region):
    """(ending AUM, ending clients) at the last snapshot inside the window."""
    d = pick(SNAP, "snapshot_date", dates, tier, region)
    if d.empty:
        return np.nan, np.nan
    last = d["snapshot_date"].max()
    at_last = d[d["snapshot_date"] == last]
    return float(at_last["aum"].sum()), float(at_last["client_id"].nunique())


def safe_div(a, b):
    if a is None or b is None or pd.isna(a) or pd.isna(b) or b == 0:
        return np.nan
    return a / b


def net_flows(dates, tier, region):
    t = pick(TXN, "txn_date", dates, tier, region)
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


def compute_measures(dates, tier, region):
    """All measures for one slice. Independent of Power BI."""
    snap = pick(SNAP, "snapshot_date", dates, tier, region)
    fees = pick(FEES, "fee_date", dates, tier, region)

    end_aum, end_clients = ending(dates, tier, region)
    ly_aum, _ = ending(shifted(dates, pd.DateOffset(years=-1)), tier, region)
    flows = net_flows(dates, tier, region)
    sum_aum = float(snap["aum"].sum())

    # AUM-weighted alpha: last snapshot, suspect returns excluded, weighted by aum
    alpha = np.nan
    if not snap.empty:
        last = snap["snapshot_date"].max()
        rows = snap[(snap["snapshot_date"] == last) & (snap["is_return_suspect"] == 0)]
        alpha = safe_div((rows["aum"] * rows["active_alpha_ytd"]).sum(), rows["aum"].sum())

    # Market Change = (Ending AUM - Ending AUM LY) - Net Flows. Blank when there is no prior year.
    market = np.nan if pd.isna(ly_aum) else (end_aum - ly_aum) - flows

    return {
        "Ending AUM": end_aum,
        "Ending AUM LY": ly_aum,
        "AUM YoY %": safe_div(end_aum - ly_aum, ly_aum),
        "Net Flows": flows,
        "Market Change": market,
        "Organic Growth Rate": safe_div(flows, ly_aum),
        "Ending Clients": end_clients,
        "Avg AUM per Client": safe_div(end_aum, end_clients),
        "Fee Yield (bps)": safe_div(float(fees["amount"].sum()) * 12 * 10000, sum_aum),
        "AUM-Weighted Alpha": alpha,
        "Alpha Signal": alpha_signal(alpha),
    }


# --------------------------------------------------------- required slices
def build_pandas_rows():
    rows = []

    def add(slice_name, values, measures):
        for m in measures:
            rows.append({"measure": m, "slice": slice_name, "pandas_value": values[m]})

    window = pd.DatetimeIndex(DATES.loc[DATES["year"] == YEAR, "date"])
    if len(window) == 0:
        sys.exit("ERROR: dim_date has no dates for %d." % YEAR)

    add("Year %d" % YEAR, compute_measures(window, None, None), FIRM_MEASURES)

    for t in TIERS:
        measures = SPLIT_MEASURES + (PAGE2_MEASURES if t == DRILL_TIER else [])
        add("Tier %s | Year %d" % (t, YEAR), compute_measures(window, t, None), measures)

    for r in REGIONS:
        add("Region %s | Year %d" % (r, YEAR), compute_measures(window, None, r), SPLIT_MEASURES)

    out = pd.DataFrame(rows)

    # The tiers, and the regions, must each add up to the firm total, or a client is missing
    # from a split without any row being flagged.
    for level, names in (("Tier", TIERS), ("Region", REGIONS)):
        for m in ("Ending AUM", "Ending AUM LY", "Net Flows"):
            part = sum(out.loc[(out["measure"] == m) &
                               (out["slice"] == "%s %s | Year %d" % (level, n, YEAR)),
                               "pandas_value"].iloc[0] for n in names)
            whole = out.loc[(out["measure"] == m) & (out["slice"] == "Year %d" % YEAR),
                            "pandas_value"].iloc[0]
            if abs(part - whole) > TOL_CURRENCY:
                sys.exit("ERROR: the %s rows for %s add to %.2f but the firm total is %.2f."
                         % (level.lower(), m, part, whole))
    return out


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

    # Every required row is a 2024 value with data behind it, so a blank on either side, or on
    # both sides, is a mismatch (two blanks would more likely be the same mistake made twice).
    kind = MEASURE_KIND[measure]
    if kind == "text":
        a = None if (isinstance(pbi, float) and np.isnan(pbi)) else pbi
        b = None if (pdv is None or (isinstance(pdv, float) and np.isnan(pdv))) else pdv
        return np.nan, (a is not None and b is not None and a == b)

    if isinstance(pbi, str):
        return np.nan, False         # non-numeric text such as "19.58%" or "#ERROR"
    if pd.isna(pbi) or pdv is None or pd.isna(pdv):
        return np.nan, False
    diff = abs(float(pbi) - float(pdv))
    tol = TOL_RATIO if kind == "ratio" else TOL_CURRENCY
    return diff, bool(diff <= tol)


def extract_check(recon):
    """Sum the 2024 rows of growth_extract.csv to tier and to region and compare them with the
    tier and region rows of kpi_reconciliation.csv (the Power BI values, which have already been
    reconciled to pandas above). Returns True if every compared value matches."""
    if not EXTRACT_FILE.exists():
        print("\nEXTRACT CHECK: %s not found." % EXTRACT_FILE)
        return False

    ext = pd.read_csv(EXTRACT_FILE)
    ext = ext[ext["year"] == YEAR]
    expected_pairs = {(t, r) for t in TIERS for r in REGIONS}
    pairs = list(zip(ext["client_tier"], ext["region"]))
    if len(pairs) != len(expected_pairs) or set(pairs) != expected_pairs:
        print("\nEXTRACT CHECK: the %d rows for %d are not exactly one row per tier x region "
              "(found %d rows, %d distinct pairs)." % (len(expected_pairs), YEAR, len(pairs),
                                                       len(set(pairs))))
        return False

    cols = {"Ending AUM": "ending_aum", "Ending AUM LY": "ending_aum_ly",
            "Net Flows": "net_flows", "Market Change": "market_change"}
    lookup = {(r["measure"], r["slice"]): r["powerbi_value"] for _, r in recon.iterrows()}

    results = []
    for level, key, names in (("Tier", "client_tier", TIERS), ("Region", "region", REGIONS)):
        sums = ext.groupby(key)[list(cols.values())].sum()
        for name in names:
            slice_name = "%s %s | Year %d" % (level, name, YEAR)
            for measure, col in cols.items():
                pbi = lookup.get((measure, slice_name), np.nan)
                ext_val = float(sums.loc[name, col]) if name in sums.index else np.nan
                if isinstance(pbi, str) or pd.isna(pbi) or pd.isna(ext_val):
                    ok, diff = False, np.nan
                else:
                    diff = abs(float(pbi) - ext_val)
                    ok = diff <= TOL_CURRENCY
                results.append({"slice": slice_name, "measure": measure, "extract_value": ext_val,
                                "kpi_reconciliation_value": pbi, "abs_diff": diff, "match": ok})

    res = pd.DataFrame(results)
    n_ok = int(res["match"].sum())
    print("\nEXTRACT CHECK: 2024 rows of growth_extract.csv summed to tier and to region vs. "
          "kpi_reconciliation.csv")
    print("%d comparisons, %d match, %d do not match" % (len(res), n_ok, len(res) - n_ok))
    bad = res[~res["match"]]
    if len(bad):
        print(bad.to_string(index=False))
    return len(bad) == 0


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

    extract_ok = extract_check(out)

    if len(bad) or not extract_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
