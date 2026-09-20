import pandas as pd

df = pd.read_csv("../02_Data/raw/fact_transactions.csv")

total_rows = len(df)
excluded = df["txn_type"].isin(["Sell", "Deposit", "Withdrawal", "Dividend", "Advisory Fee"]).sum()

result = total_rows - excluded
print(result)
