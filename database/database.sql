CREATE TABLE IF NOT EXISTS movies (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT NOT NULL,
	rating TEXT,
	genre TEXT,
	year INTEGER,
	released TEXT CHECK (
		released IS NULL
		OR (
			length(released) = 10
			AND substr(released, 5, 1) = '-'
			AND substr(released, 8, 1) = '-'
		)
	),
	score REAL,
	votes INTEGER,
	director TEXT,
	writer TEXT,
	star TEXT,
	country TEXT,
	budget INTEGER,
	gross INTEGER,
	company TEXT,
	runtime INTEGER,
	source TEXT NOT NULL CHECK (source IN ('csv', 'tmdb')),
	source_key TEXT NOT NULL,
	UNIQUE (source, source_key)
);

CREATE INDEX IF NOT EXISTS idx_movies_name ON movies (name);
CREATE INDEX IF NOT EXISTS idx_movies_year ON movies (year);
