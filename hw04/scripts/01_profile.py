"""
HW4 Part A - Audit: 01_profile.py
=================================
Profiles the eight raw Wildcat Capital tables and runs four groups of checks.

Outputs (raw files are never modified):
    reports/profile_raw.csv     one row per table x column (generic profile)
    reports/dq_summary_raw.csv  one row per check (PASS/FAIL, ERROR/WARN/INFO)

Run from VS Code (Git Bash or PowerShell, venv active):
    python scripts/01_profile.py
    python scripts/01_profile.py --data-dir "path/to/Wildcat Capital"

Design
------
* PART 1 - generic profiler.  profile_table(name, df) knows nothing about any
  specific table; it works on any DataFrame read as text.
* PART 2 - check groups.  Business knowledge lives in the declarative CONFIG
  block below (keys, foreign keys, allowed values, ranges).  Generic engines
  read the config; only a handful of cross-column rules are written by hand.

Every file is read with dtype=str, keep_default_na=False (assignment rule).
"""
import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# CONFIG - what we know about the warehouse (edit here, not in the engines)
# ----------------------------------------------------------------------------
TABLE_FILES = [  # logical name == file stem
    "dim_advisor", "dim_client", "dim_date", "dim_security", "dim_benchmark",
    "fact_fees", "fact_portfolio_snapshot", "fact_transactions",
]
PK = {
    "dim_advisor": "advisor_id", "dim_client": "client_id", "dim_date": "date_id",
    "dim_security": "security_id", "dim_benchmark": "benchmark_id",
    "fact_fees": "fee_id", "fact_portfolio_snapshot": "snapshot_id",
    "fact_transactions": "txn_id",
}
# other columns that must be unique (natural keys)
NATURAL_KEYS = {
    "dim_date": ["date"], "dim_security": ["ticker"], "dim_benchmark": ["ticker_proxy", "name"],
}
# (child table, child column, parent table, parent column) - ten ID-based + three date
FOREIGN_KEYS = [
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
# Foreign-key columns that are legitimately blank for some rows (structure, not defect)
NULLABLE_FK = {("fact_transactions", "security_id")}  # cash flows / fee debits have no security

# expected type per column: int, float, date, bool, text, flag (0/1)
EXPECTED_TYPE = {
    "dim_advisor": "advisor_id:int first_name:text last_name:text region:text years_experience:int aum_target_mm:int certifications:text",
    "dim_benchmark": "benchmark_id:int name:text asset_class:text ticker_proxy:text",
    "dim_client": "client_id:int first_name:text last_name:text age:int city:text state:text zip_code:zip risk_profile:text client_tier:text primary_account_type:text initial_aum:float client_since:date advisor_id:int is_active:bool",
    "dim_date": "date_id:int date:date year:int quarter:int month:int month_name:text week_of_year:int day_of_week:text is_month_end:flag is_quarter_end:flag is_year_end:flag is_trading_day:flag",
    "dim_security": "security_id:int ticker:text name:text asset_class:text sector:text benchmark_id:int is_etf:bool expense_ratio_bps:float",
    "fact_fees": "fee_id:int client_id:int advisor_id:int fee_date:date fee_type:text aum_basis:float bps_charged:float amount:float",
    "fact_portfolio_snapshot": "snapshot_id:int client_id:int advisor_id:int benchmark_id:int snapshot_date:date year:int month:int aum:float return_ytd:float benchmark_return_ytd:float active_alpha_ytd:float cash_pct:float account_type:text",
    "fact_transactions": "txn_id:int client_id:int advisor_id:int security_id:int txn_date:date txn_type:text shares:float price:float amount:float",
}
US_STATES = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split())
ALLOWED = {  # table -> column -> set of allowed text values
    "dim_advisor": {"region": {"Northeast", "Southeast", "Mid-Atlantic", "Midwest", "West", "Southwest"},
                    "certifications": {"None", "CFA", "CFP", "CIMA", "CFP, CFA", "CFP, CIMA", "CFA, CIMA", "CFP, CFA, CIMA"}},
    "dim_client": {"state": US_STATES,
                   "risk_profile": {"Conservative", "Moderately Conservative", "Balanced", "Moderately Aggressive", "Aggressive"},
                   "client_tier": {"Retail", "HNW", "UHNW"},
                   "primary_account_type": {"Taxable", "IRA", "Roth IRA", "Trust", "529"},
                   "is_active": {"True", "False"}},
    "dim_date": {"day_of_week": {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"},
                 "quarter": {"1", "2", "3", "4"}, "is_month_end": {"0", "1"}, "is_quarter_end": {"0", "1"},
                 "is_year_end": {"0", "1"}, "is_trading_day": {"0", "1"}},
    "dim_security": {"asset_class": {"Equity", "Fixed Income", "Alternative", "Cash Equivalent"}, "is_etf": {"True", "False"}},
    "fact_fees": {"fee_type": {"Management", "Advisory", "Custodial", "Performance"}},
    "fact_portfolio_snapshot": {"account_type": {"Taxable", "IRA", "Roth IRA", "Trust", "529"}},
    "fact_transactions": {"txn_type": {"Buy", "Sell", "Dividend", "Deposit", "Withdrawal", "Advisory Fee"}},
}
# table -> column -> (min, max, severity if violated).  None = unbounded.
RANGES = {
    "dim_advisor": {"years_experience": (0, 50, "ERROR"), "aum_target_mm": (1, None, "ERROR")},
    "dim_client": {"age": (18, 110, "ERROR"), "initial_aum": (0.01, None, "ERROR")},
    "dim_date": {"year": (2020, 2024, "ERROR"), "month": (1, 12, "ERROR"), "week_of_year": (1, 53, "ERROR")},
    "dim_security": {"expense_ratio_bps": (0, 200, "ERROR")},
    "fact_fees": {"aum_basis": (0.01, None, "ERROR"), "bps_charged": (0, 100, "WARN"), "amount": (0, None, "ERROR")},
    "fact_portfolio_snapshot": {"year": (2020, 2024, "ERROR"), "month": (1, 12, "ERROR"), "aum": (0, None, "ERROR"),
                                "return_ytd": (-1, 5, "WARN"), "benchmark_return_ytd": (-1, 5, "WARN"),
                                "active_alpha_ytd": (-6, 6, "WARN"), "cash_pct": (0, 1, "ERROR")},
    "fact_transactions": {"price": (0.01, None, "ERROR"), "amount": (0.01, None, "ERROR")},
}
DATE_WINDOW = (pd.Timestamp("2020-01-01"), pd.Timestamp("2024-12-31"))  # dim_date coverage
SENTINELS = {"none", "null", "nan", "n/a", "na", "-", "--", "?", "unknown", "tbd", "#n/a", "missing"}
# near-duplicate definitions: table -> list of (columns that must match, note)
NEAR_DUPES = {
    "dim_client": [(["first_name", "last_name", "zip_code"], "same name + ZIP"),
                   (["first_name", "last_name", "age", "city"], "same name + age + city")],
    "dim_security": [(["name"], "same security name, different ticker/id")],
    "dim_advisor": [(["first_name", "last_name"], "same advisor name")],
    "fact_fees": [(["client_id", "fee_date", "fee_type"], "same client/date/type charged twice"),
                  (["client_id", "fee_date", "amount"], "same client/date/amount")],
    "fact_portfolio_snapshot": [(["client_id", "snapshot_date"], "two snapshots for one client-month")],
    "fact_transactions": [(["client_id", "txn_date", "txn_type", "amount"], "same client/date/type/amount")],
}
TOL_MONEY = 0.01  # tolerance when recomputing money columns (rounded to 2 dp)

# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------
RE_INT = re.compile(r"^[+-]?\d+$")
RE_INT_FLOATFMT = re.compile(r"^[+-]?\d+\.0+$")
RE_FLOAT = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")
RE_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_PCT = re.compile(r"^[+-]?\d+(\.\d+)?\s*%$")
RE_CURRENCY = re.compile(r"^[+-]?\s*[$€£]\s*[\d,]+(\.\d+)?$")
RE_COMMA_NUM = re.compile(r"^[+-]?\d{1,3}(,\d{3})+(\.\d+)?$")
SEV_ORDER = {"ERROR": 0, "WARN": 1, "INFO": 2}

FINDINGS = []  # collected by add()


def add(group, table, column, check, severity, affected, total, detail="", examples=""):
    """Record one check result. FAIL when affected > 0. severity = tag if it fails."""
    FINDINGS.append({
        "group": group, "table": table, "column": column, "check": check,
        "status": "FAIL" if affected > 0 else "PASS",
        "severity": severity, "rows_affected": int(affected), "rows_checked": int(total),
        "pct_affected": round(100.0 * affected / total, 3) if total else 0.0,
        "detail": detail, "examples": str(examples)[:200],
    })


def ex(series, n=4):
    """A few distinct example values for the report."""
    return "|".join(map(str, pd.Series(series).dropna().astype(str).unique()[:n]))


def to_num(s):
    return pd.to_numeric(s, errors="coerce")


def blank_mask(s):
    return s.str.strip() == ""


def find_file(data_dir, stem):
    """Accepts 'dim_advisor.csv' or browser-download names like 'dim_advisor (1).csv'."""
    exact = data_dir / f"{stem}.csv"
    if exact.exists():
        return exact
    hits = sorted(data_dir.glob(f"{stem}*.csv"), key=lambda p: (len(p.name), p.name))
    if len(hits) > 1:
        raise SystemExit(f"ERROR: {len(hits)} files match '{stem}*.csv' in {data_dir}: {[h.name for h in hits]}. Keep one and rerun.")
    return hits[0] if hits else None


def load_tables(data_dir):
    tables = {}
    for stem in TABLE_FILES:
        f = find_file(data_dir, stem)
        if f is None:
            sys.exit(f"ERROR: cannot find {stem}.csv in {data_dir}")
        tables[stem] = pd.read_csv(f, dtype=str, keep_default_na=False)
        print(f"  loaded {stem:<26} <- {f.name:<34} {tables[stem].shape[0]:>8,} rows x {tables[stem].shape[1]} cols")
    return tables


def locate_data_dir(project_root, cli_dir):
    if cli_dir:
        return Path(cli_dir).resolve()
    for cand in [project_root / "Wildcat Capital", project_root / "data" / "raw", project_root]:
        if cand.is_dir() and find_file(cand, "dim_advisor"):
            return cand
    sys.exit("ERROR: raw CSVs not found. Pass --data-dir.")


# ----------------------------------------------------------------------------
# PART 1 - GENERIC PROFILER (works on any table)
# ----------------------------------------------------------------------------
def shape_of(v, coarse=True):
    """Value 'shape': digits->9, letters->a/A, runs collapsed when coarse."""
    s = re.sub(r"[A-Z]", "A", v)
    s = re.sub(r"[a-z]", "a", s)
    s = re.sub(r"\d", "9", s)
    if coarse:
        s = re.sub(r"(.)\1+", r"\1", s)
    return s


def infer_type(vals):
    """Infer the dominant type of non-blank text values. Returns (type, share_parsing)."""
    n = len(vals)
    if n == 0:
        return "empty", 1.0
    cands = {
        "bool": vals.isin(["True", "False", "true", "false", "TRUE", "FALSE"]).mean(),
        "date": vals.str.match(RE_DATE).mean(),
        "int": (vals.str.match(RE_INT) | vals.str.match(RE_INT_FLOATFMT)).mean(),
        "float": vals.str.match(RE_FLOAT).mean(),
    }
    for t in ("bool", "date", "int", "float"):
        if cands[t] >= 0.90:
            return t, cands[t]
    return "text", 1.0


def profile_table(table, df, expected=None):
    """One dict per column. Generic: no table-specific logic."""
    expected = expected or {}
    rows = []
    n = len(df)
    for col in df.columns:
        s = df[col]
        st = s.str.strip()
        blank = st == ""
        nonblank = s[~blank]
        nb = len(nonblank)
        inferred, _ = infer_type(nonblank.str.strip())
        etype = expected.get(col, inferred)
        # parse failures relative to the type we expect
        v = nonblank.str.strip()
        if etype in ("int", "zip"):
            ok = v.str.match(RE_INT) | (v.str.match(RE_INT_FLOATFMT) if etype == "int" else False)
            if etype == "zip":
                ok = v.str.match(r"^\d{5}$")
        elif etype == "float":
            ok = v.str.match(RE_FLOAT)
        elif etype == "date":
            ok = v.str.match(RE_DATE) & pd.to_datetime(v, format="%Y-%m-%d", errors="coerce").notna()
        elif etype == "bool":
            ok = v.isin(["True", "False"])
        elif etype == "flag":
            ok = v.isin(["0", "1"])
        else:
            ok = pd.Series(True, index=v.index)
        fail = nonblank[~ok]
        # shapes
        shape_col = nonblank.map(shape_of)
        shapes = shape_col.value_counts()
        top = "; ".join(f"{k} ({100*c/nb:.1f}%)" for k, c in shapes.head(3).items()) if nb else ""
        dom_share = shapes.iloc[0] / nb if nb else 1.0
        minority = shapes.iloc[1:] if len(shapes) > 1 else shapes.iloc[0:0]
        minority_ex = "; ".join(f"{k}: {ex(nonblank[shape_col == k], 2)}" for k in minority.head(3).index)
        # whitespace / odd characters
        lead_trail = int((s != s.str.strip()).sum())
        dbl_space = int(s.str.contains(r"\s{2,}", regex=True).sum())
        odd_chars = int(s.str.contains(r"[\x00-\x08\x0b-\x1f ​]", regex=True).sum())
        only_space = int(((s != "") & blank).sum())
        # numeric summary (rows that parse)
        numv = to_num(v) if etype in ("int", "float", "zip") or inferred in ("int", "float") else pd.Series(dtype=float)
        numv = numv.dropna()
        distinct = s.nunique()
        text_variants = 0
        if inferred == "text" and distinct <= 200:
            key = nonblank.str.lower().str.replace(r"[^a-z0-9]", "", regex=True)
            text_variants = int(nonblank.groupby(key).nunique().gt(1).sum())  # case/punct variants of the same label
        # mixed formats: any non-dominant shape inside a typed column, or small minority shape in text
        mixed = 0
        if inferred in ("int", "float", "date", "bool"):
            mixed = int(len(fail)) + int(v[ok].str.match(RE_INT_FLOATFMT).sum() if etype == "int" else 0)
        elif len(shapes) > 1 and dom_share >= 0.90 and distinct > 2:
            mixed = int(minority.sum())
        rows.append({
            "table": table, "column": col, "n_rows": n,
            "null_blank_count": int(blank.sum()), "null_blank_pct": round(100 * blank.mean(), 3),
            "sentinel_text_count": int(st.str.lower().isin(SENTINELS).sum()),
            "distinct_count": int(distinct), "distinct_pct": round(100 * distinct / n, 3) if n else 0,
            "inferred_type": inferred, "expected_type": etype,
            "dominant_shapes": top, "n_shapes": int(len(shapes)),
            "mixed_format_count": mixed, "minority_shape_examples": minority_ex,
            "parse_fail_count": int(len(fail)), "parse_fail_pct": round(100 * len(fail) / nb, 3) if nb else 0.0,
            "parse_fail_examples": ex(fail, 4),
            "pct_string_count": int(v.str.match(RE_PCT).sum()),
            "currency_string_count": int(v.str.match(RE_CURRENCY).sum() + v.str.match(RE_COMMA_NUM).sum()),
            "float_formatted_int_count": int(v.str.match(RE_INT_FLOATFMT).sum()) if etype == "int" else 0,
            "leading_zero_count": int(v.str.match(r"^0\d+").sum()),
            "leading_trailing_ws_count": lead_trail, "double_space_count": dbl_space,
            "odd_char_count": odd_chars, "whitespace_only_count": only_space,
            "case_or_punct_variant_groups": text_variants,
            "num_min": float(numv.min()) if len(numv) else np.nan,
            "num_max": float(numv.max()) if len(numv) else np.nan,
            "num_mean": round(float(numv.mean()), 6) if len(numv) else np.nan,
            "min_length": int(v.str.len().min()) if nb else 0, "max_length": int(v.str.len().max()) if nb else 0,
        })
    return pd.DataFrame(rows)


def generic_findings(prof):
    """Turn the generic profile into findings (Group 1: column level)."""
    G = "1 Column level"
    for r in prof.itertuples():
        t, c, n = r.table, r.column, r.n_rows
        is_key = c == PK.get(t) or any((t, c) == (a, b) for a, b, _, _ in FOREIGN_KEYS)
        sev_ws = "ERROR" if is_key else "WARN"
        add(G, t, c, f"values parse as expected type ({r.expected_type})", "ERROR", r.parse_fail_count,
            n - r.null_blank_count, f"inferred={r.inferred_type}", r.parse_fail_examples)
        add(G, t, c, "percent/currency/thousand-separator text in column", "ERROR",
            r.pct_string_count + r.currency_string_count, n,
            "text like '12.3%' or '$1,200' is not a number until converted", "")
        if r.expected_type == "int":
            add(G, t, c, "integers stored in float format (45.0)", "ERROR" if is_key else "WARN",
                r.float_formatted_int_count, n, "breaks text joins with the parent key" if is_key else "", "")
        add(G, t, c, "leading/trailing whitespace", sev_ws, r.leading_trailing_ws_count, n, "", "")
        add(G, t, c, "double spaces / control chars / NBSP", "WARN", r.double_space_count + r.odd_char_count, n, "", "")
        legit_sentinel = c in {k for k, v in ALLOWED.get(t, {}).items() if any(x.lower() in SENTINELS for x in v)}
        add(G, t, c, "sentinel text standing in for null (None/N/A/null...)", "INFO" if legit_sentinel else "WARN",
            r.sentinel_text_count, n,
            "the sentinel is a listed allowed value (e.g. certifications='None' = no certification): consistent text, "
            "but it is NOT a true null" if legit_sentinel else "text placeholder for missing data - convert or confirm", "")
        if r.inferred_type == "text":
            add(G, t, c, "case/punctuation variants of the same label", "WARN", r.case_or_punct_variant_groups,
                r.distinct_count, "", "")
        if r.inferred_type == "text" and r.mixed_format_count:
            add(G, t, c, "mixed formats (minority value shape in an otherwise uniform column)", "WARN",
                r.mixed_format_count, n, r.minority_shape_examples, "")
        # nulls: key columns must never be blank; everything else is INFO for review
        if is_key and (t, c) not in NULLABLE_FK:
            add(G, t, c, "key column has no blanks", "ERROR", r.null_blank_count, n, "", "")
        elif r.null_blank_count:
            add(G, t, c, "blank/missing values present", "INFO", r.null_blank_count, n,
                "check whether blanks are legitimate structure or a defect (see group 2)", "")


# ----------------------------------------------------------------------------
# PART 2 - CHECK GROUPS
# ----------------------------------------------------------------------------
def group1_column_rules(T):
    G = "1 Column level"
    for t, df in T.items():
        n = len(df)
        pk = PK.get(t)  # a table with no configured key still gets every other check
        if pk in df.columns:
            dup = df[pk].duplicated(keep=False) & ~blank_mask(df[pk])
            add(G, t, pk, "primary key unique", "ERROR", dup.sum(), n, "", ex(df.loc[dup, pk]))
        for nk in NATURAL_KEYS.get(t, []):
            d = df[nk].duplicated(keep=False) & ~blank_mask(df[nk])
            add(G, t, nk, "natural key unique", "WARN", d.sum(), n, "", ex(df.loc[d, nk]))
        # allowed values
        for col, allowed in ALLOWED.get(t, {}).items():
            bad = ~df[col].isin(allowed) & ~blank_mask(df[col])
            add(G, t, col, "values in allowed list", "ERROR", bad.sum(), n,
                f"{df.loc[bad, col].nunique()} distinct unexpected values", ex(df.loc[bad, col], 6))
        # numeric ranges
        for col, (lo, hi, sev) in RANGES.get(t, {}).items():
            x = to_num(df[col])
            bad = x.notna() & (((x < lo) if lo is not None else False) | ((x > hi) if hi is not None else False))
            add(G, t, col, f"within range [{lo}, {hi}]", sev, bad.sum(), int(x.notna().sum()),
                f"observed min={x.min():g} max={x.max():g}", ex(df.loc[bad, col]))
        # date columns: valid and inside the dim_date window
        for col in [c for c in df.columns if EXPECTED_TYPE.get(t, "").find(f"{c}:date") >= 0]:
            d = pd.to_datetime(df[col], format="%Y-%m-%d", errors="coerce")
            bad = d.notna() & ((d < DATE_WINDOW[0]) | (d > DATE_WINDOW[1]))
            if t == "dim_client":  # signup dates may pre-date the 2020 calendar window
                bad = d.notna() & (d > DATE_WINDOW[1])
            add(G, t, col, "date inside calendar window (2020-2024)" if t != "dim_client" else "date not after 2024-12-31",
                "WARN", bad.sum(), int(d.notna().sum()), f"min={d.min().date()} max={d.max().date()}", ex(df.loc[bad, col]))
        # zip leading zeros survived
        if "zip_code" in df.columns:
            add(G, t, "zip_code", "ZIP is 5 digits (leading zeros preserved)", "ERROR",
                (~df["zip_code"].str.match(r"^\d{5}$")).sum(), n, "", "")
    # US state codes vs full names handled by allowed list above


def group2_single_table(T):
    G = "2 Single-table rules"
    for t, df in T.items():
        n = len(df)
        pk = PK.get(t)
        body = df.drop(columns=[pk]) if pk in df.columns else df
        d = body.duplicated(keep=False)
        add(G, t, "(all but PK)" if pk in df.columns else "(all columns)", "exact duplicate rows ignoring the primary key", "ERROR", d.sum(), n, "", "")
        for cols, note in NEAR_DUPES.get(t, []):
            cols = [c for c in cols if c in df.columns]
            k = df[cols].apply(lambda s: s.str.strip().str.lower())
            m = k.duplicated(keep=False) & ~(k == "").any(axis=1)
            add(G, t, "+".join(cols), f"near-duplicate: {note}", "WARN", m.sum(), n,
                f"{k[m].drop_duplicates().shape[0]} duplicate groups", ex(df.loc[m, pk]))

    # Everything below is business-specific to the eight Wildcat tables; it runs only when they are all present.
    if not set(TABLE_FILES) <= set(T):
        return

    # --- dim_date: derived columns agree with the date -----------------------
    dd = T["dim_date"]
    dt = pd.to_datetime(dd["date"], errors="coerce")
    n = len(dd)
    iso = dt.dt.isocalendar()
    rules = {
        "year": dt.dt.year.astype("Int64").astype(str), "month": dt.dt.month.astype("Int64").astype(str),
        "quarter": dt.dt.quarter.astype("Int64").astype(str), "month_name": dt.dt.month_name(),
        "day_of_week": dt.dt.day_name(), "week_of_year": iso.week.astype("Int64").astype(str),
        "is_month_end": dt.dt.is_month_end.astype(int).astype(str),
        "is_quarter_end": dt.dt.is_quarter_end.astype(int).astype(str),
        "is_year_end": dt.dt.is_year_end.astype(int).astype(str),
    }
    for col, expect in rules.items():
        add(G, "dim_date", col, "derived column agrees with date", "ERROR", (dd[col] != expect).sum(), n, "", "")
    add(G, "dim_date", "is_trading_day", "weekend flagged as trading day", "ERROR",
        ((dt.dt.dayofweek >= 5) & (dd["is_trading_day"] == "1")).sum(), n, "", "")
    gaps = dt.sort_values().diff().dt.days.dropna()
    add(G, "dim_date", "date", "calendar has no gaps (1 row per day)", "ERROR", (gaps != 1).sum(), n, "", "")
    wk = ((dt.dt.dayofweek < 5) & (dd["is_trading_day"] == "0")).sum()
    add(G, "dim_date", "is_trading_day", "weekday marked non-trading (holidays)", "INFO", wk, n,
        "expected for market holidays (~9-10 per year)", "")

    # --- dim_client ----------------------------------------------------------
    c = T["dim_client"]
    n = len(c)
    aum = to_num(c["initial_aum"])
    exp_tier = np.select([aum < 500_000, aum < 5_000_000], ["Retail", "HNW"], "UHNW")
    add(G, "dim_client", "client_tier", "tier agrees with initial_aum (<500k Retail, <5M HNW, else UHNW)", "WARN",
        (aum.notna() & (c["client_tier"] != exp_tier)).sum(), n, "", "")
    since = pd.to_datetime(c["client_since"], errors="coerce")
    age_at_join = to_num(c["age"]) - (pd.Timestamp("2024-12-31").year - since.dt.year)
    add(G, "dim_client", "age/client_since", "implied age at account opening < 18", "WARN",
        (age_at_join < 18).sum(), n, "age assumed measured at end of 2024", "")
    add(G, "dim_client", "risk_profile", "risk_profile blank", "WARN", blank_mask(c["risk_profile"]).sum(), n,
        "profile missing for some clients; see group 4 for what the data implies", "")

    # --- dim_security: blanks are structure, not defects ----------------------
    s = T["dim_security"]
    n = len(s)
    etf = s["is_etf"] == "True"
    add(G, "dim_security", "sector", "sector blank <=> is_etf=True (blank is legitimate structure)", "INFO",
        (blank_mask(s["sector"]) != etf).sum(), n, "0 rows violate => blanks are structural", "")
    add(G, "dim_security", "expense_ratio_bps", "expense ratio present <=> is_etf=True", "INFO",
        (blank_mask(s["expense_ratio_bps"]) == etf).sum(), n, "0 rows violate => blanks are structural", "")
    amap = s.groupby("asset_class")["benchmark_id"].nunique()
    add(G, "dim_security", "benchmark_id", "asset classes mapping to >1 benchmark", "INFO", int((amap > 1).sum()), len(amap),
        "Equity maps to several benchmarks (large cap / small cap / intl) - plausible", "")

    # --- fact_fees -----------------------------------------------------------
    f = T["fact_fees"]
    n = len(f)
    recomputed = to_num(f["aum_basis"]) * to_num(f["bps_charged"]) / 10000 / 12
    diff = (recomputed - to_num(f["amount"])).abs()
    add(G, "fact_fees", "amount", "amount = aum_basis x bps / 10,000 / 12 (within 1 cent)", "ERROR",
        (diff > TOL_MONEY).sum(), n, f"max abs diff={diff.max():.4f}", "")
    add(G, "fact_fees", "fee_date", "fee dated on the 1st of the month", "WARN", (~f["fee_date"].str.endswith("-01")).sum(), n, "", "")
    add(G, "fact_fees", "aum_basis", "aum_basis at exactly 1,000 (possible floor/clamp)", "WARN",
        (to_num(f["aum_basis"]) == 1000).sum(), n, "round-number minimum suggests a floor applied upstream", "")

    # --- fact_portfolio_snapshot --------------------------------------------
    p = T["fact_portfolio_snapshot"]
    n = len(p)
    ret, bmr, alpha = to_num(p["return_ytd"]), to_num(p["benchmark_return_ytd"]), to_num(p["active_alpha_ytd"])
    pm = ret.notna() & bmr.notna() & alpha.notna()
    add(G, "fact_portfolio_snapshot", "active_alpha_ytd", "alpha = return_ytd - benchmark_return_ytd (1e-5)", "ERROR",
        (pm & ((ret - bmr - alpha).abs() > 1e-5)).sum(), int(pm.sum()), "rows with a text % in return_ytd skipped", "")
    sd = pd.to_datetime(p["snapshot_date"], errors="coerce")
    add(G, "fact_portfolio_snapshot", "year/month", "year and month agree with snapshot_date", "ERROR",
        ((sd.dt.year.astype("Int64").astype(str) != p["year"]) | (sd.dt.month.astype("Int64").astype(str) != p["month"])).sum(), n, "", "")
    add(G, "fact_portfolio_snapshot", "aum", "aum at exactly 1,000 (possible floor/clamp)", "WARN",
        (to_num(p["aum"]) == 1000).sum(), n, "round-number minimum suggests a floor applied upstream; true AUM unknown", "")
    add(G, "fact_portfolio_snapshot", "return_ytd", "return_ytd > +500% (implausible)", "WARN", (ret > 5).sum(), int(ret.notna().sum()),
        "implausible for one year; return and AUM history disagree on these rows - flag, do not correct", ex(p.loc[ret > 5, "return_ytd"]))

    # --- fact_transactions ---------------------------------------------------
    x = T["fact_transactions"]
    n = len(x)
    sh, pr, am = to_num(x["shares"]), to_num(x["price"]), to_num(x["amount"])
    trade = x["txn_type"].isin(["Buy", "Sell", "Dividend"])
    flow = x["txn_type"].isin(["Deposit", "Withdrawal", "Advisory Fee"])
    add(G, "fact_transactions", "security_id/shares/price", "Buy/Sell/Dividend rows missing security, shares or price", "ERROR",
        (trade & (blank_mask(x["security_id"]) | blank_mask(x["shares"]) | blank_mask(x["price"]))).sum(), int(trade.sum()), "", "")
    add(G, "fact_transactions", "security_id/shares/price", "cash-flow rows carrying security, shares or price", "WARN",
        (flow & ~(blank_mask(x["security_id"]) & blank_mask(x["shares"]) & blank_mask(x["price"]))).sum(), int(flow.sum()),
        "blank on Deposit/Withdrawal/Advisory Fee is legitimate structure", "")
    add(G, "fact_transactions", "shares", "negative shares", "ERROR", (sh < 0).sum(), int(sh.notna().sum()),
        "by type: " + str(x.loc[sh < 0, "txn_type"].value_counts().to_dict()), ex(x.loc[sh < 0, "txn_id"]))
    m = sh.notna() & pr.notna()
    signed = (sh * pr - am).abs() > 1
    absd = (sh.abs() * pr - am).abs() > 1
    add(G, "fact_transactions", "amount", "amount = shares x price (signed, 1.00 tolerance)", "ERROR", (m & signed).sum(), int(m.sum()),
        f"of these, {(m & signed & ~absd).sum()} DO match when |shares| is used (sign problem, not a wrong amount)",
        ex(x.loc[m & signed, "txn_id"]))
    add(G, "fact_transactions", "amount", "amount = |shares| x price (1.00 tolerance)", "ERROR", (m & absd).sum(), int(m.sum()),
        "if 0 here, the only problem is the sign of shares on Buy rows", "")
    tdays = T["dim_date"].set_index("date")["is_trading_day"]
    nt = x["txn_type"].isin(["Buy", "Sell"]) & (x["txn_date"].map(tdays) == "0")
    add(G, "fact_transactions", "txn_date", "Buy/Sell executed on a non-trading day", "WARN", nt.sum(), int(x["txn_type"].isin(["Buy", "Sell"]).sum()),
        "markets closed; may be synthetic-data artefact - flag, do not delete", "")


def check_referential_integrity(fact_df, fact_key, dim_df, dim_key):
    """Exact-string join check. Returns match rate, orphan rows, distinct orphan keys, null-key rate."""
    k = fact_df[fact_key]
    null = blank_mask(k)
    present = ~null
    orphan = present & ~k.isin(set(dim_df[dim_key]))
    n_present = int(present.sum())
    return {"rows": len(fact_df), "null_key_rows": int(null.sum()), "null_key_rate": round(100 * null.mean(), 3),
            "orphan_rows": int(orphan.sum()), "distinct_orphan_keys": int(k[orphan].nunique()),
            "match_rate": round(100 * (n_present - orphan.sum()) / n_present, 3) if n_present else 100.0,
            "orphan_examples": ex(k[orphan], 5)}


def group3_referential(T):
    G = "3 Referential integrity"
    for child, ccol, parent, pcol in FOREIGN_KEYS:
        if child not in T or parent not in T:
            continue  # relationship not applicable to the tables supplied
        fk, dm = T[child], T[parent]
        r = check_referential_integrity(fk, ccol, dm, pcol)
        # same test after normalising 45.0 -> 45 so we can separate "format" problems from "missing parent"
        norm = fk.assign(**{ccol: fk[ccol].str.strip().str.replace(r"\.0+$", "", regex=True)})
        r2 = check_referential_integrity(norm, ccol, dm, pcol)
        name = f"{child}.{ccol} -> {parent}.{pcol}"
        detail = f"match {r['match_rate']}% ({r['distinct_orphan_keys']} distinct orphan keys)"
        if r["orphan_rows"] != r2["orphan_rows"]:
            detail += f"; after fixing float-format keys: {r2['orphan_rows']} orphans ({r2['match_rate']}% match)"
        add(G, child, ccol, f"FK exists in parent: {name}", "ERROR", r["orphan_rows"], r["rows"] - r["null_key_rows"], detail, r["orphan_examples"])
        if r["null_key_rows"]:
            sev = "INFO" if (child, ccol) in NULLABLE_FK else "ERROR"
            add(G, child, ccol, f"FK is never blank: {name}", sev, r["null_key_rows"], r["rows"],
                "blank is legitimate for cash-flow rows (no security involved)" if sev == "INFO" else "", "")
        # parents that nothing points at (INFO: unused dimension members). Skipped for dim_date:
        # monthly facts only touch ~60 of 1,827 calendar days by design.
        if parent != "dim_date":
            unused = ~dm[pcol].isin(set(fk[ccol].str.replace(r"\.0+$", "", regex=True)))
            add(G, parent, pcol, f"parent rows never referenced by {child}.{ccol}", "INFO", unused.sum(), len(dm),
                "dimension members with no child rows (reverse integrity; not a join failure)", ex(dm.loc[unused, pcol]))


def group4_cross_table(T):
    G = "4 Cross-table business rules"
    if not set(TABLE_FILES) <= set(T):
        return  # these rules are written for the eight Wildcat tables
    cl, fee, snap, tx = T["dim_client"], T["fact_fees"], T["fact_portfolio_snapshot"], T["fact_transactions"]
    cl_idx = cl.set_index("client_id")

    # facts carry the same advisor as the client's advisor of record
    for name, f in [("fact_fees", fee), ("fact_portfolio_snapshot", snap), ("fact_transactions", tx)]:
        mapped = f["client_id"].map(cl_idx["advisor_id"])
        bad = mapped.notna() & (mapped != f["advisor_id"])
        add(G, name, "advisor_id", "fact advisor_id equals dim_client.advisor_id", "ERROR", bad.sum(), int(mapped.notna().sum()), "", "")

    # snapshot account type vs client primary account type
    mp = snap["client_id"].map(cl_idx["primary_account_type"])
    add(G, "fact_portfolio_snapshot", "account_type", "snapshot account_type equals dim_client.primary_account_type", "WARN",
        (mp.notna() & (mp != snap["account_type"])).sum(), int(mp.notna().sum()), "", "")

    # fee AUM basis equals snapshot AUM for the same client-month
    m = fee.merge(snap[["client_id", "snapshot_date", "aum"]], left_on=["client_id", "fee_date"],
                  right_on=["client_id", "snapshot_date"], how="left")
    miss = m["aum"].isna()
    add(G, "fact_fees", "client_id+fee_date", "fee has a matching portfolio snapshot (same client-month)", "ERROR", miss.sum(), len(m), "", "")
    d = (to_num(m["aum_basis"]) - to_num(m["aum"])).abs()
    add(G, "fact_fees", "aum_basis", "fee aum_basis equals snapshot aum for the same client-month", "ERROR",
        (~miss & (d > TOL_MONEY)).sum(), int((~miss).sum()), f"max abs diff={d.max():.2f}", "")
    k = set(zip(fee["client_id"], fee["fee_date"]))
    nofee = ~pd.Series(list(zip(snap["client_id"], snap["snapshot_date"]))).isin(k)
    add(G, "fact_portfolio_snapshot", "client_id+snapshot_date", "snapshot months with no fee row", "INFO", nofee.sum(), len(snap),
        "possible: no billing in some months / low-AUM accounts - not necessarily wrong", "")

    # activity before the client existed (compare at MONTH level; snapshots/fees are dated the 1st)
    cs_month = cl_idx["client_since"].str[:7]
    for name, f, col in [("fact_fees", fee, "fee_date"), ("fact_portfolio_snapshot", snap, "snapshot_date"), ("fact_transactions", tx, "txn_date")]:
        cm = f["client_id"].map(cs_month)
        add(G, name, col, "activity dated before the client's client_since month", "WARN",
            (cm.notna() & (f[col].str[:7] < cm)).sum(), int(cm.notna().sum()), "month-level comparison", "")

    # inactive clients should not have recent snapshots; active clients should reach the last month
    last = snap.groupby("client_id")["snapshot_date"].max()
    inactive = cl.loc[cl["is_active"] == "False", "client_id"]
    active = cl.loc[cl["is_active"] == "True", "client_id"]
    add(G, "dim_client", "is_active", "inactive clients still have snapshots in the final month (2024-12)", "WARN",
        (last.reindex(inactive) == "2024-12-01").sum(), len(inactive), "", "")
    la = last.reindex(active).dropna()
    add(G, "dim_client", "is_active", "active clients whose snapshots stop before 2024-12", "WARN", (la < "2024-12-01").sum(), len(la), "", "")
    add(G, "dim_client", "client_id", "clients with no facts at all (no snapshots, fees or transactions)", "INFO",
        (~cl["client_id"].isin(set(snap["client_id"]) | set(fee["client_id"]) | set(tx["client_id"]))).sum(), len(cl),
        "dimension members that were never used", "")

    # blank risk_profile: what do the facts imply? (supports a fill-vs-flag decision later)
    bench_by_client = snap.groupby("client_id")["benchmark_id"].agg(lambda s: s.mode().iat[0])
    risk_bm = (cl.assign(b=cl["client_id"].map(bench_by_client)).loc[lambda d: d["risk_profile"].str.strip() != ""]
               .groupby("risk_profile")["b"].agg(lambda s: s.mode().iat[0]))
    one_to_one = (cl.assign(b=cl["client_id"].map(bench_by_client)).loc[lambda d: d["risk_profile"].str.strip() != ""]
                  .groupby("risk_profile")["b"].nunique().max())
    blank_ids = cl.loc[blank_mask(cl["risk_profile"]), "client_id"]
    implied = blank_ids.map(bench_by_client).value_counts().to_dict()
    add(G, "dim_client", "risk_profile", "blank risk_profile: benchmark in snapshots implies a profile", "INFO",
        len(blank_ids), len(cl), f"each known profile maps to {one_to_one} benchmark; blank clients' benchmarks={implied}; "
        f"benchmark->profile: {risk_bm.to_dict()}", "")

    # transaction advisory-fee debits vs fee table (do the two systems describe the same fact?)
    adv_tx = tx[tx["txn_type"] == "Advisory Fee"].assign(y=lambda d: d["txn_date"].str[:4], a=lambda d: to_num(d["amount"]))
    adv_fee = fee.assign(y=fee["fee_date"].str[:4], a=to_num(fee["amount"]))
    tot_tx = adv_tx.groupby(["client_id", "y"])["a"].sum()
    tot_fee = adv_fee.groupby(["client_id", "y"])["a"].sum()
    j = pd.concat([tot_tx, tot_fee], axis=1, keys=["tx", "fee"]).dropna()
    off = ((j["tx"] - j["fee"]).abs() / j["fee"] > 0.05).sum()
    add(G, "fact_transactions vs fact_fees", "amount", "yearly 'Advisory Fee' debits within 5% of fact_fees totals (per client-year)", "WARN",
        off, len(j), f"total tx debits={adv_tx['a'].sum():,.0f} vs total fees={adv_fee['a'].sum():,.0f}; the two tables do not reconcile - "
        "investigate before assuming either is the source of truth", "")


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="HW4 Part A - profile raw Wildcat Capital tables")
    ap.add_argument("--data-dir", help="folder with the 8 raw CSVs (default: auto-detect)")
    ap.add_argument("--reports-dir", help="output folder (default: <project>/reports)")
    args = ap.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    data_dir = locate_data_dir(project_root, args.data_dir)
    out_dir = Path(args.reports_dir) if args.reports_dir else project_root / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Project root : {project_root}\nRaw data dir : {data_dir}\nReports dir  : {out_dir}\n\nLoading (dtype=str, keep_default_na=False):")
    T = load_tables(data_dir)

    # Part 1: generic profile
    expected = {t: dict(p.split(":") for p in spec.split()) for t, spec in EXPECTED_TYPE.items()}
    prof = pd.concat([profile_table(t, df, expected.get(t)) for t, df in T.items()], ignore_index=True)
    generic_findings(prof)

    # Part 2: four groups
    group1_column_rules(T)
    group2_single_table(T)
    group3_referential(T)
    group4_cross_table(T)

    summary = pd.DataFrame(FINDINGS)
    summary["fail_rank"] = summary["status"].map({"FAIL": 0, "PASS": 1})
    summary["sev_rank"] = summary["severity"].map(SEV_ORDER)
    summary = (summary.sort_values(["fail_rank", "sev_rank", "group", "table", "column"], kind="stable")
               .drop(columns=["fail_rank", "sev_rank"]).reset_index(drop=True))
    # a passing check is reported as INFO-level evidence, not as an issue
    summary.insert(0, "finding_id", [f"F{i+1:03d}" for i in range(len(summary))])

    prof.to_csv(out_dir / "profile_raw.csv", index=False, encoding="utf-8")
    summary.to_csv(out_dir / "dq_summary_raw.csv", index=False, encoding="utf-8")

    # console report
    fails = summary[summary["status"] == "FAIL"]
    print(f"\nProfile  : {len(prof)} columns profiled across {len(T)} tables -> {out_dir / 'profile_raw.csv'}")
    print(f"Checks   : {len(summary)} run, {len(fails)} FAIL, {(summary.status == 'PASS').sum()} PASS -> {out_dir / 'dq_summary_raw.csv'}")
    print("\nFAILED checks by severity:", fails["severity"].value_counts().reindex(["ERROR", "WARN", "INFO"]).fillna(0).astype(int).to_dict())
    for sev in ["ERROR", "WARN", "INFO"]:
        sub = fails[fails["severity"] == sev]
        if sub.empty:
            continue
        print(f"\n===== {sev} ({len(sub)}) =====")
        for r in sub.itertuples():
            print(f"[{r.finding_id}] {r.table}.{r.column}: {r.check} -> {r.rows_affected:,} of {r.rows_checked:,} ({r.pct_affected}%)"
                  + (f"\n        {r.detail}" if r.detail else "") + (f"\n        e.g. {r.examples}" if r.examples else ""))
    print("\nDone. Raw files were not modified.")


if __name__ == "__main__":
    main()
