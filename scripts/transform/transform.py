
from pathlib import Path
import csv
import pandas as pd

# 1. Define paths
ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = ROOT / "data" / "raw" / "movies.csv"
OUTPUT_FILE = ROOT / "data" / "processed" / "movies_clean.csv"

COLUMNS = [
    "name", "rating", "genre", "year", "released", "score",
    "votes", "director", "writer", "star", "country",
    "budget", "gross", "company", "runtime"
]

# 2. Check the source file
if not INPUT_FILE.exists():
    raise FileNotFoundError(f"File not found: {INPUT_FILE}")

rows = []
errors = []

# 3. Read and fix irregular formatting
with open(INPUT_FILE, "r", encoding="utf-8-sig", newline="") as file:
    for line_number, line in enumerate(file, start=1):
        line = line.rstrip("\r\n")

        if line_number == 1:
            continue  # Header handled separately

        if not line.strip():
            continue

        # Some lines are entirely wrapped in double quotes.
        if line.startswith('"') and line.endswith('";'):
            line = line[1:-2]
        elif line.startswith('"') and line.endswith('"'):
            line = line[1:-1]

        # Decode doubled CSV quotes.
        line = line.replace('""', '"')

        try:
            fields = next(csv.reader([line], strict=True))
        except csv.Error as error:
            errors.append((line_number, f"CSV error: {error}", line))
            continue

        # If extra columns exist, they may come from commas
        # in the title. Recombine them at the beginning.
        if len(fields) > len(COLUMNS):
            extra = len(fields) - len(COLUMNS)
            fields = [",".join(fields[:extra + 1])] + fields[extra + 1:]

        if len(fields) != len(COLUMNS):
            errors.append((
                line_number,
                f"{len(fields)} columns instead of {len(COLUMNS)}",
                line
            ))
            continue

        rows.append(fields)

# 4. Build the DataFrame
df = pd.DataFrame(rows, columns=COLUMNS)

# Targeted fix for a malformed title in the source
mask = df["name"].eq('Code Geass: Lelouch of the Re;"Surrection')
df.loc[mask, "name"] = "Code Geass: Lelouch of the Re;Surrection"

# 5. Clean whitespace and empty values
for column in df.columns:
    df[column] = df[column].map(
        lambda value: value.strip() if isinstance(value, str) else value
    )
    df[column] = df[column].replace("", pd.NA)

# 6. Convert numeric columns
numeric_columns = [
    "year", "score", "votes", "budget", "gross", "runtime"
]

for column in numeric_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

# 7. Check for exact duplicates
duplicates = df.duplicated().sum()
df = df.drop_duplicates()

# Clean text columns
text_columns = df.select_dtypes(include=["object", "str"]).columns

for column in text_columns:
    df[column] = df[column].str.strip()

# Replace empty strings with missing values
df.replace(r"^\s*$", pd.NA, regex=True, inplace=True)

# Post-cleaning checks
print("\n--- FINAL CHECK ---")
print("Dimensions:", df.shape)
print("Empty titles:", df["name"].isna().sum())
print("Exact duplicates:", df.duplicated().sum())
print("\nMissing values:")
print(df.isna().sum())


# --- MISSING VALUES HANDLING ---

# Normalize empty strings and whitespace-only values
df.replace(r"^\s*$", pd.NA, regex=True, inplace=True)

# Display the number of missing values per column
print("\n--- MISSING VALUES HANDLING ---")

missing_values = df.isna().sum()

for column, count in missing_values.items():
    if count > 0:
        percentage = count / len(df) * 100
        print(
            f"{column}: {count} missing values "
            f"({percentage:.2f}%)"
        )

print(
    "\nStrategy: missing values are kept "
    "when no reliable replacement value is available."
)

# 8. Create the output directory and export
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

# 9. Display the cleaning summary
print("\n--- CLEANING SUMMARY ---")
print(f"Lines successfully read: {len(rows)}")
print(f"Exact duplicates removed: {duplicates}")
print(f"Lines flagged as anomalies: {len(errors)}")
print(f"Final dimensions: {df.shape[0]} rows, {df.shape[1]} columns")
print(f"File exported: {OUTPUT_FILE}")


print("\n--- QUALITY CONTROL ---")

# Display some movies with their main information
print("\nSample movies:")
print(
    df[["name", "genre", "year", "score", "budget", "gross"]]
    .head(10)
    .to_string(index=False)
)

# Check for suspicious titles
print("\nEmpty titles:")
print(df["name"].isna().sum())

print("\nYears outside the 1888-2026 range:")
print(
    df.loc[
        ~df["year"].between(1888, 2026),
        ["name", "year"]
    ].head(20).to_string(index=False)
)

# Check for scores outside the usual range
print("\nScores outside the 0-10 range:")

invalid_scores = df[
    df["score"].notna()
    & ~df["score"].between(0, 10)
]

print(invalid_scores[["name", "score"]].to_string(index=False))


# Check specifically for the movie with the problematic title
print("\nSearch for Code Geass movie:")
print(
    df.loc[
        df["name"].str.contains("Code Geass", case=False, na=False),
        ["name", "rating", "genre", "year", "score"]
    ].to_string(index=False)
)


print("\n--- MISSING VALUES ---")
print(df.isna().sum())

if errors:
    print("\n--- ANOMALY EXAMPLES ---")
    for line_number, reason, content in errors[:10]:
        print(f"Line {line_number}: {reason}")
        print(content[:200])


print("\n--- POTENTIAL DUPLICATES ---")

duplicate_names = df[
    df["name"].duplicated(keep=False)
].sort_values("name")


print("\n--- DUPLICATES ON TITLE, YEAR, AND DIRECTOR ---")

duplicate_movies = df[
    df.duplicated(
        subset=["name", "year", "director"],
        keep=False
    )
].sort_values(["name", "year", "director"])

print(f"Rows affected: {len(duplicate_movies)}")

print(
    duplicate_movies[["name", "year", "director"]]
    .to_string(index=False)
)


print(f"Movies with duplicate titles: {len(duplicate_names)} rows")

print(
    duplicate_names[["name", "year", "director"]]
    .head(30)
    .to_string(index=False)
)


print("\n--- DATA TYPES ---")
print(df.dtypes)
