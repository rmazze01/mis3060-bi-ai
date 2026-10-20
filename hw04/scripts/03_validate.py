"""
HW4 Part D - Referential integrity and validation: 03_validate.py
=================================================================
Runs the SAME checks on the raw tables and on the clean tables so the effect of
Part C is shown in numbers.

Contents
    1. check_referential_integrity()   one reusable function (keep it for Assignment 5)
    2. Rule-based checks               natural business bounds, allowed lists, sign rules
    3. Cross-table reconciliations     recomputed vs stored, fact vs dimension
    4. IQR outlier flags               on columns with no natural upper bound
    5. Data-quality scorecard          one row per table per stage (raw / clean)

Outputs (reports/):
    data_quality_scorecard.csv   REQUIRED: 16 rows = 8 tables x {raw, clean}
    ri_results.csv               all 13 relationships x {raw, clean}
    validation_detail.csv        every rule / reconciliation / judgment check / IQR result

Run (venv active; run 02_clean.py first so data/clean exists):
    python scripts/03_validate.py

Scorecard definitions (all in %, computed on the ORIGINAL columns only so raw and clean
are comparable; the flag_ columns added in Part C are not scored):
    completeness     non-blank cells / all cells, over columns where a blank would be a defect.
                     Structurally blank columns are excluded (see STRUCTURAL_BLANK).
    key_uniqueness   rows whose primary key is non-blank and appears exactly once / rows
    type_validity    non-blank values that parse STRICTLY as the expected type / non-blank values
                     in typed columns (45.0 in an integer column and 9.28% in a decimal column fail)
    rule_pass        passed / evaluated, pooled over the table's natural-bound rules and its
                     row-level reconciliations. Judgment checks (e.g. return > +500%) are reported
                     separately and are NOT in this score.
    referential_match matched / non-blank keys, pooled over the table's foreign keys.
                     Blank ("n/a") for tables that have no foreign key.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
TABLES = ["dim_advisor", "dim_client", "dim_date", "dim_security", "dim_benchmark",
          "fact_fees", "fact_portfolio_snapshot", "fact_transactions"]
PK = {"dim_advisor": "advisor_id", "dim_client": "client_id", "dim_date": "date_id",
      "dim_security": "security_id", "dim_benchmark": "benchmark_id", "fact_fees": "fee_id",
      "fact_portfolio_snapshot": "snapshot_id", "fact_transactions": "txn_id"}
FOREIGN_KEYS = [  # (child, child column, parent, parent column): 10 ID-based + 3 date
    ("dim_client", "advisor_id", "dim_advisor", "advisor_id"),
    ("dim_security", "benchmark_id", "dim_benchmark", "benchmark_id"),
    ("fact_fees", "client_id", "dim_client", "client_id"),
    ("fact_fees", "advisor_id", "dim_advisor", "advisor_id"),
    ("fact_portfolio_snapshot", "client_id", "dim_client", "client_id"),
    ("fact_portfolio_snapshot", "advisor_id", "dim_advisor", "advisor_id"),
    ("fact_portfolio_snapshot", "benchmark_id", "dim_benchmark", "benchmark_id"),
    ("fact_transactions", "client_id", "dim_client", "client_id"),
    ("fact_transactions", "advisor_id", "dim_advisor", "advisor_id"),
    ("fact_transactions", "security_id", "dim_security", "security_id"),
    ("fact_fees", "fee_date", "dim_date", "date"),
    ("fact_portfolio_snapshot", "snapshot_date", "dim_date", "date"),
    ("fact_transactions", "txn_date", "dim_date", "date"),
]
# Original columns and expected types (flag_ columns added in Part C are deliberately absent)
COLUMN_TYPES = {
    "dim_advisor": "advisor_id:int first_name:text last_name:text region:text years_experience:int aum_target_mm:int certifications:text",
    "dim_benchmark": "benchmark_id:int name:text asset_class:text ticker_proxy:text",
    "dim_client": "client_id:int first_name:text last_name:text age:int city:text state:text zip_code:zip risk_profile:text client_tier:text primary_account_type:text initial_aum:float client_since:date advisor_id:int is_active:bool",
    "dim_date": "date_id:int date:date year:int quarter:int month:int month_name:text week_of_year:int day_of_week:text is_month_end:flag is_quarter_end:flag is_year_end:flag is_trading_day:flag",
    "dim_security": "security_id:int ticker:text name:text asset_class:text sector:text benchmark_id:int is_etf:bool expense_ratio_bps:float",
    "fact_fees": "fee_id:int client_id:int advisor_id:int fee_date:date fee_type:text aum_basis:float bps_charged:float amount:float",
    "fact_portfolio_snapshot": "snapshot_id:int client_id:int advisor_id:int benchmark_id:int snapshot_date:date year:int month:int aum:float return_ytd:float benchmark_return_ytd:float active_alpha_ytd:float cash_pct:float account_type:text",
    "fact_transactions": "txn_id:int client_id:int advisor_id:int security_id:int txn_date:date txn_type:text shares:float price:float amount:float",
}
# Blank is legitimate structure here (decision log D09, D10) -> not counted against completeness
STRUCTURAL_BLANK = {("dim_security", "sector"), ("dim_security", "expense_ratio_bps"),
                    ("fact_transactions", "security_id"), ("fact_transactions", "shares"), ("fact_transactions", "price")}
US_STATES = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split())
CAL_START, CAL_END = pd.Timestamp("2020-01-01"), pd.Timestamp("2024-12-31")
TOL_MONEY = 0.01        # recomputed fee within one cent
TOL_TRADE = 1.00        # shares x price vs amount (same tolerance as the audit)
TOL_ALPHA = 0.000051    # alpha = return - benchmark; 2-dp percent precision of converted rows
RECON_GROUP_TOL = 0.05  # advisory-fee debits vs fee table: within 5% per client-year
IQR_COLUMNS = [("fact_transactions", "amount"), ("fact_fees", "amount"), ("dim_client", "initial_aum")]
IQR_SENTENCE = ("Flagged means statistically unusual relative to the middle 50% of the column, not wrong: "
                "large balances, big deposits and big trades are normal for UHNW clients, so outliers are reviewed, "
                "never deleted or corrected on that basis alone.")


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------
def num(s):
    return pd.to_numeric(s, errors="coerce")


def blank(s):
    return s.str.strip() == ""


def pct(a, b):
    return round(100.0 * a / b, 3) if b else float("nan")


def parse_date(s):
    return pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")


def find_file(data_dir, stem):
    exact = data_dir / f"{stem}.csv"
    if exact.exists():
        return exact
    hits = sorted(data_dir.glob(f"{stem}*.csv"), key=lambda p: (len(p.name), p.name))
    if len(hits) > 1:
        raise SystemExit(f"ERROR: {len(hits)} files match '{stem}*.csv' in {data_dir}: {[h.name for h in hits]}. Keep one and rerun.")
    return hits[0] if hits else None


def locate_raw_dir(project_root, cli_dir):
    if cli_dir:
        return Path(cli_dir).resolve()
    for cand in [project_root / "Wildcat Capital", project_root / "data" / "raw", project_root]:
        if cand.is_dir() and find_file(cand, "dim_advisor"):
            return cand
    sys.exit("ERROR: raw CSVs not found. Pass --data-dir.")


def load_tables(folder, label):
    out = {}
    for t in TABLES:
        f = find_file(folder, t)
        if f is None:
            sys.exit(f"ERROR: {t}.csv not found in {folder} ({label}). Run scripts/02_clean.py first." if label == "clean"
                     else f"ERROR: {t}.csv not found in {folder} ({label}).")
        out[t] = pd.read_csv(f, dtype=str, keep_default_na=False)  # text first, convert on purpose
    return out


# ----------------------------------------------------------------------------
# 1. REUSABLE REFERENTIAL-INTEGRITY FUNCTION  (keep for Assignment 5)
# ----------------------------------------------------------------------------
def check_referential_integrity(fact_df, fact_key, dim_df, dim_key):
    """Check that every value of fact_df[fact_key] exists in dim_df[dim_key].

    Keys are compared as exact text, the way a database or Power BI join sees them
    (so '45.0' does not match '45'). Blank / missing keys are not orphans: they are
    reported separately as the null-key rate and excluded from the match rate.

    Returns a dict:
        rows                  rows in fact_df
        null_key_rows         rows whose key is blank / missing
        null_key_rate         null_key_rows as % of rows
        non_null_rows         rows with a key
        orphan_rows           rows whose (non-blank) key is NOT in the dimension  (count)
        distinct_orphan_keys  number of distinct missing key values
        match_rate            % of non-blank keys found in the dimension (100.0 if no keys)
        orphans               DataFrame of the orphan rows (empty when none)
    """
    key = fact_df[fact_key].astype("string")
    is_null = key.isna() | (key.str.strip() == "")
    valid_keys = set(dim_df[dim_key].dropna().astype("string").str.strip())
    in_dim = key.str.strip().isin(valid_keys)
    orphan_mask = (~is_null) & (~in_dim)
    n, n_null = len(fact_df), int(is_null.sum())
    n_nonnull = n - n_null
    n_orphan = int(orphan_mask.sum())
    return {
        "rows": n,
        "null_key_rows": n_null,
        "null_key_rate": round(100.0 * n_null / n, 3) if n else 0.0,
        "non_null_rows": n_nonnull,
        "orphan_rows": n_orphan,
        "distinct_orphan_keys": int(key[orphan_mask].nunique()),
        "match_rate": round(100.0 * (n_nonnull - n_orphan) / n_nonnull, 3) if n_nonnull else 100.0,
        "orphans": fact_df[orphan_mask],
    }


def run_all_relationships(T, stage):
    rows = []
    for child, ccol, parent, pcol in FOREIGN_KEYS:
        r = check_referential_integrity(T[child], ccol, T[parent], pcol)
        rows.append({"stage": stage, "relationship": f"{child}.{ccol} -> {parent}.{pcol}",
                     "child_table": child, "child_column": ccol, "parent_table": parent, "parent_column": pcol,
                     **{k: v for k, v in r.items() if k != "orphans"}})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# 2. RULE-BASED CHECKS  (each returns (evaluated_mask, fail_mask))
# ----------------------------------------------------------------------------
def r_range(col, lo=None, hi=None, lo_strict=False, hi_strict=False):
    def f(df):
        x = num(df[col])
        ev = x.notna()
        bad = pd.Series(False, index=df.index)
        if lo is not None:
            bad |= (x <= lo) if lo_strict else (x < lo)
        if hi is not None:
            bad |= (x >= hi) if hi_strict else (x > hi)
        return ev, ev & bad
    return f


def r_allowed(col, allowed):
    def f(df):
        v = df[col]
        ev = ~blank(v)
        return ev, ev & ~v.isin(allowed)
    return f


def r_regex(col, pattern):
    def f(df):
        v = df[col]
        ev = ~blank(v)
        return ev, ev & ~v.str.fullmatch(pattern)
    return f


def r_date_between(col, lo=None, hi=None):
    def f(df):
        d = parse_date(df[col])
        ev = d.notna()
        bad = pd.Series(False, index=df.index)
        if lo is not None:
            bad |= d < lo
        if hi is not None:
            bad |= d > hi
        return ev, ev & bad
    return f


def r_tier_matches_aum(df):
    aum = num(df["initial_aum"])
    expected = pd.Series(np.select([aum < 500_000, aum < 5_000_000], ["Retail", "HNW"], "UHNW"), index=df.index)
    ev = aum.notna() & ~blank(df["client_tier"])
    return ev, ev & (df["client_tier"] != expected)


def r_date_parts_agree(df):
    d = parse_date(df["date"])
    ev = d.notna()
    iso = d.dt.isocalendar()
    ok = ((df["year"] == d.dt.year.astype("Int64").astype(str)) & (df["month"] == d.dt.month.astype("Int64").astype(str))
          & (df["quarter"] == d.dt.quarter.astype("Int64").astype(str)) & (df["month_name"] == d.dt.month_name())
          & (df["day_of_week"] == d.dt.day_name()) & (df["week_of_year"] == iso.week.astype("Int64").astype(str))
          & (df["is_month_end"] == d.dt.is_month_end.astype(int).astype(str))
          & (df["is_quarter_end"] == d.dt.is_quarter_end.astype(int).astype(str))
          & (df["is_year_end"] == d.dt.is_year_end.astype(int).astype(str)))
    return ev, ev & ~ok


def r_weekend_not_trading(df):
    d = parse_date(df["date"])
    ev = d.notna()
    return ev, ev & (d.dt.dayofweek >= 5) & (df["is_trading_day"] == "1")


def r_tx_structure(df):
    """Trades carry security, shares and price; cash flows carry none of them (decision log D10)."""
    trade = df["txn_type"].isin(["Buy", "Sell", "Dividend"])
    cash = df["txn_type"].isin(["Deposit", "Withdrawal", "Advisory Fee"])
    all_present = ~blank(df["security_id"]) & ~blank(df["shares"]) & ~blank(df["price"])
    all_blank = blank(df["security_id"]) & blank(df["shares"]) & blank(df["price"])
    ev = trade | cash
    return ev, (trade & ~all_present) | (cash & ~all_blank)


def r_security_ticker(df):
    ev = ~blank(df["ticker"])
    return ev, ev & ~df["ticker"].str.fullmatch(r"[A-Z]{2,5}")


ALLOWED = {
    "region": {"Northeast", "Southeast", "Mid-Atlantic", "Midwest", "West", "Southwest"},
    "certifications": {"None", "CFA", "CFP", "CIMA", "CFP, CFA", "CFP, CIMA", "CFA, CIMA", "CFP, CFA, CIMA"},
    "risk_profile": {"Conservative", "Moderately Conservative", "Balanced", "Moderately Aggressive", "Aggressive"},
    "tier": {"Retail", "HNW", "UHNW"}, "acct": {"Taxable", "IRA", "Roth IRA", "Trust", "529"},
    "bool": {"True", "False"}, "flag": {"0", "1"},
    "dow": {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"},
    "months": {"January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"},
    "sec_class": {"Equity", "Fixed Income", "Alternative", "Cash Equivalent"},
    "fee_type": {"Management", "Advisory", "Custodial", "Performance"},
    "txn_type": {"Buy", "Sell", "Dividend", "Deposit", "Withdrawal", "Advisory Fee"},
}

# (table, column, description, kind, function)  kind: range / allowed list / format / sign / consistency
RULES = [
    ("dim_advisor", "years_experience", "0 to 50 years", "range", r_range("years_experience", 0, 50)),
    ("dim_advisor", "aum_target_mm", "AUM target above 0", "sign", r_range("aum_target_mm", 0, None, lo_strict=True)),
    ("dim_advisor", "region", "allowed region list", "allowed list", r_allowed("region", ALLOWED["region"])),
    ("dim_advisor", "certifications", "allowed certification list (incl. 'None')", "allowed list", r_allowed("certifications", ALLOWED["certifications"])),
    ("dim_client", "age", "18 to 110", "range", r_range("age", 18, 110)),
    ("dim_client", "initial_aum", "initial AUM above 0", "sign", r_range("initial_aum", 0, None, lo_strict=True)),
    ("dim_client", "state", "USPS 2-letter state code", "allowed list", r_allowed("state", US_STATES)),
    ("dim_client", "zip_code", "5 digits (leading zeros kept)", "format", r_regex("zip_code", r"\d{5}")),
    ("dim_client", "risk_profile", "allowed risk profile (blank is scored under completeness)", "allowed list", r_allowed("risk_profile", ALLOWED["risk_profile"])),
    ("dim_client", "client_tier", "Retail / HNW / UHNW", "allowed list", r_allowed("client_tier", ALLOWED["tier"])),
    ("dim_client", "primary_account_type", "allowed account type", "allowed list", r_allowed("primary_account_type", ALLOWED["acct"])),
    ("dim_client", "is_active", "True / False", "allowed list", r_allowed("is_active", ALLOWED["bool"])),
    ("dim_client", "client_since", "not after 2024-12-31", "range", r_date_between("client_since", None, CAL_END)),
    ("dim_client", "client_tier", "tier agrees with initial_aum (<500k, <5M, else UHNW)", "consistency", r_tier_matches_aum),
    ("dim_date", "year", "2020 to 2024", "range", r_range("year", 2020, 2024)),
    ("dim_date", "quarter", "1 to 4", "range", r_range("quarter", 1, 4)),
    ("dim_date", "month", "1 to 12", "range", r_range("month", 1, 12)),
    ("dim_date", "week_of_year", "1 to 53", "range", r_range("week_of_year", 1, 53)),
    ("dim_date", "day_of_week", "weekday names", "allowed list", r_allowed("day_of_week", ALLOWED["dow"])),
    ("dim_date", "month_name", "month names", "allowed list", r_allowed("month_name", ALLOWED["months"])),
    ("dim_date", "is_trading_day", "0 / 1", "allowed list", r_allowed("is_trading_day", ALLOWED["flag"])),
    ("dim_date", "is_month_end", "0 / 1", "allowed list", r_allowed("is_month_end", ALLOWED["flag"])),
    ("dim_date", "is_quarter_end", "0 / 1", "allowed list", r_allowed("is_quarter_end", ALLOWED["flag"])),
    ("dim_date", "is_year_end", "0 / 1", "allowed list", r_allowed("is_year_end", ALLOWED["flag"])),
    ("dim_date", "date", "derived columns (year, month, quarter, names, week, period-end flags) agree with date", "consistency", r_date_parts_agree),
    ("dim_date", "is_trading_day", "weekends are not trading days", "consistency", r_weekend_not_trading),
    ("dim_security", "asset_class", "allowed asset class", "allowed list", r_allowed("asset_class", ALLOWED["sec_class"])),
    ("dim_security", "is_etf", "True / False", "allowed list", r_allowed("is_etf", ALLOWED["bool"])),
    ("dim_security", "expense_ratio_bps", "0 to 200 bps", "range", r_range("expense_ratio_bps", 0, 200)),
    ("dim_security", "ticker", "2-5 capital letters", "format", r_security_ticker),
    ("fact_fees", "aum_basis", "AUM basis above 0", "sign", r_range("aum_basis", 0, None, lo_strict=True)),
    ("fact_fees", "bps_charged", "fee rate above 0 bps", "sign", r_range("bps_charged", 0, None, lo_strict=True)),
    ("fact_fees", "amount", "fee amount above 0", "sign", r_range("amount", 0, None, lo_strict=True)),
    ("fact_fees", "fee_type", "allowed fee type", "allowed list", r_allowed("fee_type", ALLOWED["fee_type"])),
    ("fact_fees", "fee_date", "inside calendar 2020-2024", "range", r_date_between("fee_date", CAL_START, CAL_END)),
    ("fact_portfolio_snapshot", "year", "2020 to 2024", "range", r_range("year", 2020, 2024)),
    ("fact_portfolio_snapshot", "month", "1 to 12", "range", r_range("month", 1, 12)),
    ("fact_portfolio_snapshot", "aum", "AUM not negative", "sign", r_range("aum", 0, None)),
    ("fact_portfolio_snapshot", "return_ytd", "return not below -100%", "range", r_range("return_ytd", -1, None)),
    ("fact_portfolio_snapshot", "benchmark_return_ytd", "benchmark return not below -100%", "range", r_range("benchmark_return_ytd", -1, None)),
    ("fact_portfolio_snapshot", "cash_pct", "0 to 1", "range", r_range("cash_pct", 0, 1)),
    ("fact_portfolio_snapshot", "account_type", "allowed account type", "allowed list", r_allowed("account_type", ALLOWED["acct"])),
    ("fact_portfolio_snapshot", "snapshot_date", "inside calendar 2020-2024", "range", r_date_between("snapshot_date", CAL_START, CAL_END)),
    ("fact_transactions", "txn_type", "allowed transaction type", "allowed list", r_allowed("txn_type", ALLOWED["txn_type"])),
    ("fact_transactions", "shares", "shares above 0 when present (direction is carried by txn_type)", "sign", r_range("shares", 0, None, lo_strict=True)),
    ("fact_transactions", "price", "price above 0 when present", "sign", r_range("price", 0, None, lo_strict=True)),
    ("fact_transactions", "amount", "amount above 0", "sign", r_range("amount", 0, None, lo_strict=True)),
    ("fact_transactions", "txn_date", "inside calendar 2020-2024", "range", r_date_between("txn_date", CAL_START, CAL_END)),
    ("fact_transactions", "security_id/shares/price", "present on trades, blank on cash flows", "consistency", r_tx_structure),
]

# Judgment checks: thresholds that are our assumption, not a business law. Reported, NOT scored.
JUDGMENT = [
    ("fact_portfolio_snapshot", "return_ytd", "return above +500% (decision D06)",
     lambda df: (num(df["return_ytd"]).notna(), num(df["return_ytd"]) > 5)),
    ("fact_portfolio_snapshot", "aum", "AUM at exactly 1,000.00 floor (decision D07)",
     lambda df: (num(df["aum"]).notna(), num(df["aum"]) == 1000)),
    ("fact_fees", "aum_basis", "AUM basis at exactly 1,000.00 floor (decision D07)",
     lambda df: (num(df["aum_basis"]).notna(), num(df["aum_basis"]) == 1000)),
    ("fact_fees", "bps_charged", "fee rate above 100 bps (assumed ceiling, decision D13)",
     lambda df: (num(df["bps_charged"]).notna(), num(df["bps_charged"]) > 100)),
]


# ----------------------------------------------------------------------------
# 3. CROSS-TABLE RECONCILIATIONS  (row-level ones feed the scorecard)
# ----------------------------------------------------------------------------
def make_recons(T):
    cl, sn, fe, tx = T["dim_client"], T["fact_portfolio_snapshot"], T["fact_fees"], T["fact_transactions"]
    out = []
    sn_key = pd.MultiIndex.from_frame(sn[["client_id", "snapshot_date"]])
    fe_key = pd.MultiIndex.from_frame(fe[["client_id", "fee_date"]])

    # fees <-> snapshots (two facts describing the same client-month)
    has_snap = pd.Series(np.asarray(fe_key.isin(sn_key)), index=fe.index)
    out.append(("fact_fees", "fee row has a portfolio snapshot for the same client-month", "cross-table",
                pd.Series(True, index=fe.index), ~has_snap))
    snap_aum = pd.Series(num(sn["aum"]).values, index=sn_key)
    snap_aum = snap_aum[~snap_aum.index.duplicated()]
    mapped = pd.Series(snap_aum.reindex(fe_key).values, index=fe.index)
    ev = has_snap & mapped.notna()
    out.append(("fact_fees", "fee aum_basis equals snapshot aum (same client-month)", "cross-table",
                ev, ev & ((num(fe["aum_basis"]) - mapped).abs() > TOL_MONEY)))

    # fact advisor <-> client's advisor of record
    adv_of = cl.drop_duplicates("client_id").set_index("client_id")["advisor_id"]
    for name, df in [("fact_fees", fe), ("fact_portfolio_snapshot", sn), ("fact_transactions", tx)]:
        m = df["client_id"].map(adv_of)
        ev = m.notna()
        out.append((name, "fact advisor_id equals the client's advisor in dim_client", "cross-table", ev, ev & (m != df["advisor_id"])))

    # snapshot account type <-> client's primary account type
    acct_of = cl.drop_duplicates("client_id").set_index("client_id")["primary_account_type"]
    m = sn["client_id"].map(acct_of)
    ev = m.notna()
    out.append(("fact_portfolio_snapshot", "snapshot account_type equals dim_client.primary_account_type", "cross-table",
                ev, ev & (m != sn["account_type"])))

    # recomputed vs stored (single-table recomputations)
    recomputed = num(fe["aum_basis"]) * num(fe["bps_charged"]) / 10000 / 12
    ev = recomputed.notna() & num(fe["amount"]).notna()
    out.append(("fact_fees", "fee amount = aum_basis x bps / 10,000 / 12 (within 1 cent)", "recomputed",
                ev, ev & ((recomputed - num(fe["amount"])).abs() > TOL_MONEY)))
    sh, pr, am = num(tx["shares"]), num(tx["price"]), num(tx["amount"])
    ev = sh.notna() & pr.notna() & am.notna()
    out.append(("fact_transactions", "amount = shares x price (within $1.00)", "recomputed",
                ev, ev & ((sh * pr - am).abs() > TOL_TRADE)))
    ret, bm, al = num(sn["return_ytd"]), num(sn["benchmark_return_ytd"]), num(sn["active_alpha_ytd"])
    ev = ret.notna() & bm.notna() & al.notna()
    out.append(("fact_portfolio_snapshot", "active_alpha_ytd = return_ytd - benchmark_return_ytd", "recomputed",
                ev, ev & ((al - (ret - bm)).abs() > TOL_ALPHA)))
    return out


def group_level_recon(T):
    """Advisory-fee debits in fact_transactions vs fact_fees, per client-year (not a row-level score)."""
    tx, fe = T["fact_transactions"], T["fact_fees"]
    a = tx[tx["txn_type"] == "Advisory Fee"].assign(y=lambda d: d["txn_date"].str[:4], v=lambda d: num(d["amount"]))
    f = fe.assign(y=fe["fee_date"].str[:4], v=num(fe["amount"]))
    j = pd.concat([a.groupby(["client_id", "y"])["v"].sum(), f.groupby(["client_id", "y"])["v"].sum()],
                  axis=1, keys=["tx", "fee"]).dropna()
    bad = ((j["tx"] - j["fee"]).abs() / j["fee"]) > RECON_GROUP_TOL
    return len(j), int(bad.sum()), float(a["v"].sum()), float(f["v"].sum())


# ----------------------------------------------------------------------------
# 4. IQR OUTLIER FLAGS
# ----------------------------------------------------------------------------
def iqr_flags(T):
    rows = []
    for table, col in IQR_COLUMNS:
        x = num(T[table][col]).dropna()
        q1, q3 = x.quantile(0.25), x.quantile(0.75)
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        flagged = ((x < lo) | (x > hi))
        rows.append({"table": table, "column": col, "q1": q1, "q3": q3, "lower_fence": lo, "upper_fence": hi,
                     "n_values": len(x), "n_flagged": int(flagged.sum()), "pct_flagged": pct(int(flagged.sum()), len(x)),
                     "max_value": x.max()})
    return rows


# ----------------------------------------------------------------------------
# 5. SCORECARD
# ----------------------------------------------------------------------------
def type_valid_mask(s, ty):
    if ty == "int":
        return s.str.fullmatch(r"[+-]?\d+")
    if ty == "float":
        return s.str.fullmatch(r"[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?")
    if ty == "zip":
        return s.str.fullmatch(r"\d{5}")
    if ty == "date":
        return s.str.fullmatch(r"\d{4}-\d{2}-\d{2}") & parse_date(s).notna()
    if ty == "bool":
        return s.isin(["True", "False"])
    if ty == "flag":
        return s.isin(["0", "1"])
    return pd.Series(True, index=s.index)


def evaluate_stage(T, stage):
    ri = run_all_relationships(T, stage)
    detail, rule_counts = [], {t: [0, 0] for t in TABLES}  # table -> [evaluated, failed]

    def add_detail(section, table, column, desc, kind, n_ev, n_fail, in_score, note=""):
        detail.append({"stage": stage, "section": section, "table": table, "column": column, "check": desc, "kind": kind,
                       "n_evaluated": int(n_ev), "n_failed": int(n_fail), "pct_pass": pct(n_ev - n_fail, n_ev),
                       "in_scorecard": in_score, "note": note})

    for table, col, desc, kind, fn in RULES:
        ev, bad = fn(T[table])
        n_ev, n_bad = int(ev.sum()), int(bad.sum())
        rule_counts[table][0] += n_ev
        rule_counts[table][1] += n_bad
        add_detail("rule", table, col, desc, kind, n_ev, n_bad, True)

    for table, desc, kind, ev, bad in make_recons(T):
        n_ev, n_bad = int(ev.sum()), int(bad.sum())
        rule_counts[table][0] += n_ev
        rule_counts[table][1] += n_bad
        add_detail("reconciliation", table, "", desc, kind, n_ev, n_bad, True)

    n_groups, n_bad, tx_total, fee_total = group_level_recon(T)
    add_detail("reconciliation (group)", "fact_transactions / fact_fees", "amount",
               "Advisory Fee debits within 5% of fact_fees total, per client-year", "cross-table", n_groups, n_bad, False,
               f"transaction debits ${tx_total:,.0f} vs fee table ${fee_total:,.0f}; known limitation (decision D16), not scored")

    for table, col, desc, fn in JUDGMENT:
        ev, bad = fn(T[table])
        add_detail("judgment flag", table, col, desc, "judgment", int(ev.sum()), int(bad.sum()), False,
                   "flagged, not corrected; threshold is an assumption, so not in rule_pass")

    for r in iqr_flags(T):
        add_detail("IQR outlier", r["table"], r["column"],
                   f"outside Tukey fences [{r['lower_fence']:,.2f}, {r['upper_fence']:,.2f}] (Q1-1.5*IQR, Q3+1.5*IQR)", "IQR",
                   r["n_values"], r["n_flagged"], False,
                   f"max {r['max_value']:,.2f}. {IQR_SENTENCE}")

    rows = []
    for t in TABLES:
        df = T[t]
        orig_cols = [item.split(":")[0] for item in COLUMN_TYPES[t].split()]
        types = dict(item.split(":") for item in COLUMN_TYPES[t].split())
        req = [c for c in orig_cols if (t, c) not in STRUCTURAL_BLANK]
        filled = sum(int((~blank(df[c])).sum()) for c in req)
        key = df[PK[t]]
        uniq_ok = int(((~blank(key)) & (~key.duplicated(keep=False))).sum())
        valid = total = 0
        for c in orig_cols:
            if types[c] == "text":
                continue
            nb = ~blank(df[c])
            total += int(nb.sum())
            valid += int((type_valid_mask(df.loc[nb, c], types[c])).sum())
        e, f = rule_counts[t]
        mine = ri[ri["child_table"] == t]
        rows.append({"stage": stage, "table": t, "rows": len(df),
                     "pct_completeness": pct(filled, len(df) * len(req)),
                     "pct_key_uniqueness": pct(uniq_ok, len(df)),
                     "pct_type_validity": pct(valid, total),
                     "pct_rule_pass": pct(e - f, e),
                     "pct_referential_match": pct(int(mine["non_null_rows"].sum() - mine["orphan_rows"].sum()), int(mine["non_null_rows"].sum())) if len(mine) else float("nan"),
                     "rules_evaluated": e, "rules_failed": f})
    return pd.DataFrame(rows), ri, pd.DataFrame(detail)


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="HW4 Part D - validate raw vs clean tables")
    ap.add_argument("--data-dir", help="folder with the 8 RAW CSVs (default: auto-detect)")
    ap.add_argument("--clean-dir", help="folder with the 8 CLEAN CSVs (default: <project>/data/clean)")
    ap.add_argument("--reports-dir", help="output folder (default: <project>/reports)")
    args = ap.parse_args()
    root = Path(__file__).resolve().parent.parent
    raw_dir = locate_raw_dir(root, args.data_dir)
    clean_dir = Path(args.clean_dir) if args.clean_dir else root / "data" / "clean"
    out_dir = Path(args.reports_dir) if args.reports_dir else root / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Raw tables   : {raw_dir}\nClean tables : {clean_dir}\nReports      : {out_dir}\n")
    if not clean_dir.is_dir():
        sys.exit("ERROR: data/clean not found - run scripts/02_clean.py first.")

    raw, clean = load_tables(raw_dir, "raw"), load_tables(clean_dir, "clean")
    sc_raw, ri_raw, det_raw = evaluate_stage(raw, "raw")
    sc_cln, ri_cln, det_cln = evaluate_stage(clean, "clean")

    scorecard = (pd.concat([sc_raw, sc_cln], ignore_index=True)
                 .assign(_t=lambda d: d["table"].map({t: i for i, t in enumerate(TABLES)}), _s=lambda d: (d["stage"] == "clean").astype(int))
                 .sort_values(["_t", "_s"]).drop(columns=["_t", "_s"]).reset_index(drop=True))
    ri_all = pd.concat([ri_raw, ri_cln], ignore_index=True)
    detail = pd.concat([det_raw, det_cln], ignore_index=True)

    assert len(scorecard) == 16 and len(ri_all) == 26, "expected 8 tables x 2 stages and 13 relationships x 2 stages"
    pcts = scorecard[[c for c in scorecard.columns if c.startswith("pct_")]]
    assert ((pcts.fillna(0) >= 0) & (pcts.fillna(0) <= 100)).all().all(), "a percentage is outside 0-100"

    scorecard.to_csv(out_dir / "data_quality_scorecard.csv", index=False, encoding="utf-8", lineterminator="\n")
    ri_all.to_csv(out_dir / "ri_results.csv", index=False, encoding="utf-8", lineterminator="\n")
    detail.to_csv(out_dir / "validation_detail.csv", index=False, encoding="utf-8", lineterminator="\n")

    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)
    pd.set_option("display.max_colwidth", 80)

    print("=" * 100 + "\nREFERENTIAL INTEGRITY - 13 relationships, raw vs clean\n" + "=" * 100)
    show = ri_all.pivot_table(index="relationship", columns="stage", values=["match_rate", "orphan_rows", "distinct_orphan_keys", "null_key_rate"],
                              aggfunc="first", sort=False)
    show.columns = [f"{a}_{b}" for a, b in show.columns]
    show = show[["match_rate_raw", "match_rate_clean", "orphan_rows_raw", "orphan_rows_clean", "distinct_orphan_keys_raw", "null_key_rate_raw"]]
    print(show.to_string())

    print("\n" + "=" * 100 + "\nRULE / RECONCILIATION CHECKS THAT FAILED (raw vs clean)\n" + "=" * 100)
    d = detail[detail["section"].isin(["rule", "reconciliation"])]
    w = d.pivot_table(index=["table", "column", "check"], columns="stage", values="n_failed", aggfunc="first", sort=False).fillna(0).astype(int)
    w = w[(w["raw"] > 0) | (w["clean"] > 0)]
    print(w.to_string() if len(w) else "  none")

    print("\n" + "=" * 100 + "\nJUDGMENT FLAGS (reported, not scored) and group-level reconciliation\n" + "=" * 100)
    j = detail[detail["section"].isin(["judgment flag", "reconciliation (group)"])]
    print(j.pivot_table(index=["table", "check"], columns="stage", values="n_failed", aggfunc="first", sort=False).astype(int).to_string())

    print("\n" + "=" * 100 + "\nIQR OUTLIER FLAGS (Tukey fences, 1.5 x IQR)\n" + "=" * 100)
    i = detail[detail["section"] == "IQR outlier"][["stage", "table", "column", "n_evaluated", "n_failed", "pct_pass"]].copy()
    i["pct_flagged"] = (100 - i["pct_pass"]).round(3)
    print(i.drop(columns="pct_pass").rename(columns={"n_evaluated": "n_values", "n_failed": "n_flagged"}).to_string(index=False))
    print(f"\n  {IQR_SENTENCE}")

    print("\n" + "=" * 100 + "\nDATA QUALITY SCORECARD (% ; blank = not applicable)\n" + "=" * 100)
    print(scorecard.drop(columns=["rules_evaluated", "rules_failed"]).to_string(index=False))

    print("\nIMPROVEMENT, raw -> clean (only metrics that changed)")
    a = sc_raw.set_index("table")
    b = sc_cln.set_index("table")
    for t in TABLES:
        ch = []
        for c in ["pct_completeness", "pct_key_uniqueness", "pct_type_validity", "pct_rule_pass", "pct_referential_match"]:
            x, y = a.loc[t, c], b.loc[t, c]
            if not (pd.isna(x) and pd.isna(y)) and x != y:
                ch.append(f"{c[4:]}: {x} -> {y}")
        if a.loc[t, "rows"] != b.loc[t, "rows"]:
            ch.append(f"rows: {a.loc[t, 'rows']:,} -> {b.loc[t, 'rows']:,} (quarantined)")
        print(f"  {t:<26} " + ("; ".join(ch) if ch else "no change"))

    print(f"\nSaved: {out_dir / 'data_quality_scorecard.csv'}\n       {out_dir / 'ri_results.csv'}\n       {out_dir / 'validation_detail.csv'}\nDone.")


if __name__ == "__main__":
    main()
