import csv
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CSV_FILE = ROOT / "data" / "processed" / "movies_clean.csv"
API_CLEAN_FILE = ROOT / "data" / "processed" / "movies_API_clean.csv"
SQL_FILE = ROOT / "database" / "database.sql"
DB_FILE = ROOT / "database" / "movies.db"

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

def clean_text(value):
	if value is None:
		return None
	value = str(value).strip()
	if not value or value.casefold() in {"na", "n/a", "nan", "null", "none"}:
		return None
	return value


def parse_number(value, integer=False):
	value = clean_text(value)
	if value is None:
		return None
	try:
		number = float(value.replace(",", ""))
	except ValueError:
		return None
	if integer:
		return int(number)
	return number


def parse_release_date(value):
	value = clean_text(value)
	if value is None:
		return None

	value = value.split(" (", maxsplit=1)[0].strip()
	for date_format in ("%Y-%m-%d", "%B %d, %Y", "%b %d, %Y", "%m/%d/%Y"):
		try:
			return datetime.strptime(value, date_format).date().isoformat()
		except ValueError:
			continue
	return None


def parse_year(value, released=None):
	year = parse_number(value, integer=True)
	if year is not None:
		return year
	if released:
		return int(released[:4])
	return None


def normalize_record(values, source, source_key):
	record = {column: clean_text(values.get(column)) for column in MOVIE_COLUMNS}
	record["year"] = parse_year(values.get("year"), record["released"])
	record["released"] = parse_release_date(values.get("released"))
	for column in ("score",):
		record[column] = parse_number(values.get(column))
	for column in ("votes", "budget", "gross", "runtime"):
		record[column] = parse_number(values.get(column), integer=True)
	record["source"] = source
	record["source_key"] = source_key
	return record


def load_csv_records(file_path, source):
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
			name = clean_text(row.get("name"))
			if name is None:
				continue
			source_key = f"row:{row_number}"
			records.append(normalize_record(row, source, source_key))
	return records


def load_records(records):
	if not SQL_FILE.exists():
		raise FileNotFoundError(f"SQL schema not found: {SQL_FILE}")

	DB_FILE.parent.mkdir(parents=True, exist_ok=True)
	columns = ("source", "source_key", *MOVIE_COLUMNS)
	placeholders = ", ".join("?" for _ in columns)
	updates = ", ".join(
		f"{column} = excluded.{column}"
		for column in MOVIE_COLUMNS
	)
	query = (
		f"INSERT INTO movies ({', '.join(columns)}) VALUES ({placeholders}) "
		"ON CONFLICT(source, source_key) DO UPDATE SET "
		f"{updates}"
	)

	with closing(sqlite3.connect(DB_FILE)) as connection:
		with connection:
			connection.executescript(SQL_FILE.read_text(encoding="utf-8"))
			connection.executemany(
				query,
				[tuple(record[column] for column in columns) for record in records],
			)


def main():
	records = load_csv_records(CSV_FILE, "csv")
	records += load_csv_records(API_CLEAN_FILE, "tmdb")
	load_records(records)
	print(f"Loading complete: {len(records)} records processed.")
	print(f"SQLite database: {DB_FILE}")


if __name__ == "__main__":
	main()
