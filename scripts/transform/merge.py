import csv
import re
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CSV_FILE = ROOT / "data" / "processed" / "movies_clean.csv"
API_CLEAN_FILE = ROOT / "data" / "processed" / "movies_API_clean.csv"
OUTPUT_FILE = ROOT / "data" / "processed" / "movies_merged.csv"

MOVIE_COLUMNS = (
    "name",
    "rating",
    "genre",
    "year",
    "released",
    "score",
    "votes",
    "director",
    "writer",
    "star",
    "country",
    "budget",
    "gross",
    "company",
    "runtime",
)
OUTPUT_COLUMNS = ("source", "source_key", "tmdb_source_key", *MOVIE_COLUMNS)
MISSING_VALUES = {"", "na", "n/a", "nan", "null", "none"}


def is_missing(value):
    return value is None or str(value).strip().casefold() in MISSING_VALUES


def read_records(file_path, source):
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    records = []
    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != list(MOVIE_COLUMNS):
            raise ValueError(
                f"Unexpected columns in {file_path.name}: {reader.fieldnames}"
            )
        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(
                    f"CSV line {row_number}: extra columns detected."
                )
            if is_missing(row.get("name")):
                continue
            records.append(
                {
                    **row,
                    "source": source,
                    "source_key": f"row:{row_number}",
                }
            )
    return records


def movie_identity(record):
    name = record.get("name")
    if is_missing(name):
        return None

    normalized_name = unicodedata.normalize("NFKD", name)
    normalized_name = "".join(
        character
        for character in normalized_name
        if not unicodedata.combining(character)
    )
    normalized_name = normalized_name.casefold()
    normalized_name = " ".join(
        re.sub(r"[^a-z0-9]+", " ", normalized_name).split()
    )
    if not normalized_name:
        return None

    year = record.get("year")
    try:
        year = int(float(year))
    except (TypeError, ValueError):
        release_date = record.get("released", "")
        match = re.match(r"^\s*(\d{4})", release_date)
        if match is None:
            return None
        year = int(match.group(1))

    return normalized_name, year


def merge_records(csv_records, api_records):
    csv_identities = [movie_identity(record) for record in csv_records]
    api_identities = [movie_identity(record) for record in api_records]
    csv_counts = Counter(identity for identity in csv_identities if identity)
    api_counts = Counter(identity for identity in api_identities if identity)
    api_by_identity = {
        identity: record
        for identity, record in zip(api_identities, api_records)
        if identity and api_counts[identity] == 1
    }

    matched_api_keys = set()
    merged_records = []
    for csv_record, identity in zip(csv_records, csv_identities):
        api_record = None
        if (
            identity
            and csv_counts[identity] == 1
            and api_counts[identity] == 1
        ):
            api_record = api_by_identity[identity]
            matched_api_keys.add(api_record["source_key"])

        merged = {
            "source": "csv",
            "source_key": csv_record["source_key"],
            "tmdb_source_key": (
                api_record["source_key"] if api_record is not None else ""
            ),
        }
        for column in MOVIE_COLUMNS:
            csv_value = csv_record.get(column)
            api_value = api_record.get(column) if api_record else None
            merged[column] = (
                csv_value if not is_missing(csv_value) else
                api_value if not is_missing(api_value) else
                ""
            )
        merged_records.append(merged)

    for api_record in api_records:
        if api_record["source_key"] in matched_api_keys:
            continue
        merged_records.append(
            {
                "source": "tmdb",
                "source_key": api_record["source_key"],
                "tmdb_source_key": "",
                **{column: api_record.get(column, "") for column in MOVIE_COLUMNS},
            }
        )

    return merged_records


def main():
    csv_records = read_records(CSV_FILE, "csv")
    api_records = read_records(API_CLEAN_FILE, "tmdb")
    records = merge_records(csv_records, api_records)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(records)

    matched_count = sum(
        bool(record["tmdb_source_key"]) for record in records
    )
    print(f"Movies merged: {len(records)}")
    print(f"CSV/API matches: {matched_count}")
    print(f"File created: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
