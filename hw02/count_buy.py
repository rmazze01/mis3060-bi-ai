import pandas as pd

df = pd.read_csv("../02_Data/raw/fact_transactions.csv")
buy_count = (df["txn_type"] == "Buy").sum()
print(buy_count)
