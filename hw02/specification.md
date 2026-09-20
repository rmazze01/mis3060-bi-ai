# Specification: Transaction Data EDA Script

## Purpose

Write **one single Python script** that performs a complete exploratory data analysis (EDA) of a financial transactions dataset. The script must run start to finish in a single execution and produce console output, a saved text summary, and three saved chart images. Do not split this into multiple scripts or multiple runs — every step below belongs in the same file.

## Input

The script loads the file `data/raw/fact_transactions.csv` into a pandas DataFrame. This is the only input file.

## Required Behavior

The script must perform the following steps, in order, all within one run:

1. **Load the data.** Read `data/raw/fact_transactions.csv` into a pandas DataFrame.

2. **Report the shape.** Print the number of rows and the number of columns.

3. **Report columns and types.** Print every column name along with its data type.

4. **Report missing values.** Print the count of missing (null) values for every column, even columns with zero missing values.

5. **Report descriptive statistics.** For all numeric columns, print count, mean, standard deviation, minimum, 25th percentile, median, 75th percentile, and maximum.

6. **Report transaction type frequency.** Print the value counts and the percentage of total for the `txn_type` column, sorted from the most frequent type to the least frequent.

7. **Report unique entity counts.** Print the number of unique clients, the number of unique advisors, and the number of unique securities referenced anywhere in the file.

8. **Report the date range.** Print the earliest and latest value in `txn_date`.

9. **Check for duplicate transactions.** Check whether any `txn_id` value appears more than once, and print how many duplicate rows exist.

10. **Report the shape of the `amount` column.** Print the mean, median, and skewness of `amount`.

11. **Summarize amount by transaction type.** Group the data by `txn_type`. For each type, print the count of transactions, the mean `amount`, and the median `amount`, with both amounts rounded to two decimal places. Sort the results by mean amount from highest to lowest.

12. **Report correlations.** Compute the correlation matrix for `shares`, `price`, and `amount`, rounded to two decimal places, and print it. Then identify and print the three strongest correlations among these variables, excluding any variable's correlation with itself.

13. **Investigate negative share values.** For the `shares` column, broken out by `txn_type`, print the minimum value, the maximum value, and the count of negative values in each group.

14. **Validate the shape.** Compare the DataFrame's shape to the expected shape of 298,772 rows and 9 columns. If it does not match, print a clearly visible warning message.

15. **Generate and save three charts**, each saved as a PNG file in a folder named `hw02/charts/`:
    - A histogram of the `amount` column, with a vertical line marking the mean and a separate vertical line marking the median, both clearly labeled (for example, in a legend). Save this as `hw02/charts/hist_amount.png`.
    - A horizontal box plot of `amount`, broken out by `txn_type`. Save this as `hw02/charts/box_amount_by_type.png`.
    - A scatter plot with `shares` on the x-axis and `amount` on the y-axis, with points colored according to `txn_type`. Save this as `hw02/charts/scatter_shares_amount.png`.

16. **Save a text summary.** Write a plain-text file to `hw02/hw02_profile.txt` containing the results of steps 2 through 13 (shape, column types, missing values, descriptive statistics, transaction type frequency, unique entity counts, date range, duplicate count, amount statistics, grouped amount summary, correlation matrix and top correlations, and the negative-shares breakdown). This should be the same information printed to the console during those steps, saved in readable plain text.

17. **Include a header comment block.** At the very top of the script, include a comment block identifying: the name/purpose of the script, the dataset it analyzes, the author, and the date the script was generated.

## Output Locations

- Console output: all print statements from steps 2 through 14 should appear when the script runs.
- `hw02/hw02_profile.txt`: plain-text summary of steps 2 through 13.
- `hw02/charts/hist_amount.png`, `hw02/charts/box_amount_by_type.png`, `hw02/charts/scatter_shares_amount.png`: the three saved charts.

## Constraints

- This must be **one Python script**, executed **once**, that performs all 17 steps above in a single run — not separate scripts for separate steps.
- Do not skip or reorder the steps; each one should be clearly identifiable in the script (for example, with section comments) and in the output.
- The script should run without requiring manual intervention once started.
