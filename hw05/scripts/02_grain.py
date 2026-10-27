#!/usr/bin/env python3
"""
02_grain.py - HW5 Part B evidence: the grain ("one row represents ...") of each fact table.

For each fact table it proves, in code:
  * the declared grain key is UNIQUE (no row repeats at that grain)
  * the key is MINIMAL: dropping any one column from it creates duplicates, so the grain
    is not coarser than we claim
  * the date columns really are monthly (always the 1st) where the sentence says "month"
  * for fact_transactions, which has no natural key, why only txn_id is unique

Read-only. Run from the hw05 folder:   python scripts/02_grain.py
Optional:  python scripts/02_grain.py --data-dir path/to/folder
Save the output for the README:        python scripts/02_grain.py > grain_output.txt
Exit code 0 = every check passed, 1 = something failed.
Requires: pandas
"""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd

GRAIN = {   # table -> columns that identify one row
    "fact_fees": ["client_id", "fee_date"],
    "fact_portfolio_snapshot": ["client_id", "snapshot_date"],
}
SENTENCES = {
    "fact_fees": "One row represents one fee charged to one client in one month.",
    "fact_portfolio_snapshot": "One row represents one client's account at the start of one month.",
    "fact_transactions": "One row represents one transaction by one client on one date.",
}
MONTHLY_DATE_COL = {"fact_fees": "fee_date", "fact_portfolio_snapshot": "snapshot_date"}
TXN_NATURAL_KEY = ["client_id", "txn_date", "txn_type", "security_id"]

failures = []


def check(ok, label, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"  ({detail})" if detail else ""))
    if not ok:
        failures.append(label)


def load(data_dir):
    out = {}
    for p in sorted(data_dir.glob("fact_*.csv")):
        name = re.sub(r"\s*\(\d+\)$", "", p.stem).strip()
        out[name] = pd.read_csv(p, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parent.parent)
    data_dir = ap.parse_args().data_dir
    T = load(data_dir)
    print(f"HW5 Part B: grain  |  data folder: {data_dir}")

    for t in SENTENCES:
        if t not in T:
            print(f"missing table {t}")
            return 1

    for t, key in GRAIN.items():
        df = T[t]
        print(f"\n{t}\n  {SENTENCES[t]}\n  grain key: ({', '.join(key)})")
        dup = int(df.duplicated(key, keep=False).sum())
        check(dup == 0, f"grain key is unique", f"{len(df):,} rows, {df[key].drop_duplicates().shape[0]:,} distinct keys, {dup} duplicate rows")
        for c in key:                                   # minimality: remove one column at a time
            smaller = [k for k in key if k != c]
            n = int(df.duplicated(smaller, keep=False).sum())
            check(n > 0, f"key is minimal: without {c}, ({', '.join(smaller)}) repeats", f"{n:,} rows repeat")
        dc = MONTHLY_DATE_COL[t]
        first = df[dc].str[8:] == "01"
        check(first.all(), f"{dc} is always the 1st of a month", f"{int(first.sum()):,} of {len(df):,} rows; "
              f"{df[dc].nunique()} distinct months")
        if t == "fact_fees":
            per = df.groupby(["client_id", "fee_date"]).fee_type.nunique().max()
            check(per == 1, "each client-month holds a single fee type", f"max fee types per client-month = {per}")
        if t == "fact_portfolio_snapshot":
            per = df.groupby("client_id")[["account_type", "benchmark_id"]].nunique().max().to_dict()
            check(max(per.values()) == 1, "each client has one account type and one benchmark throughout", str(per))

    t = "fact_transactions"
    df = T[t]
    print(f"\n{t}\n  {SENTENCES[t]}\n  grain key: (txn_id)")
    check(df.txn_id.is_unique, "txn_id is unique", f"{len(df):,} rows")
    rep = df.duplicated(TXN_NATURAL_KEY, keep=False)
    print(f"  natural key candidate ({', '.join(TXN_NATURAL_KEY)}) repeats on {int(rep.sum()):,} rows")
    check(rep.any(), "no natural key exists: the candidate repeats, so it cannot be the grain")
    same_amount = df.duplicated(TXN_NATURAL_KEY + ["amount"], keep=False)
    check(not same_amount.any(), "repeated rows differ in amount, so they are separate transactions",
          f"{int(same_amount.sum())} rows share key + amount")
    full = df.drop(columns="txn_id").duplicated().sum()
    check(full == 0, "no row is an exact copy of another (ignoring txn_id)", f"{int(full)} copies")
    print("  by type, repeated-key rows:", df[rep].txn_type.value_counts().to_dict())

    print(f"\n{'ALL CHECKS PASSED' if not failures else str(len(failures)) + ' CHECK(S) FAILED'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
