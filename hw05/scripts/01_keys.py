#!/usr/bin/env python3
"""
01_keys.py - HW5 Part A evidence: primary keys and foreign keys of the 8 Wildcat tables.

Proves, in code, the key table written in star_design.md:
  1. each table has the row count in the handout
  2. each primary key is never blank, unique, and a whole number
  3. each foreign key points at an existing parent key (orphans counted)
  4. blank foreign keys are counted and explained (only fact_transactions.security_id may be blank)
  5. fact dates match dim_date[date] (a unique column), and the facts hold no date_id
  6. no undeclared column looks like a foreign key (the declared design is complete)

Read-only. Run from the hw05 folder:   python scripts/01_keys.py
Optional:  python scripts/01_keys.py --data-dir path/to/folder
Save the output for the README:        python scripts/01_keys.py > keys_output.txt
Exit code 0 = every check passed, 1 = something failed.
Requires: pandas
"""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd

# ---- The design under test (this is the Part A answer) -------------------------------
EXPECTED_ROWS = {
    "dim_advisor": 25, "dim_benchmark": 8, "dim_client": 2500, "dim_date": 1827,
    "dim_security": 500, "fact_fees": 122197, "fact_portfolio_snapshot": 129547,
    "fact_transactions": 298572,
}
PRIMARY_KEYS = {
    "dim_advisor": "advisor_id", "dim_benchmark": "benchmark_id", "dim_client": "client_id",
    "dim_date": "date_id", "dim_security": "security_id", "fact_fees": "fee_id",
    "fact_portfolio_snapshot": "snapshot_id", "fact_transactions": "txn_id",
}
# (child table, child column, parent table, parent column)
FOREIGN_KEYS = [
    ("dim_client", "advisor_id", "dim_advisor", "advisor_id"),
    ("dim_security", "benchmark_id", "dim_benchmark", "benchmark_id"),
    ("fact_fees", "client_id", "dim_client", "client_id"),
    ("fact_fees", "advisor_id", "dim_advisor", "advisor_id"),
    ("fact_fees", "fee_date", "dim_date", "date"),
    ("fact_portfolio_snapshot", "client_id", "dim_client", "client_id"),
    ("fact_portfolio_snapshot", "advisor_id", "dim_advisor", "advisor_id"),
    ("fact_portfolio_snapshot", "benchmark_id", "dim_benchmark", "benchmark_id"),
    ("fact_portfolio_snapshot", "snapshot_date", "dim_date", "date"),
    ("fact_transactions", "client_id", "dim_client", "client_id"),
    ("fact_transactions", "advisor_id", "dim_advisor", "advisor_id"),
    ("fact_transactions", "security_id", "dim_security", "security_id"),
    ("fact_transactions", "txn_date", "dim_date", "date"),
]
# Foreign keys allowed to be blank, with the reason
BLANK_ALLOWED = {
    ("fact_transactions", "security_id"):
        "cash rows (Deposit, Withdrawal, Advisory Fee) involve no security",
}
BLANK_ALLOWED_TXN_TYPES = {"Deposit", "Withdrawal", "Advisory Fee"}  # rows where blank is OK
DATE_RX = r"\d{4}-\d{2}-\d{2}"
INT_RX = r"\d+"

failures = []


def check(ok, label, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"  ({detail})" if detail else ""))
    if not ok:
        failures.append(label)


def load(data_dir):
    tables = {}
    for p in sorted(data_dir.glob("*.csv")):
        name = re.sub(r"\s*\(\d+\)$", "", p.stem).strip()   # 'dim_client (2)' -> 'dim_client'
        tables[name] = pd.read_csv(p, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    return tables


def blank(s):
    return s.str.strip() == ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parent.parent)
    data_dir = ap.parse_args().data_dir
    T = load(data_dir)
    print(f"HW5 Part A: keys  |  data folder: {data_dir}\n")

    missing = [t for t in EXPECTED_ROWS if t not in T]
    check(not missing, "all 8 tables found", ", ".join(missing))
    if missing:
        return 1

    print("\n1. Row counts match the handout")
    for t, n in EXPECTED_ROWS.items():
        check(len(T[t]) == n, f"{t}: {len(T[t]):,} rows", f"expected {n:,}")

    print("\n2. Primary keys: never blank, unique, whole number")
    for t, pk in PRIMARY_KEYS.items():
        s = T[t][pk]
        check(pk in T[t].columns, f"{t}.{pk} exists")
        check(not blank(s).any(), f"{t}.{pk} has no blanks", f"{int(blank(s).sum())} blank")
        check(s.is_unique, f"{t}.{pk} is unique", f"{s.nunique():,} distinct of {len(s):,}")
        check(s.str.fullmatch(INT_RX).all(), f"{t}.{pk} is a whole number")

    print("\n3. Dates join on dim_date[date], which must be a unique calendar date")
    d = T["dim_date"]["date"]
    check(d.is_unique and d.str.fullmatch(DATE_RX).all(), "dim_date[date] is unique and YYYY-MM-DD",
          f"{d.min()} to {d.max()}")
    for t in ("fact_fees", "fact_portfolio_snapshot", "fact_transactions"):
        check("date_id" not in T[t].columns, f"{t} has no date_id column (so it cannot join on date_id)")

    print("\n4. Foreign keys: every non-blank value exists in the parent key")
    for ct, cc, pt, pc in FOREIGN_KEYS:
        child, parent = T[ct][cc], T[pt][pc]
        nb = child[~blank(child)]
        orphans = ~nb.isin(set(parent))
        check(orphans.sum() == 0, f"{ct}[{cc}] -> {pt}[{pc}]",
              f"{len(nb):,} values checked, {int(orphans.sum())} orphans"
              + (f", e.g. {', '.join(nb[orphans].unique()[:3])}" if orphans.any() else ""))

    print("\n5. Blank foreign keys")
    for ct, cc, pt, pc in FOREIGN_KEYS:
        n_blank = int(blank(T[ct][cc]).sum())
        if (ct, cc) in BLANK_ALLOWED:
            tt = T[ct].txn_type.str.strip()
            only_cash = (blank(T[ct][cc]) == tt.isin(BLANK_ALLOWED_TXN_TYPES)).all()
            by_type = tt[blank(T[ct][cc])].value_counts().to_dict()
            check(only_cash, f"{ct}[{cc}] is blank exactly on cash rows ({BLANK_ALLOWED[(ct, cc)]})",
                  f"{n_blank:,} blank: {by_type}")
        else:
            check(n_blank == 0, f"{ct}[{cc}] is never blank", f"{n_blank} blank")

    print("\n6. Redundant copy: fact advisor_id equals the client's advisor_id")
    adv = T["dim_client"].set_index("client_id").advisor_id
    for t in ("fact_fees", "fact_portfolio_snapshot", "fact_transactions"):
        same = T[t].client_id.map(adv) == T[t].advisor_id
        check(same.all(), f"{t}.advisor_id = dim_client.advisor_id", f"{int(same.sum()):,} of {len(same):,} rows")

    print("\n7. Completeness of the design: no undeclared foreign key candidates")
    declared = {(ct, cc) for ct, cc, _, _ in FOREIGN_KEYS} | {(t, pk) for t, pk in PRIMARY_KEYS.items()}
    pk_cols = set(PRIMARY_KEYS.values())
    extra = [f"{t}.{c}" for t, df in T.items() for c in df.columns
             if c.endswith("_id") and c in pk_cols and (t, c) not in declared]
    check(not extra, "every *_id column that matches another table's key is declared", ", ".join(extra))

    print(f"\n{'ALL CHECKS PASSED' if not failures else str(len(failures)) + ' CHECK(S) FAILED'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
