import pandas as pd

# Path to the CSV file
csv_file_path = 'data/raw/movies.csv'

# Transform the CSV into a Pandas DataFrame
try:
    df_csv = pd.read_csv(csv_file_path)
    print("Data successfully extracted from CSV:")
    print(df_csv.head())
except FileNotFoundError:
    print(f"Error: The file '{csv_file_path}' was not found.")
except Exception as e:
    print(f"An error occurred while reading the CSV: {e}")

# Fix formats in the database:
