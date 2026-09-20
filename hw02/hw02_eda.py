"""
Script: hw02_eda.py
Purpose: Exploratory Data Analysis (EDA) of a financial transactions dataset
Dataset: data/raw/fact_transactions.csv (fact_transactions.csv)
Author: Rose Mazzeo
Generated: 2026-09-17
"""

import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Setup: resolve paths relative to this script's location so the script runs
# correctly no matter what directory it is launched from.
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

# Primary expected location: <project_root>/data/raw/fact_transactions.csv
# Fallback: this project's actual folder layout, 02_Data/raw/fact_transactions.csv
CANDIDATE_PATHS = [
    os.path.join(PROJECT_ROOT, "data", "raw", "fact_transactions.csv"),
    os.path.join(PROJECT_ROOT, "02_Data", "raw", "fact_transactions.csv"),
]
DATA_PATH = next((p for p in CANDIDATE_PATHS if os.path.exists(p)), CANDIDATE_PATHS[0])

CHARTS_DIR = os.path.join(SCRIPT_DIR, "charts")
PROFILE_PATH = os.path.join(SCRIPT_DIR, "hw02_profile.txt")

os.makedirs(CHARTS_DIR, exist_ok=True)

EXPECTED_SHAPE = (298772, 9)

# Collects the same text that gets printed to the console for steps 2-13,
# so it can also be written out to hw02_profile.txt.
summary_lines = []


def emit(text=""):
    """Print to console and also capture for the text summary file."""
    print(text)
    summary_lines.append(text)


# ---------------------------------------------------------------------------
# 1. Load the data
# ---------------------------------------------------------------------------
if not os.path.exists(DATA_PATH):
    sys.exit(f"ERROR: could not find data file. Tried: {CANDIDATE_PATHS}")

df = pd.read_csv(DATA_PATH, parse_dates=["txn_date"])

print(f"Loaded data from: {DATA_PATH}\n")

# ---------------------------------------------------------------------------
# 2. Shape
# ---------------------------------------------------------------------------
emit("=" * 70)
emit("2. DATASET SHAPE")
emit("=" * 70)
emit(f"Rows: {df.shape[0]:,}    Columns: {df.shape[1]}")
emit("")

# ---------------------------------------------------------------------------
# 3. Column names and data types
# ---------------------------------------------------------------------------
emit("=" * 70)
emit("3. COLUMN NAMES AND DATA TYPES")
emit("=" * 70)
emit(df.dtypes.to_string())
emit("")

# ---------------------------------------------------------------------------
# 4. Missing values per column
# ---------------------------------------------------------------------------
emit("=" * 70)
emit("4. MISSING VALUES PER COLUMN")
emit("=" * 70)
emit(df.isna().sum().to_string())
emit("")

# ---------------------------------------------------------------------------
# 5. Descriptive statistics for numeric columns
# ---------------------------------------------------------------------------
emit("=" * 70)
emit("5. DESCRIPTIVE STATISTICS (NUMERIC COLUMNS)")
emit("=" * 70)
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
desc = df[numeric_cols].describe().T
desc["median"] = df[numeric_cols].median()
desc = desc[["count", "mean", "std", "min", "25%", "50%", "75%", "max"]]
emit(desc.to_string())
emit("")

# ---------------------------------------------------------------------------
# 6. txn_type value counts and percentages
# ---------------------------------------------------------------------------
emit("=" * 70)
emit("6. TRANSACTION TYPE FREQUENCY")
emit("=" * 70)
type_counts = df["txn_type"].value_counts().sort_values(ascending=False)
type_pcts = (type_counts / type_counts.sum() * 100).round(2)
freq_table = pd.DataFrame({"count": type_counts, "percent": type_pcts})
emit(freq_table.to_string())
emit("")

# ---------------------------------------------------------------------------
# 7. Unique clients, advisors, securities
# ---------------------------------------------------------------------------
emit("=" * 70)
emit("7. UNIQUE ENTITY COUNTS")
emit("=" * 70)
emit(f"Unique clients:    {df['client_id'].nunique():,}")
emit(f"Unique advisors:   {df['advisor_id'].nunique():,}")
emit(f"Unique securities: {df['security_id'].nunique():,}")
emit("")

# ---------------------------------------------------------------------------
# 8. Date range
# ---------------------------------------------------------------------------
emit("=" * 70)
emit("8. DATE RANGE")
emit("=" * 70)
emit(f"Earliest txn_date: {df['txn_date'].min().date()}")
emit(f"Latest txn_date:   {df['txn_date'].max().date()}")
emit("")

# ---------------------------------------------------------------------------
# 9. Duplicate txn_id check
# ---------------------------------------------------------------------------
emit("=" * 70)
emit("9. DUPLICATE TRANSACTIONS (BY txn_id)")
emit("=" * 70)
dup_count = df["txn_id"].duplicated().sum()
emit(f"Duplicate txn_id rows: {dup_count:,}")
emit("")

# ---------------------------------------------------------------------------
# 10. Mean, median, skewness of amount
# ---------------------------------------------------------------------------
emit("=" * 70)
emit("10. AMOUNT: MEAN, MEDIAN, SKEWNESS")
emit("=" * 70)
amount_mean = df["amount"].mean()
amount_median = df["amount"].median()
amount_skew = df["amount"].skew()
# Round with Python's built-in round() (banker's / round-half-to-even)
# rather than string formatting, so values that land exactly on a rounding
# boundary (e.g. 41220.485) round consistently with round()/numpy.round()
# elsewhere in this script instead of however :.2f happens to round the
# underlying binary float.
amount_mean_r = round(amount_mean, 2)
amount_median_r = round(amount_median, 2)
emit(f"Mean amount:     {amount_mean_r:,.2f}")
emit(f"Median amount:   {amount_median_r:,.2f}")
emit(f"Skewness:        {amount_skew:.4f}")
emit("")

# ---------------------------------------------------------------------------
# 11. Group by txn_type: count, mean amount, median amount
# ---------------------------------------------------------------------------
emit("=" * 70)
emit("11. AMOUNT SUMMARY BY TRANSACTION TYPE")
emit("=" * 70)
grouped = df.groupby("txn_type")["amount"].agg(count="count", mean_amount="mean", median_amount="median")
grouped["mean_amount"] = grouped["mean_amount"].round(2)
grouped["median_amount"] = grouped["median_amount"].round(2)
grouped = grouped.sort_values("mean_amount", ascending=False)
emit(grouped.to_string())
emit("")

# ---------------------------------------------------------------------------
# 12. Correlation matrix for shares, price, amount + top 3 correlations
# ---------------------------------------------------------------------------
emit("=" * 70)
emit("12. CORRELATION MATRIX (shares, price, amount)")
emit("=" * 70)
corr_cols = ["shares", "price", "amount"]
corr_matrix = df[corr_cols].corr().round(2)
emit(corr_matrix.to_string())
emit("")

# Identify top 3 strongest correlations, excluding self-correlation and
# duplicate pairs (e.g. only report A-B once, not also B-A).
corr_pairs = []
for i, col_i in enumerate(corr_cols):
    for j, col_j in enumerate(corr_cols):
        if j > i:
            corr_pairs.append((col_i, col_j, corr_matrix.loc[col_i, col_j]))

corr_pairs_sorted = sorted(corr_pairs, key=lambda x: abs(x[2]), reverse=True)[:3]

emit("Top 3 strongest correlations:")
for col_i, col_j, val in corr_pairs_sorted:
    emit(f"  {col_i} <-> {col_j}: {val:.2f}")
emit("")

# ---------------------------------------------------------------------------
# 13. Negative shares breakdown by txn_type
# ---------------------------------------------------------------------------
emit("=" * 70)
emit("13. SHARES: MIN, MAX, NEGATIVE COUNT BY TRANSACTION TYPE")
emit("=" * 70)
shares_summary = df.groupby("txn_type")["shares"].agg(
    min_shares="min",
    max_shares="max",
    negative_count=lambda s: (s < 0).sum(),
)
emit(shares_summary.to_string())
emit("")

# ---------------------------------------------------------------------------
# 14. Shape validation warning
# ---------------------------------------------------------------------------
if df.shape != EXPECTED_SHAPE:
    print("!" * 70)
    print(f"WARNING: DataFrame shape {df.shape} does not match expected shape {EXPECTED_SHAPE}.")
    print("!" * 70)
else:
    print(f"Shape check passed: {df.shape} matches expected {EXPECTED_SHAPE}.")

# ---------------------------------------------------------------------------
# 15. Charts
# ---------------------------------------------------------------------------

# --- Histogram of amount with mean/median lines ---
fig, ax = plt.subplots(figsize=(10, 6))
ax.hist(df["amount"].dropna(), bins=50, color="#4C72B0", edgecolor="white")
ax.axvline(amount_mean, color="red", linestyle="--", linewidth=2, label=f"Mean: {amount_mean_r:,.2f}")
ax.axvline(amount_median, color="green", linestyle="-", linewidth=2, label=f"Median: {amount_median_r:,.2f}")
ax.set_title("Distribution of Transaction Amount")
ax.set_xlabel("Amount")
ax.set_ylabel("Frequency")
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(CHARTS_DIR, "hist_amount.png"), dpi=150)
plt.close(fig)

# --- Horizontal box plot of amount by txn_type ---
fig, ax = plt.subplots(figsize=(10, 6))
type_order = df.groupby("txn_type")["amount"].median().sort_values().index.tolist()
data_by_type = [df.loc[df["txn_type"] == t, "amount"].dropna() for t in type_order]
try:
    ax.boxplot(data_by_type, vert=False, tick_labels=type_order)
except TypeError:
    # Older Matplotlib versions use 'labels' instead of 'tick_labels'
    ax.boxplot(data_by_type, vert=False, labels=type_order)
ax.set_title("Transaction Amount by Type")
ax.set_xlabel("Amount")
ax.set_ylabel("Transaction Type")
fig.tight_layout()
fig.savefig(os.path.join(CHARTS_DIR, "box_amount_by_type.png"), dpi=150)
plt.close(fig)

# --- Scatter plot of shares vs amount, colored by txn_type ---
fig, ax = plt.subplots(figsize=(10, 6))
scatter_df = df.dropna(subset=["shares", "amount"])
types = scatter_df["txn_type"].unique()
colors = plt.cm.tab10(np.linspace(0, 1, len(types)))
for t, c in zip(types, colors):
    subset = scatter_df[scatter_df["txn_type"] == t]
    ax.scatter(subset["shares"], subset["amount"], s=10, alpha=0.5, color=c, label=t)
ax.set_title("Shares vs. Amount by Transaction Type")
ax.set_xlabel("Shares")
ax.set_ylabel("Amount")
ax.legend(markerscale=2, fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(CHARTS_DIR, "scatter_shares_amount.png"), dpi=150)
plt.close(fig)

print(f"\nCharts saved to: {CHARTS_DIR}")

# ---------------------------------------------------------------------------
# 16. Save plain-text summary of items 2-13
# ---------------------------------------------------------------------------
with open(PROFILE_PATH, "w") as f:
    f.write(f"EDA Profile Summary - Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Source data: {DATA_PATH}\n\n")
    f.write("\n".join(summary_lines))

print(f"Text summary saved to: {PROFILE_PATH}")
