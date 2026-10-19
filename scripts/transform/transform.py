
from pathlib import Path
import csv
import pandas as pd

# 1. Définir les chemins
ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = ROOT / "data" / "raw" / "movies.csv"
OUTPUT_FILE = ROOT / "data" / "processed" / "movies_clean.csv"

COLUMNS = [
    "name", "rating", "genre", "year", "released", "score",
    "votes", "director", "writer", "star", "country",
    "budget", "gross", "company", "runtime"
]

# 2. Vérifier le fichier source
if not INPUT_FILE.exists():
    raise FileNotFoundError(f"Fichier introuvable : {INPUT_FILE}")

rows = []
errors = []

# 3. Lire et corriger le format irrégulier
with open(INPUT_FILE, "r", encoding="utf-8-sig", newline="") as file:
    for line_number, line in enumerate(file, start=1):
        line = line.rstrip("\r\n")

        if line_number == 1:
            continue  # En-tête traité séparément

        if not line.strip():
            continue

        # Certaines lignes sont entièrement entourées de guillemets.
        if line.startswith('"') and line.endswith('";'):
            line = line[1:-2]
        elif line.startswith('"') and line.endswith('"'):
            line = line[1:-1]

        # Décoder les guillemets doublés du CSV.
        line = line.replace('""', '"')

        try:
            fields = next(csv.reader([line], strict=True))
        except csv.Error as error:
            errors.append((line_number, f"Erreur CSV : {error}", line))
            continue

        # Si des colonnes supplémentaires existent, elles peuvent
        # provenir de virgules dans le titre. On les regroupe au début.
        if len(fields) > len(COLUMNS):
            extra = len(fields) - len(COLUMNS)
            fields = [",".join(fields[:extra + 1])] + fields[extra + 1:]

        if len(fields) != len(COLUMNS):
            errors.append((
                line_number,
                f"{len(fields)} colonnes au lieu de {len(COLUMNS)}",
                line
            ))
            continue

        rows.append(fields)

# 4. Construire le DataFrame
df = pd.DataFrame(rows, columns=COLUMNS)

# Correction ciblée du titre mal formaté dans la source
mask = df["name"].eq('Code Geass: Lelouch of the Re;"Surrection')
df.loc[mask, "name"] = "Code Geass: Lelouch of the Re;Surrection"

# 5. Nettoyer les espaces et les valeurs vides
for column in df.columns:
    df[column] = df[column].map(
        lambda value: value.strip() if isinstance(value, str) else value
    )
    df[column] = df[column].replace("", pd.NA)

# 6. Convertir les colonnes numériques
numeric_columns = [
    "year", "score", "votes", "budget", "gross", "runtime"
]

for column in numeric_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

# 7. Vérifier les doublons exacts
duplicates = df.duplicated().sum()
df = df.drop_duplicates()

# Nettoyage des colonnes textuelles
text_columns = df.select_dtypes(include=["object", "str"]).columns

for column in text_columns:
    df[column] = df[column].str.strip()

# Remplacer les chaînes vides par des valeurs manquantes
df.replace(r"^\s*$", pd.NA, regex=True, inplace=True)

# Vérifications après nettoyage
print("\n--- CONTRÔLE FINAL ---")
print("Dimensions :", df.shape)
print("Titres vides :", df["name"].isna().sum())
print("Doublons exacts :", df.duplicated().sum())
print("\nValeurs manquantes :")
print(df.isna().sum())


# --- GESTION DES VALEURS MANQUANTES ---

# Uniformiser les chaînes vides et les espaces seuls
df.replace(r"^\s*$", pd.NA, regex=True, inplace=True)

# Afficher le nombre de valeurs manquantes par colonne
print("\n--- GESTION DES VALEURS MANQUANTES ---")

missing_values = df.isna().sum()

for column, count in missing_values.items():
    if count > 0:
        percentage = count / len(df) * 100
        print(
            f"{column} : {count} valeurs manquantes "
            f"({percentage:.2f} %)"
        )

print(
    "\nStratégie : les valeurs manquantes sont conservées "
    "lorsqu'aucune valeur fiable ne permet de les remplacer."
)

# 8. Créer le dossier de sortie et exporter
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

# 9. Afficher le bilan
print("\n--- BILAN DU NETTOYAGE ---")
print(f"Lignes correctement lues : {len(rows)}")
print(f"Doublons exacts supprimés : {duplicates}")
print(f"Lignes mises en anomalie : {len(errors)}")
print(f"Dimensions finales : {df.shape[0]} lignes, {df.shape[1]} colonnes")
print(f"Fichier exporté : {OUTPUT_FILE}")


print("\n--- CONTRÔLE QUALITÉ ---")

# Afficher quelques films avec leurs principales informations
print("\nExemples de films :")
print(
    df[["name", "genre", "year", "score", "budget", "gross"]]
    .head(10)
    .to_string(index=False)
)

# Vérifier les titres qui semblent suspects
print("\nTitres vides :")
print(df["name"].isna().sum())

print("\nAnnées hors de l'intervalle 1888-2026 :")
print(
    df.loc[
        ~df["year"].between(1888, 2026),
        ["name", "year"]
    ].head(20).to_string(index=False)
)

# Vérifier les notes hors de l'intervalle habituel
print("\nNotes renseignées hors de l'intervalle 0-10 :")

invalid_scores = df[
    df["score"].notna()
    & ~df["score"].between(0, 10)
]

print(invalid_scores[["name", "score"]].to_string(index=False))


# Vérifier spécifiquement le film dont le titre posait problème
print("\nRecherche du film Code Geass :")
print(
    df.loc[
        df["name"].str.contains("Code Geass", case=False, na=False),
        ["name", "rating", "genre", "year", "score"]
    ].to_string(index=False)
)


print("\n--- VALEURS MANQUANTES ---")
print(df.isna().sum())

if errors:
    print("\n--- EXEMPLES D'ANOMALIES ---")
    for line_number, reason, content in errors[:10]:
        print(f"Ligne {line_number} : {reason}")
        print(content[:200])


print("\n--- DOUBLONS POTENTIELS ---")

duplicate_names = df[
    df["name"].duplicated(keep=False)
].sort_values("name")


print("\n--- DOUBLONS SUR TITRE, ANNÉE ET RÉALISATEUR ---")

duplicate_movies = df[
    df.duplicated(
        subset=["name", "year", "director"],
        keep=False
    )
].sort_values(["name", "year", "director"])

print(f"Lignes concernées : {len(duplicate_movies)}")

print(
    duplicate_movies[["name", "year", "director"]]
    .to_string(index=False)
)


print(f"Films dont le titre apparaît plusieurs fois : {len(duplicate_names)} lignes")

print(
    duplicate_names[["name", "year", "director"]]
    .head(30)
    .to_string(index=False)
)


print("\n--- TYPES DE DONNÉES ---")
print(df.dtypes)
