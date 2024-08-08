import pandas as pd

# Read the CSV file
df = pd.read_csv('touchtunes_collection_example.csv', header=None)

# Rotate the DataFrame 90 degrees to the right
rotated_df = df.T

# Display the rotated DataFrame
print(rotated_df)
