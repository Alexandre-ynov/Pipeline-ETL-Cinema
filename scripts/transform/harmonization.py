import pandas as pd

# Chemin vers le fichier CSV
csv_file_path = 'data/raw/movies.csv'

#On transforme le CSV en DataFrame Pandas
try:
    df_csv = pd.read_csv(csv_file_path)
    print("Données extraites du CSV avec succès :")
    print(df_csv.head())
except FileNotFoundError:
    print(f"Erreur: Le fichier '{csv_file_path}' n'a pas été trouvé.")
except Exception as e:
    print(f"Une erreur est survenue lors de la lecture du CSV : {e}")

#On corrige les formats dans la DataBase : 

