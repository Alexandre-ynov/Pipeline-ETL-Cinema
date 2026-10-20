# Pipeline-ETL-Cinema 

## Topic

**Which movie genre has been the most popular over the years?**

We chose to develop an ETL pipeline focused on the movie industry. This pipeline collects data from multiple sources, cleans and harmonizes it, and loads it into a structured SQLite database ready for analysis.

---

## Table of Contents

- [Project Structure](#project-structure)
- [Data Sources](#data-sources)
- [Pipeline Architecture](#pipeline-architecture)
  - [Step 1 — Extraction](#step-1--extraction)
  - [Step 2 — Transformation](#step-2--transformation)
  - [Step 3 — Loading](#step-3--loading)
- [Database Schema](#database-schema)
- [Installation & Usage](#installation--usage)
- [Known Issues & Fixes](#known-issues--fixes)
- [Requirements](#requirements)

---

## Project Structure

```
Pipeline-ETL-Cinema/
├── data/
│   ├── raw/                          # Raw source data (untouched)
│   │   ├── movies.csv                # Kaggle dataset (~7,668 movies)
│   │   └── movies_API.json           # TMDB API response (20 movies)
│   └── processed/                    # Cleaned & transformed data
│       ├── movies_clean.csv          # Cleaned CSV data
│       └── movies_API_clean.csv      # Cleaned API data
├── database/
│   ├── database.sql                  # SQL schema definition
│   └── movies.db                     # SQLite database (7,688 records)
├── notebooks/
│   └── notebook.ipynb                # Exploration & prototyping notebook
├── scripts/
│   ├── extract/
│   │   └── extract.py                # API extraction script
│   ├── transform/
│   │   ├── transform.py              # CSV cleaning & transformation
│   │   ├── transformJson.py          # JSON (API) transformation
│   │   └── harmonization.py          # Format harmonization (prototype)
│   └── load/
│       └── load.py                   # Database loading script
├── requirements/
│   └── requirements.txt              # Python dependencies
├── .env                              # API credentials (not tracked by git)
├── .gitignore
└── README.md
```

---

## Data Sources

| Source | Type | Description | Volume |
|--------|------|-------------|--------|
| [Kaggle — The Movie Dataset](https://www.kaggle.com/code/ericyooon/the-movie-datasetgit) | CSV file | Comprehensive dataset of movies (1980–2020) with ratings, budget, gross revenue, cast, etc. | ~7,668 movies |
| [TMDB API](https://developer.themoviedb.org/) | REST API | The Movie Database public API — discover endpoint returning recent/popular movies | 20 movies per request |

### Why these sources?

- **Kaggle CSV**: Provides a large historical dataset spanning 40 years of cinema, with detailed information on budgets, revenues, ratings, genres, directors, and actors — ideal for trend analysis.
- **TMDB API**: Supplements the Kaggle data with current movie listings, demonstrating live API integration in the ETL pipeline and ensuring the dataset stays up-to-date.

---

## Pipeline Architecture

### Step 1 — Extraction

**Script:** `scripts/extract/extract.py`

The extraction phase collects data from two sources:

1. **CSV File** — The Kaggle dataset (`movies.csv`) is downloaded manually and placed in `data/raw/`. It contains 7,668 movies with 15 columns: name, rating, genre, year, released, score, votes, director, writer, star, country, budget, gross, company, runtime.

2. **TMDB API** — The script calls the TMDB `/discover/movie` endpoint using either a Bearer token (`JETON`) or an API key (`CLE_API`) configured in the `.env` file. The JSON response is saved to `data/raw/movies_API.json`.

**Output:** Raw data files in `data/raw/`

### Step 2 — Transformation

**Scripts:** `scripts/transform/transform.py`, `scripts/transform/transformJson.py`

#### CSV Transformation (`transform.py`)

The CSV cleaning process handles several data quality challenges:

- **Irregular formatting**: Some rows are wrapped in double quotes or contain escaped quote characters. The script manually parses each line to handle these edge cases.
- **Extra columns**: Lines with commas in movie titles produce extra fields; these are recombined into the `name` column.
- **Specific fixes**: The title "Code Geass: Lelouch of the Re;Surrection" required targeted correction due to malformed quoting.
- **Whitespace trimming**: All string columns are stripped of leading/trailing whitespace.
- **Missing values**: Empty strings are replaced with `NA`. The strategy is to preserve missing values when no reliable replacement is available.
- **Numeric conversion**: Columns `year`, `score`, `votes`, `budget`, `gross`, and `runtime` are converted to numeric types.
- **Duplicate detection**: Exact duplicates are removed; near-duplicates (same name + year + director) are flagged.
- **Quality checks**: Validates titles are non-empty, years fall within 1888–2026, and scores are between 0–10.

#### JSON/API Transformation (`transformJson.py`)

The API data transformation:

- Maps TMDB genre IDs to human-readable genre names using a lookup dictionary (28 → Action, 18 → Drama, etc.).
- Normalizes release dates to ISO format (`YYYY-MM-DD`).
- Extracts the year from the release date.
- Maps TMDB fields (`title`, `vote_average`, `vote_count`) to the unified schema.
- Fields not available from TMDB (director, writer, star, country, budget, gross, company, runtime) are set to `Na`.

**Output:** Cleaned data in `data/processed/`

### Step 3 — Loading

**Script:** `scripts/load/load.py`

The loading phase integrates all cleaned data into a SQLite database:

- **Schema creation**: Executes `database/database.sql` to create the `movies` table with proper types and constraints.
- **Data normalization**: All records are re-parsed and normalized (dates, numbers, text) before insertion.
- **Upsert logic**: Uses `INSERT ... ON CONFLICT DO UPDATE` to handle re-runs without creating duplicates. Each record is uniquely identified by `(source, source_key)`.
- **Source tracking**: Each row is tagged with its origin (`csv` or `tmdb`) and a source key for traceability.
- **Loads both** `movies_clean.csv` (7,668 records) and `movies_API_clean.csv` (20 records).

**Output:** `database/movies.db` containing 7,688 records

---

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS movies (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    rating      TEXT,
    genre       TEXT,
    year        INTEGER,
    released    TEXT CHECK (
        released IS NULL
        OR (length(released) = 10
            AND substr(released, 5, 1) = '-'
            AND substr(released, 8, 1) = '-')
    ),
    score       REAL,
    votes       INTEGER,
    director    TEXT,
    writer      TEXT,
    star        TEXT,
    country     TEXT,
    budget      INTEGER,
    gross       INTEGER,
    company     TEXT,
    runtime     INTEGER,
    source      TEXT NOT NULL CHECK (source IN ('csv', 'tmdb')),
    source_key  TEXT NOT NULL,
    UNIQUE (source, source_key)
);

CREATE INDEX IF NOT EXISTS idx_movies_name ON movies (name);
CREATE INDEX IF NOT EXISTS idx_movies_year ON movies (year);
```

**Key design choices:**
- `released` has a CHECK constraint ensuring ISO date format (`YYYY-MM-DD`).
- `source` + `source_key` composite unique constraint enables idempotent upserts.
- Indexes on `name` and `year` optimize the most common query patterns.

---

## Installation & Usage

### Prerequisites

- Python 3.10+
- A TMDB API key (free at [themoviedb.org](https://developer.themoviedb.org/))

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd Pipeline-ETL-Cinema

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements/requirements.txt
```

### Configure API credentials

Create a `.env` file at the project root:

```env
CLE_API=your_tmdb_api_key
JETON=your_tmdb_bearer_token
```

> Only one of the two is required. The Bearer token (`JETON`) takes priority.

### Run the pipeline

Execute the scripts in order:

```bash
# 1. Extract data from TMDB API
python scripts/extract/extract.py

# 2. Transform the CSV dataset
python scripts/transform/transform.py

# 3. Transform the API JSON data
python scripts/transform/transformJson.py

# 4. Load everything into the SQLite database
python scripts/load/load.py
```

### Explore the data

```bash
# Open the notebook for interactive exploration
jupyter notebook notebooks/notebook.ipynb

# Or query the database directly
sqlite3 database/movies.db "SELECT genre, COUNT(*) as count FROM movies GROUP BY genre ORDER BY count DESC LIMIT 10;"
```

---

## Known Issues & Fixes

| Issue | Description | Resolution |
|-------|-------------|------------|
| CSV parsing error at line 7603 | `Expected 15 fields, saw 16` — caused by a comma inside a movie title | Handled programmatically by recombining extra fields into the `name` column |
| Malformed title quoting | "Code Geass: Lelouch of the Re;Surrection" had broken CSV quoting | Targeted fix applied in `transform.py` |
| TMDB incomplete data | API responses lack director, writer, star, country, budget, gross, company, runtime | Fields set to `Na`; could be enriched via additional API calls |
| CSV trailing semicolons | The original CSV uses semicolons at the end of each line in the `runtime` column | Cleaned during transformation |

---

## Requirements

```
requests
python-dotenv
pandas
```

---

## Team

Ynov B3 — ETL Pipeline & Orchestration project

---
