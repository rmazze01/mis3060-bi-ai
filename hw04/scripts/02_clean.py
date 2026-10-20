"""
HW4 Part C - Cleaning program: 02_clean.py
==========================================
Reads the eight raw Wildcat Capital tables (never modified) and writes a clean
copy of all eight, plus a full audit trail.  Every step implements one entry of
decision_log.md (D01-D08) and is followed by a before/after check and `assert`s.
If a fix did not do what the log claims, the script stops.

Outputs (relative to the project folder, i.e. hw04/):
    data/clean/<8 tables>.csv           same file names + same columns (+ flag_ columns)
    data/clean/README_clean.md          relationships, BI column types, flags, limitations
    data/audit/cleaning_log.csv         table, issue, action, rows affected, note
    data/audit/value_changes.csv        table, key column, key, column, old value, new value
    data/audit/quarantine_*.csv         one file per quarantined set

Run (venv active):   python scripts/02_clean.py        [--data-dir "path/to/raw"]

Order of steps (see decision_log.md section 3):
    D01 quarantine orphan transactions -> D02 security_id -> D05 Buy share sign ->
    D03 return_ytd percent text -> D04 state codes -> D06/D07/D08 flag columns
Then: proof that raw = clean + quarantined, that every changed cell is logged,
that no foreign key is broken, write files, read them back, check raw unchanged.
"""
import argparse
import hashlib
import sys
from decimal import Decimal
from pathlib import Path

import pandas as pd

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
TABLES = ["dim_advisor", "dim_client", "dim_date", "dim_security", "dim_benchmark",
          "fact_fees", "fact_portfolio_snapshot", "fact_transactions"]
PK = {"dim_advisor": "advisor_id", "dim_client": "client_id", "dim_date": "date_id",
      "dim_security": "security_id", "dim_benchmark": "benchmark_id", "fact_fees": "fee_id",
      "fact_portfolio_snapshot": "snapshot_id", "fact_transactions": "txn_id"}
FOREIGN_KEYS = [  # (child, child col, parent, parent col): 10 ID-based + 3 date
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
NULLABLE_FK = {("fact_transactions", "security_id")}
STATE_MAP = {"Pennsylvania": "PA", "Florida": "FL", "New York": "NY", "New Jersey": "NJ",
             "California": "CA", "Illinois": "IL", "Texas": "TX"}
US_STATES = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split())
# Numbers the decision log promises (from the audit). The script stops if the data disagrees.
EXPECTED = {"orphan_tx": 200, "security_id_float": 197_044, "pct_returns": 300, "state_names": 78,
            "return_outliers": 312, "snapshot_floor": 420, "fee_floor": 386, "risk_blank": 76}
RETURN_OUTLIER_THRESHOLD = 5.0   # decision D06: return_ytd above +500%
AUM_FLOOR = 1000.0               # decision D07
PCT_RECON_TOL = 0.000051         # 2-dp percent rounding (5e-5) + 6-dp rounding of the two reference columns
MONEY_TOL = 1.00                 # amount = shares x price tolerance (same as audit)
BI_TYPE = {"int": "Whole number", "float": "Decimal number", "date": "Date", "bool": "True/False (text 'True'/'False')",
           "text": "Text", "zip": "Text (keep leading zeros)", "flag": "Whole number (0/1)"}
COLUMN_TYPES = {
    "dim_advisor": "advisor_id:int first_name:text last_name:text region:text years_experience:int aum_target_mm:int certifications:text",
    "dim_benchmark": "benchmark_id:int name:text asset_class:text ticker_proxy:text",
    "dim_client": "client_id:int first_name:text last_name:text age:int city:text state:text zip_code:zip risk_profile:text client_tier:text primary_account_type:text initial_aum:float client_since:date advisor_id:int is_active:bool flag_risk_profile_missing:flag",
    "dim_date": "date_id:int date:date year:int quarter:int month:int month_name:text week_of_year:int day_of_week:text is_month_end:flag is_quarter_end:flag is_year_end:flag is_trading_day:flag",
    "dim_security": "security_id:int ticker:text name:text asset_class:text sector:text benchmark_id:int is_etf:bool expense_ratio_bps:float",
    "fact_fees": "fee_id:int client_id:int advisor_id:int fee_date:date fee_type:text aum_basis:float bps_charged:float amount:float flag_aum_basis_at_floor:flag",
    "fact_portfolio_snapshot": "snapshot_id:int client_id:int advisor_id:int benchmark_id:int snapshot_date:date year:int month:int aum:float return_ytd:float benchmark_return_ytd:float active_alpha_ytd:float cash_pct:float account_type:text flag_return_ytd_outlier:flag flag_aum_at_floor:flag",
    "fact_transactions": "txn_id:int client_id:int advisor_id:int security_id:int txn_date:date txn_type:text shares:float price:float amount:float",
}

LOG = []       # cleaning_log rows
CHANGES = []   # value_changes frames
QUARANTINE = {}  # file stem -> (table, DataFrame)
RAW = {}
CLEAN = {}
STATS = {}     # numbers reused in README


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------
def num(s):
    return pd.to_numeric(s, errors="coerce")


def blank(s):
    return s.str.strip() == ""


def banner(step, title):
    print(f"\n{'=' * 78}\n{step}  {title}\n{'=' * 78}")


def log_action(table, issue, action, rows, note=""):
    LOG.append({"table": table, "issue": issue, "action": action, "rows_affected": int(rows), "note": note})


def expect(name, got, expected):
    assert got == expected, f"{name}: found {got:,} but the decision log / audit expects {expected:,} - stop and re-audit"


def record_and_apply(table, mask, col, new_values):
    """Apply new_values to CLEAN[table].loc[mask, col] and log every changed cell."""
    df = CLEAN[table]
    old = df.loc[mask, col].astype(str)
    new = pd.Series(new_values, index=df.index[mask]).astype(str)
    assert (old.values != new.values).all(), f"{table}.{col}: a 'changed' value is identical to the original"
    CHANGES.append(pd.DataFrame({"table": table, "key_column": PK[table], "key": df.loc[mask, PK[table]].values,
                                 "column": col, "old_value": old.values, "new_value": new.values}))
    df.loc[mask, col] = new.values


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def find_file(data_dir, stem):
    exact = data_dir / f"{stem}.csv"
    if exact.exists():
        return exact
    hits = sorted(data_dir.glob(f"{stem}*.csv"), key=lambda p: (len(p.name), p.name))
    return hits[0] if hits else None


def locate_data_dir(project_root, cli_dir):
    if cli_dir:
        return Path(cli_dir).resolve()
    for cand in [project_root / "Wildcat Capital", project_root / "data" / "raw", project_root]:
        if cand.is_dir() and find_file(cand, "dim_advisor"):
            return cand
    sys.exit("ERROR: raw CSVs not found. Pass --data-dir.")


def ri_orphans(fact, fk, dim, pk):
    """Orphan count among non-blank keys (exact text match, as a join would see it)."""
    k = fact[fk]
    k = k[~blank(k)]
    return int((~k.isin(set(dim[pk]))).sum())


# ----------------------------------------------------------------------------
# cleaning steps - one per decision
# ----------------------------------------------------------------------------
def d01_quarantine_orphan_transactions():
    banner("D01", "Quarantine transactions whose client_id is not in dim_client")
    tx, cl = CLEAN["fact_transactions"], CLEAN["dim_client"]
    orphan = ~tx["client_id"].isin(set(cl["client_id"]))
    n = int(orphan.sum())
    print(f"  before: {len(tx):,} rows, {n:,} orphan client_ids ({orphan.mean():.3%})")
    expect("orphan transactions", n, EXPECTED["orphan_tx"])
    q = tx[orphan].copy()
    q.insert(0, "raw_row_number", q.index + 1)  # 1-based data row in the raw file (header excluded)
    q["quarantine_reason"] = "client_id not found in dim_client (orphan foreign key)"
    QUARANTINE["quarantine_fact_transactions_orphan_client"] = ("fact_transactions", q)
    CLEAN["fact_transactions"] = tx[~orphan]
    tx2 = CLEAN["fact_transactions"]
    after_orphans = ri_orphans(tx2, "client_id", cl, "client_id")
    print(f"  after : {len(tx2):,} rows kept, {len(q):,} quarantined, orphan client_ids = {after_orphans}")
    assert after_orphans == 0
    assert len(tx2) + len(q) == len(RAW["fact_transactions"]), "rows lost or duplicated"
    assert set(q["txn_id"]).isdisjoint(set(tx2["txn_id"]))
    STATS["orphan_amount"] = float(num(q["amount"]).sum())
    STATS["orphan_trade_rows"] = int(q["txn_type"].isin(["Buy", "Sell", "Dividend"]).sum())
    log_action("fact_transactions", "D01 orphan client_id (200 clients not in dim_client)", "quarantine", n,
               f"moved to quarantine_fact_transactions_orphan_client.csv; amount ${STATS['orphan_amount']:,.0f}; clean={len(tx2):,}")


def d02_security_id_float_format():
    banner("D02", "fact_transactions.security_id: '45.0' -> '45'")
    tx, sec = CLEAN["fact_transactions"], CLEAN["dim_security"]
    sid = tx["security_id"]
    nonblank = ~blank(sid)
    floatfmt = sid.str.fullmatch(r"\d+\.0+")
    sec_ids = set(sec["security_id"])
    match_before = sid[nonblank].isin(sec_ids).mean()
    n = int(floatfmt.sum())
    print(f"  before: {n:,} float-format ids; text match rate against dim_security = {match_before:.1%}")
    assert floatfmt[nonblank].all(), "a non-blank security_id is not of the form 'N.0' - the fix would not be complete"
    assert match_before == 0.0, "expected 0% text match before the fix (audit F008)"
    expect("float-format security_id (after D01)", n, EXPECTED["security_id_float"])
    n_blank = int((~nonblank).sum())
    new = sid.str.replace(r"\.0+$", "", regex=True)
    record_and_apply("fact_transactions", floatfmt, "security_id", new[floatfmt])
    sid2 = CLEAN["fact_transactions"]["security_id"]
    nb2 = ~blank(sid2)
    match_after = sid2[nb2].isin(sec_ids).mean()
    print(f"  after : text match rate = {match_after:.1%}; blanks unchanged = {int((~nb2).sum()):,}")
    assert match_after == 1.0
    assert not sid2.str.contains(".", regex=False).any()
    assert int((~nb2).sum()) == n_blank
    log_action("fact_transactions", "D02 security_id stored as float text ('45.0')", "convert", n,
               "trailing .0 removed; 0% -> 100% text match with dim_security; blanks (cash flows) untouched")


def d05_negative_buy_shares():
    banner("D05", "fact_transactions.shares: negative shares on Buy -> absolute value")
    tx = CLEAN["fact_transactions"]
    sh, pr, am = num(tx["shares"]), num(tx["price"]), num(tx["amount"])
    neg = sh < 0
    assert (tx.loc[neg, "txn_type"] == "Buy").all(), "negative shares exist on a non-Buy row - decision D05 does not cover that"
    both = sh.notna() & pr.notna()
    mismatch_signed = both & ((sh * pr - am).abs() > MONEY_TOL)
    mismatch_abs = both & ((sh.abs() * pr - am).abs() > MONEY_TOL)
    n = int(neg.sum())
    print(f"  before: {n:,} negative-share Buy rows; amount != shares x price on {int(mismatch_signed.sum()):,} rows "
          f"(only {int(mismatch_abs.sum())} rows fail if |shares| is used)")
    assert n <= 836 and n > 0
    assert int(mismatch_abs.sum()) == 0, "amount does not reconcile to |shares| x price, so the sign is not the only problem"
    assert int(mismatch_signed.sum()) == n, "the amount mismatches are not exactly the negative rows"
    record_and_apply("fact_transactions", neg, "shares", tx.loc[neg, "shares"].str.lstrip("-"))
    tx2 = CLEAN["fact_transactions"]
    sh2, pr2, am2 = num(tx2["shares"]), num(tx2["price"]), num(tx2["amount"])
    both2 = sh2.notna() & pr2.notna()
    bad_after = int((both2 & ((sh2 * pr2 - am2).abs() > MONEY_TOL)).sum())
    print(f"  after : negative shares = {int((sh2 < 0).sum())}; rows where amount != shares x price = {bad_after}")
    assert int((sh2 < 0).sum()) == 0
    assert bad_after == 0
    log_action("fact_transactions", "D05 negative shares on Buy rows", "convert", n,
               "shares = abs(shares); amount = shares x price now holds on every row (tolerance $1.00)")


def d03_percent_text_returns():
    banner("D03", "fact_portfolio_snapshot.return_ytd: '9.28%' -> 0.0928")
    sn = CLEAN["fact_portfolio_snapshot"]
    ret = sn["return_ytd"]
    pct = ret.str.strip().str.fullmatch(r"[+-]?\d+(\.\d+)?\s*%")
    n = int(pct.sum())
    print(f"  before: {n:,} percent-text values; non-% values parse as float: {num(ret[~pct]).notna().all()}")
    expect("percent-text returns", n, EXPECTED["pct_returns"])
    assert num(ret[~pct]).notna().all(), "a non-% value in return_ytd does not parse as a number"
    new = ret[pct].map(lambda v: format(Decimal(v.strip().rstrip("%").strip()).scaleb(-2), "f"))
    expected_fraction = num(sn.loc[pct, "benchmark_return_ytd"]) + num(sn.loc[pct, "active_alpha_ytd"])
    diff_as_fraction = (num(new) - expected_fraction).abs()
    diff_as_points = (num(ret[pct].str.rstrip("%")) - expected_fraction).abs()
    print(f"  reconcile vs benchmark_return_ytd + active_alpha_ytd: max diff if /100 = {diff_as_fraction.max():.6f}; "
          f"if left as percent points = {diff_as_points.max():,.3f}")
    assert diff_as_fraction.max() <= PCT_RECON_TOL, "converted values do not reconcile with benchmark + alpha"
    assert diff_as_points.min() > 0.01, "left as percent points the values would also reconcile - scale not proven"
    record_and_apply("fact_portfolio_snapshot", pct, "return_ytd", new)
    ret2 = CLEAN["fact_portfolio_snapshot"]["return_ytd"]
    print(f"  after : '%' remaining = {int(ret2.str.contains('%', regex=False).sum())}; "
          f"column parses as float = {num(ret2).notna().all()}")
    assert not ret2.str.contains("%", regex=False).any()
    assert num(ret2).notna().all()
    log_action("fact_portfolio_snapshot", "D03 return_ytd stored as percent text", "convert", n,
               f"stripped %, divided by 100 (exact Decimal shift); reconciled to benchmark_return_ytd + active_alpha_ytd, max diff {diff_as_fraction.max():.6f}")


def d04_state_codes():
    banner("D04", "dim_client.state: full names -> USPS codes")
    cl = CLEAN["dim_client"]
    st = cl["state"]
    full = st.isin(STATE_MAP.keys())
    n = int(full.sum())
    print(f"  before: {n:,} full-name states; values outside (USPS codes + the 7 mapped names): "
          f"{int((~(full | st.isin(US_STATES))).sum())}")
    expect("full-name states", n, EXPECTED["state_names"])
    assert (full | st.isin(US_STATES)).all(), "an unexpected state value exists that the mapping does not cover"
    expected_counts = st.map(lambda v: STATE_MAP.get(v, v)).value_counts().to_dict()
    record_and_apply("dim_client", full, "state", st[full].map(STATE_MAP))
    st2 = CLEAN["dim_client"]["state"]
    print(f"  after : values not in USPS list = {int((~st2.isin(US_STATES)).sum())}; "
          f"distinct states = {st2.nunique()}")
    assert st2.isin(US_STATES).all()
    assert st2.value_counts().to_dict() == expected_counts, "state totals changed beyond the 7 mapped names"
    log_action("dim_client", "D04 state: full names mixed with USPS codes", "standardize", n,
               "7-name mapping (PA, FL, NY, NJ, CA, IL, TX); per-state totals = raw codes + raw names")


def flags_d06_d07_d08():
    banner("D06/D07/D08", "Flag columns (values are never changed)")
    sn, fe, cl = CLEAN["fact_portfolio_snapshot"], CLEAN["fact_fees"], CLEAN["dim_client"]
    raw_sn, raw_fe, raw_cl = RAW["fact_portfolio_snapshot"], RAW["fact_fees"], RAW["dim_client"]

    # D06 - implausible return
    r = num(sn["return_ytd"])
    f6 = (r > RETURN_OUTLIER_THRESHOLD)
    sn["flag_return_ytd_outlier"] = f6.astype(int).astype(str)
    n6 = int(f6.sum())
    expect("return_ytd outliers (> +500%)", n6, EXPECTED["return_outliers"])
    # alpha = return - benchmark: exact (1e-5) on rows that were numeric in the raw file;
    # the 300 converted percent rows can only match to the 2-dp percent rounding (D03 already proved that)
    was_numeric = num(raw_sn["return_ytd"]).notna().reindex(sn.index)
    alpha_diff = (num(sn["active_alpha_ytd"]) - (r - num(sn["benchmark_return_ytd"]))).abs()
    alpha_check = alpha_diff[was_numeric].max()
    assert alpha_check < 1e-5, "active_alpha_ytd != return_ytd - benchmark_return_ytd on originally numeric rows"
    assert alpha_diff[~was_numeric].max() <= PCT_RECON_TOL
    print(f"  D06 flag_return_ytd_outlier: {n6:,} rows ({sn.loc[f6, 'client_id'].nunique()} clients); "
          f"alpha = return - benchmark holds (max diff {alpha_check:.6f} on {int(was_numeric.sum()):,} numeric rows; "
          f"<= {PCT_RECON_TOL} on the 300 converted rows), so one flag covers both columns")
    log_action("fact_portfolio_snapshot", "D06 return_ytd above +500% (implausible)", "flag", n6,
               "flag_return_ytd_outlier=1; value NOT changed (return and AUM history disagree, no source to correct from)")

    # D07 - AUM floor (snapshot + fees)
    a = num(sn["aum"])
    assert a.min() >= AUM_FLOOR, "AUM below the floor exists - the 'floor' explanation does not hold"
    f7 = (a == AUM_FLOOR)
    sn["flag_aum_at_floor"] = f7.astype(int).astype(str)
    n7 = int(f7.sum())
    expect("snapshot rows at AUM floor", n7, EXPECTED["snapshot_floor"])
    b = num(fe["aum_basis"])
    assert b.min() >= AUM_FLOOR
    f7b = (b == AUM_FLOOR)
    fe["flag_aum_basis_at_floor"] = f7b.astype(int).astype(str)
    n7b = int(f7b.sum())
    expect("fee rows at AUM floor", n7b, EXPECTED["fee_floor"])
    # reconcile: every floor fee row must sit on a floor snapshot row of the same client-month
    m = fe.loc[f7b, ["client_id", "fee_date"]].merge(
        sn[["client_id", "snapshot_date", "flag_aum_at_floor"]],
        left_on=["client_id", "fee_date"], right_on=["client_id", "snapshot_date"], how="left")
    assert (m["flag_aum_at_floor"] == "1").all(), "a floor fee row does not match a floor snapshot row"
    print(f"  D07 flag_aum_at_floor: {n7:,} snapshot rows; flag_aum_basis_at_floor: {n7b:,} fee rows "
          f"(all {n7b:,} sit on a flagged snapshot of the same client-month)")
    log_action("fact_portfolio_snapshot", "D07 aum at exactly 1,000 (upstream floor)", "flag", n7,
               "flag_aum_at_floor=1; value NOT changed (true AUM unknown)")
    log_action("fact_fees", "D07 aum_basis at exactly 1,000 (upstream floor)", "flag", n7b,
               "flag_aum_basis_at_floor=1; value NOT changed; all rows reconcile to flagged snapshot months")

    # D08 - blank risk profile
    f8 = blank(cl["risk_profile"])
    cl["flag_risk_profile_missing"] = f8.astype(int).astype(str)
    n8 = int(f8.sum())
    expect("blank risk_profile", n8, EXPECTED["risk_blank"])
    print(f"  D08 flag_risk_profile_missing: {n8:,} clients (risk_profile left blank, not filled)")
    log_action("dim_client", "D08 risk_profile blank", "flag", n8,
               "flag_risk_profile_missing=1; NOT filled (benchmark pattern may be a default, not evidence)")

    # after-state: flagged columns hold exactly the raw/converted values; flags are 0/1 text
    assert sn["aum"].equals(raw_sn["aum"]) and fe["aum_basis"].equals(raw_fe["aum_basis"])
    assert cl["risk_profile"].equals(raw_cl["risk_profile"])
    for df, c in [(sn, "flag_return_ytd_outlier"), (sn, "flag_aum_at_floor"),
                  (fe, "flag_aum_basis_at_floor"), (cl, "flag_risk_profile_missing")]:
        assert df[c].isin(["0", "1"]).all()
    STATS.update(flag_return=n6, flag_return_clients=int(sn.loc[f6, "client_id"].nunique()),
                 flag_snap_floor=n7, flag_fee_floor=n7b, flag_risk=n8)


def note_untouched_tables_and_leave_as_is():
    """Log the 'leave as is' decisions with counts computed from the clean data (rows_affected = 0)."""
    banner("D09-D19", "Leave-as-is decisions: confirm and count (no data changed)")
    sec, adv, cl = CLEAN["dim_security"], CLEAN["dim_advisor"], CLEAN["dim_client"]
    fe, sn, tx, dd = CLEAN["fact_fees"], CLEAN["fact_portfolio_snapshot"], CLEAN["fact_transactions"], CLEAN["dim_date"]

    etf = sec["is_etf"] == "True"
    assert (blank(sec["sector"]) == etf).all() and (blank(sec["expense_ratio_bps"]) == ~etf).all()
    log_action("dim_security", "D09 sector / expense_ratio_bps blank", "leave as is", 0,
               f"{int(blank(sec['sector']).sum())} blank sectors = ETFs; {int(blank(sec['expense_ratio_bps']).sum())} blank expense ratios = non-ETFs; 0 exceptions")

    cash = tx["txn_type"].isin(["Deposit", "Withdrawal", "Advisory Fee"])
    trade = tx["txn_type"].isin(["Buy", "Sell", "Dividend"])
    three_blank = blank(tx["security_id"]) & blank(tx["shares"]) & blank(tx["price"])
    assert (three_blank == cash).all() and not (three_blank & trade).any()
    log_action("fact_transactions", "D10 security_id / shares / price blank", "leave as is", 0,
               f"{int(three_blank.sum()):,} blanks = exactly the Deposit/Withdrawal/Advisory Fee rows; every trade row complete")

    log_action("dim_advisor", "D11 certifications = literal text 'None'", "leave as is", 0,
               f"{int((adv['certifications'] == 'None').sum())} advisors; legitimate category (no certification), not a null")

    dup_names = sec[sec.duplicated("name", keep=False)]
    log_action("dim_security", "D12 duplicated security names", "leave as is", 0,
               f"{len(dup_names)} securities / {dup_names['name'].nunique()} names; ids, tickers and attributes differ")

    log_action("fact_fees", "D13 bps_charged above 100 (one row)", "leave as is", 0,
               f"{int((num(fe['bps_charged']) > 100).sum())} row(s); amount reconciles to aum_basis x bps / 120000")

    no_activity = ~cl["client_id"].isin(set(sn["client_id"]) | set(fe["client_id"]) | set(tx["client_id"]))
    STATS["clients_no_facts"] = int(no_activity.sum())
    log_action("dim_client", "D14 clients with no facts", "leave as is", 0,
               f"{STATS['clients_no_facts']} clients (valid reference data)")

    tdays = dd.set_index("date")["is_trading_day"]
    bs = tx["txn_type"].isin(["Buy", "Sell"])
    weekend_trades = int((bs & (tx["txn_date"].map(tdays) == "0")).sum())
    STATS.update(weekend_trades=weekend_trades, buy_sell=int(bs.sum()))
    log_action("fact_transactions", "D15 Buy/Sell on non-trading days", "leave as is", 0,
               f"{weekend_trades:,} of {int(bs.sum()):,} Buy/Sell rows; same ~28% share for every transaction type")

    adv_tx = num(tx.loc[tx["txn_type"] == "Advisory Fee", "amount"]).sum()
    adv_fee = num(fe["amount"]).sum()
    STATS.update(tx_fee_total=float(adv_tx), fee_table_total=float(adv_fee))
    log_action("fact_transactions / fact_fees", "D16 advisory fee debits vs fee table", "leave as is", 0,
               f"transaction debits ${adv_tx:,.0f} vs fee table ${adv_fee:,.0f}; no source of truth")

    keys = set(zip(fe["client_id"], fe["fee_date"]))
    nofee = int((~pd.Series(list(zip(sn["client_id"], sn["snapshot_date"]))).isin(keys)).sum())
    STATS["months_no_fee"] = nofee
    log_action("fact_portfolio_snapshot", "D17 snapshot months with no fee row", "leave as is", 0, f"{nofee:,} snapshot rows")

    ft = fe.sort_values(["client_id", "fee_date"]).groupby("client_id")["fee_type"].apply(lambda s: (s != s.shift()).iloc[1:].mean()).mean()
    STATS["fee_type_change"] = float(ft)
    log_action("fact_fees", "D18 fee_type changes month to month", "leave as is", 0, f"type changes in {ft:.1%} of month-to-month steps")

    for t in ["dim_advisor", "dim_benchmark", "dim_date", "dim_security"]:
        assert CLEAN[t].equals(RAW[t]), f"{t} should be unchanged"
        log_action(t, "No defects requiring a fix", "none (identical to raw)", 0, "clean file equals raw file")
    print("  all leave-as-is conditions confirmed; four tables are byte-for-byte equal in content to raw")


# ----------------------------------------------------------------------------
# proofs
# ----------------------------------------------------------------------------
def prove_reconciliation():
    banner("PROOF 1", "raw rows = clean rows + quarantined rows (every table)")
    rows = []
    for t in TABLES:
        qn = sum(len(q) for (qt, q) in QUARANTINE.values() if qt == t)
        raw_n, clean_n = len(RAW[t]), len(CLEAN[t])
        pk = PK[t]
        assert RAW[t][pk].is_unique, f"{t}.{pk} not unique in raw"
        q_keys = set().union(*[set(q[pk]) for (qt, q) in QUARANTINE.values() if qt == t]) if qn else set()
        assert set(CLEAN[t][pk]) | q_keys == set(RAW[t][pk]) and set(CLEAN[t][pk]).isdisjoint(q_keys)
        assert raw_n == clean_n + qn, f"{t}: {raw_n} != {clean_n} + {qn}"
        rows.append((t, raw_n, clean_n, qn))
        print(f"  {t:<26} raw {raw_n:>8,} = clean {clean_n:>8,} + quarantined {qn:>4,}   OK")
    STATS["row_table"] = rows


def prove_every_change_is_logged():
    banner("PROOF 2", "every changed cell is in value_changes.csv, and nothing else changed")
    changes = pd.concat(CHANGES, ignore_index=True)
    logged = changes.groupby(["table", "column"]).size().to_dict()
    for t in TABLES:
        raw, cl, pk = RAW[t], CLEAN[t], PK[t]
        cols = list(raw.columns)
        assert list(cl.columns[:len(cols)]) == cols, f"{t}: original columns changed"
        kept = raw.set_index(pk, drop=False).loc[cl[pk].values]
        diff = (kept[cols].to_numpy() != cl[cols].to_numpy()).sum(axis=0)
        for c, d in zip(cols, diff):
            assert int(d) == logged.get((t, c), 0), f"{t}.{c}: {int(d)} cells differ from raw but {logged.get((t, c), 0)} are logged"
        extra = list(cl.columns[len(cols):])
        n_cells = int(diff.sum())
        print(f"  {t:<26} changed cells {n_cells:>8,} (all logged); added columns: {extra if extra else '-'}")
    return changes


def prove_referential_integrity():
    banner("PROOF 3", "all 13 relationships on the clean tables")
    for child, ccol, parent, pcol in FOREIGN_KEYS:
        o = ri_orphans(CLEAN[child], ccol, CLEAN[parent], pcol)
        nb = int((~blank(CLEAN[child][ccol])).sum())
        print(f"  {child}.{ccol:<14} -> {parent}.{pcol:<12} orphans {o}  (match {100 * (nb - o) / nb:.3f}% of {nb:,} non-blank keys)")
        assert o == 0, f"{child}.{ccol} still has orphans"
        if (child, ccol) not in NULLABLE_FK:
            assert nb == len(CLEAN[child]), f"{child}.{ccol} has blank keys"


# ----------------------------------------------------------------------------
# README_clean.md
# ----------------------------------------------------------------------------
def build_readme():
    S = STATS
    rt = "\n".join(f"| `{t}` | {r:,} | {c:,} | {q:,} |" for t, r, c, q in S["row_table"])
    rel = "\n".join(f"| `{c}.{cc}` | `{p}.{pc}` | many-to-one | {'nullable (blank for cash-flow rows)' if (c, cc) in NULLABLE_FK else 'required'} |"
                    for c, cc, p, pc in FOREIGN_KEYS)
    types = []
    for t in TABLES:
        types.append(f"\n**`{t}`** (key: `{PK[t]}`)\n\n| Column | BI type |\n|---|---|")
        for item in COLUMN_TYPES[t].split():
            c, ty = item.split(":")
            types.append(f"| `{c}` | {BI_TYPE[ty]} |")
    return f"""# Clean data - README
HW4 for MIS3060. Produced by `scripts/02_clean.py` from the raw Wildcat Capital extract. The raw files were not modified (SHA-256 checked before and after). Every change is traceable in `data/audit/`.

## 1. What is in this folder
Eight CSV files with the **same names and same columns** as the raw tables. Four 0/1 flag columns were added at the end of three tables (section 4).

| Table | Raw rows | Clean rows | Quarantined |
|---|---:|---:|---:|
{rt}

Raw rows = clean rows + quarantined rows holds for every table. Audit files: `data/audit/cleaning_log.csv` (what was done and why), `data/audit/value_changes.csv` (every changed cell, old vs new), `data/audit/quarantine_fact_transactions_orphan_client.csv` (removed rows, all original columns + raw row number + reason).

## 2. Relationships between tables
Star-schema layout: dimensions `dim_advisor`, `dim_client`, `dim_security`, `dim_benchmark`, `dim_date`; facts `fact_fees` (client x month), `fact_portfolio_snapshot` (client x month), `fact_transactions` (one row per transaction). Ten ID-based and three date relationships; all resolve with **0 orphans** on the clean tables.

| Child column | Parent column | Cardinality | Key presence |
|---|---|---|---|
{rel}

The three date relationships join to `dim_date.date` (text `YYYY-MM-DD`; `date_id` is the surrogate key). `fact_transactions.security_id` is blank by design for Deposit, Withdrawal and Advisory Fee rows, so the relationship must allow blank keys.

## 3. Column-type settings for a BI tool
Import every column as **text first**, then set these types explicitly (do not trust auto-detect): IDs as whole numbers, money and rates as decimals, dates as Date. Keep `zip_code` as **Text** (232 ZIP codes start with 0). `is_active` and `is_etf` hold the text `True`/`False`. The text `None` in `dim_advisor.certifications` is a real value ("no certification"), not a missing value - do not let the tool convert it to null. Empty cells (e.g. `sector` for ETFs, `risk_profile` when flagged) are genuine blanks.
{chr(10).join(types)}

## 4. Flag columns added (0/1; the original value is never changed)
| Column | Table | Rows flagged | Meaning |
|---|---|---:|---|
| `flag_return_ytd_outlier` | `fact_portfolio_snapshot` | {S['flag_return']:,} | `return_ytd` above +500% ({S['flag_return_clients']} clients). Return and AUM history disagree; exclude from averages |
| `flag_aum_at_floor` | `fact_portfolio_snapshot` | {S['flag_snap_floor']:,} | `aum` is exactly 1,000.00 - an upstream minimum; true AUM unknown |
| `flag_aum_basis_at_floor` | `fact_fees` | {S['flag_fee_floor']:,} | `aum_basis` is exactly 1,000.00 (same client-months as the flagged snapshots) |
| `flag_risk_profile_missing` | `dim_client` | {S['flag_risk']:,} | `risk_profile` is blank; not filled because the evidence for "Balanced" may be circular |

## 5. Fixes applied (see `cleaning_log.csv` and `value_changes.csv`)
- **D01** {len(QUARANTINE['quarantine_fact_transactions_orphan_client'][1]):,} transactions quarantined: `client_id` not in `dim_client` (total ${S['orphan_amount']:,.0f}).
- **D02** `fact_transactions.security_id` converted from `45.0` to `45` (text match with `dim_security` 0% -> 100%).
- **D05** negative `shares` on Buy rows converted to absolute value; `amount = shares x price` now holds on every row.
- **D03** `return_ytd` percent text (`9.28%`) converted to a decimal fraction (`0.0928`), reconciled to `benchmark_return_ytd + active_alpha_ytd`.
- **D04** `dim_client.state` full names standardized to USPS codes.

## 6. Known limitations (chosen not to fix, with reasons)
| Limitation | Size | Why it was left |
|---|---|---|
| Flagged but uncorrected returns above +500% | {S['flag_return']:,} rows | No other column gives the correct return; correcting would invent data |
| AUM floor at 1,000 | {S['flag_snap_floor']:,} snapshot / {S['flag_fee_floor']:,} fee rows | True AUM is unknown; value kept so snapshot and fee tables agree |
| Blank `risk_profile` | {S['flag_risk']:,} clients | A wrong fill is worse than a visible blank; confirm with the advisor |
| Buy/Sell dated on weekends | {S['weekend_trades']:,} of {S['buy_sell']:,} rows | Same share (~28%) for every transaction type, so it is a property of the whole extract; no source for the right date |
| Advisory fee debits (transactions) do not match `fact_fees` | ${S['tx_fee_total']:,.0f} vs ${S['fee_table_total']:,.0f} | The tables disagree broadly and neither is known to be the source of truth |
| Snapshot months with no fee row | {S['months_no_fee']:,} | No evidence of what the fee should be; billing gaps can be real |
| `fee_type` changes month to month | {S['fee_type_change']:.1%} of steps | `amount` reconciles, but the label cannot be corrected; do not split revenue by fee type |
| Duplicated security names | 3 pairs | Different ids, tickers and attributes: distinct securities, not duplicates |
| One fee rate above 100 bps (100.38) | 1 row | The 100 bps ceiling was an assumption; the amount reconciles |
| Clients, benchmarks with no facts | {S['clients_no_facts']} clients | Valid reference data; client counts differ between the dimension and the facts |
| Blank `sector`/`expense_ratio_bps`; blank `security_id`/`shares`/`price` on cash flows | structural | Blanks follow `is_etf` and the transaction type exactly; filling would invent data |
"""


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="HW4 Part C - clean the Wildcat Capital tables")
    ap.add_argument("--data-dir", help="folder with the 8 raw CSVs (default: auto-detect)")
    args = ap.parse_args()
    project_root = Path(__file__).resolve().parent.parent
    data_dir = locate_data_dir(project_root, args.data_dir)
    clean_dir, audit_dir = project_root / "data" / "clean", project_root / "data" / "audit"
    clean_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)
    print(f"Project root : {project_root}\nRaw data dir : {data_dir}\nClean output : {clean_dir}\nAudit output : {audit_dir}")

    banner("LOAD", "Read raw files as text (dtype=str, keep_default_na=False)")
    paths = {}
    for t in TABLES:
        f = find_file(data_dir, t)
        if f is None:
            sys.exit(f"ERROR: cannot find {t}.csv in {data_dir}")
        paths[t] = f
        RAW[t] = pd.read_csv(f, dtype=str, keep_default_na=False)
        print(f"  {t:<26} <- {f.name:<34} {len(RAW[t]):>8,} rows x {RAW[t].shape[1]} cols")
    hashes_before = {t: sha256(p) for t, p in paths.items()}
    for t in TABLES:
        CLEAN[t] = RAW[t].copy()

    # cleaning steps, in the order from the decision log
    d01_quarantine_orphan_transactions()
    d02_security_id_float_format()
    d05_negative_buy_shares()
    d03_percent_text_returns()
    d04_state_codes()
    flags_d06_d07_d08()
    note_untouched_tables_and_leave_as_is()

    # proofs
    prove_reconciliation()
    changes = prove_every_change_is_logged()
    prove_referential_integrity()

    # write outputs
    banner("WRITE", "Clean tables, audit trail, README")
    for t in TABLES:
        CLEAN[t].to_csv(clean_dir / f"{t}.csv", index=False, encoding="utf-8", lineterminator="\n")
    for stem, (t, q) in QUARANTINE.items():
        q.to_csv(audit_dir / f"{stem}.csv", index=False, encoding="utf-8", lineterminator="\n")
    pd.DataFrame(LOG).rename(columns={"rows_affected": "rows_affected"}).to_csv(
        audit_dir / "cleaning_log.csv", index=False, encoding="utf-8", lineterminator="\n")
    changes.to_csv(audit_dir / "value_changes.csv", index=False, encoding="utf-8", lineterminator="\n")
    (clean_dir / "README_clean.md").write_text(build_readme(), encoding="utf-8", newline="\n")

    # read back what was written: exactly what we hold in memory
    for t in TABLES:
        back = pd.read_csv(clean_dir / f"{t}.csv", dtype=str, keep_default_na=False)
        assert back.equals(CLEAN[t].reset_index(drop=True)), f"{t}: file on disk differs from the clean data in memory"
        assert len(back) == len(CLEAN[t])
    print(f"  wrote and re-read {len(TABLES)} clean tables: identical to memory")
    print(f"  wrote {len(QUARANTINE)} quarantine file(s), cleaning_log.csv ({len(LOG)} rows), "
          f"value_changes.csv ({len(changes):,} rows), README_clean.md")

    # raw files untouched
    hashes_after = {t: sha256(p) for t, p in paths.items()}
    assert hashes_before == hashes_after, "a raw file changed during the run"
    print("  raw files unchanged (SHA-256 identical before and after)")

    print("\nSUMMARY OF CHANGES BY STEP")
    summ = pd.DataFrame(LOG)
    print(summ[summ["action"].isin(["quarantine", "convert", "standardize", "flag"])]
          [["table", "issue", "action", "rows_affected"]].to_string(index=False))
    print("\nAll assertions passed. Done.")


if __name__ == "__main__":
    main()
