import csv
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = ROOT / "data" / "raw" / "movies_API.json"
OUTPUT_FILE = ROOT / "data" / "processed" / "movies_API_clean.csv"

COLUMNS = [
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
]

TMDB_GENRES = {
    12: "Adventure",
    14: "Fantasy",
    16: "Animation",
    18: "Drama",
    27: "Horror",
    28: "Action",
    35: "Comedy",
    36: "History",
    37: "Western",
    53: "Thriller",
    80: "Crime",
    99: "Documentary",
    878: "Sci-Fi",
    9648: "Mystery",
    10402: "Music",
    10749: "Romance",
    10751: "Family",
    10752: "War",
    10770: "TV Movie",
}


def clean_value(value):
    if value is None or value == "":
        return "Na"
    return value


def normalize_release_date(value):
    if not value:
        return "Na"
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError):
        return "Na"


def transform_movie(movie):
    released = normalize_release_date(movie.get("release_date"))
    year = released[:4] if released != "Na" else "Na"
    genre_ids = movie.get("genre_ids") or []
    genres = [
        TMDB_GENRES.get(genre_id, f"TMDB:{genre_id}")
        for genre_id in genre_ids
    ]

    transformed = {column: "Na" for column in COLUMNS}
    transformed.update(
        {
            "name": clean_value(movie.get("title")),
            "genre": ", ".join(genres) if genres else "Na",
            "year": year,
            "released": released,
            "score": clean_value(movie.get("vote_average")),
            "votes": clean_value(movie.get("vote_count")),
        }
    )
    return transformed


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"JSON file not found: {INPUT_FILE}")

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    movies = payload.get("results", []) if isinstance(payload, dict) else payload
    if not isinstance(movies, list):
        raise ValueError("The JSON must contain a list of movies under 'results'.")

    records = [
        transform_movie(movie)
        for movie in movies
        if isinstance(movie, dict) and movie.get("title")
    ]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(records)

    print(f"Movies transformed: {len(records)}")
    print(f"File created: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
