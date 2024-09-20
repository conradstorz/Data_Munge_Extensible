import pandas as pd

# Load the CSV file
file_path = 'kio.csv'
df = pd.read_csv(file_path)

# Clean the data by stripping leading/trailing spaces from all columns
df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

# Create two separate dataframes for total and declined transactions
df_total = df.groupby('Machine ID')['Total Amount ($)'].sum().reset_index()

# Filter out only rows where 'Transaction Type' contains 'DECLINED' for the declined subtotal
df_declined = df[df['Response Code'].str.contains("declined", case=False, na=False)]
df_declined_total = df_declined.groupby('Machine ID')['Total Amount ($)'].sum().reset_index()

# Rename the columns for clarity
df_total.rename(columns={'Total Amount ($)': 'Total Transactions Amount ($)'}, inplace=True)
df_declined_total.rename(columns={'Total Amount ($)': 'Declined Transactions Amount ($)'}, inplace=True)

# Merge the two subtotals by 'Machine ID'
df_final = pd.merge(df_total, df_declined_total, on='Machine ID', how='left')

# Fill any NaN values in the declined amount column with 0 (in case there are no declined transactions for some machines)
df_final['Declined Transactions Amount ($)'] = df_final['Declined Transactions Amount ($)'].fillna(0)

# Subtract the Declined Transactions from the Total Transactions to get the Net Amount
df_final['Net Transactions Amount ($)'] = df_final['Total Transactions Amount ($)'] - df_final['Declined Transactions Amount ($)']

# Save the final report to a CSV file
df_final.to_csv('final_report_with_net_total_by_machine_id.csv', index=False)

# Display the final report (optional)
print(df_final)
