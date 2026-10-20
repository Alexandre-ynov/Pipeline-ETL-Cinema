import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
csv_file_path = ROOT / 'data' / 'raw' / 'movies.csv'
api_file_path = ROOT / 'data' / 'raw' / 'movies_API.json'
output_file_path = ROOT / 'data' / 'processed' / 'movies_harmonized.csv'
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
    print(f"Une erreur est survenue lors de la lecture du CSV : {e}")


#On corrige les formats dans la DataBase : 

#Format Date pour les dates de sortie:
try:
    released_values = df_csv['released']
    release_dates = released_values.astype('string').str.extract(
        r'^([A-Za-z]+ \d{1,2}, \d{4})',
        expand=False,
    )
    df_csv['released'] = pd.to_datetime(
        release_dates,
        format='%B %d, %Y',
        errors='coerce',
    )
    unparsed_release_dates = released_values.notna() & df_csv['released'].isna()
    print(
        "Format de la colonne 'released' corrigé. "
        f"Dates non reconnues : {unparsed_release_dates.sum()}."
    )
except KeyError:
    print("Erreur: La colonne 'released' est manquante dans le DataFrame.")

#Format numériques pour year, scores, vote, budget, gross :
try:
    numeric_columns = ['year','score', 'votes', 'budget', 'gross']
    for column in numeric_columns:
        df_csv[column] = pd.to_numeric(df_csv[column], errors='coerce')
    print("Formats numériques corrigés avec succès.")
except KeyError as e:
    print(f"Erreur: La colonne '{e.args[0]}' est manquante dans le DataFrame.")
except Exception as e:
    print(f"Une erreur est survenue lors de la conversion des formats numériques : {e}")

#Format numérique pour la colonne runtime, en supprimant les points-virgules et en convertissant en numérique :
df_csv.columns = df_csv.columns.str.strip().str.rstrip(";")

df_csv["runtime"] = pd.to_numeric(
    df_csv["runtime"].astype("string").str.rstrip(";"),
    errors="coerce",
)



    print(f"An error occurred while reading the CSV: {e}")

# Fix formats in the database:
