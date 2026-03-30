"""
populate_films.py — Film Data Population
=========================================
Queries the TMDB API to retrieve the top 10 highest-rated films for each
actor in the Actors table, then populates the Films table and updates the
actor_films column with a comma-separated list of film IDs.

Run this script up to 4 times (25 actors processed per run).

Usage:
    python populate_films.py

Environment:
    export TMDB_API_KEY=your_key_here
"""

import os
import json
import sqlite3
import requests

# ── Configuration ─────────────────────────────────────────────────────────────
DB_NAME    = "Popular_Actors.db"
BATCH_SIZE = 25
MAX_FILMS  = 10

API_KEY  = os.environ.get("TMDB_API_KEY", "")
TMDB_BASE = (
    "https://api.themoviedb.org/3/discover/movie"
    "?language=en-US&sort_by=vote_average.desc"
    "&include_adult=false&include_video=false&page=1"
)

if not API_KEY:
    raise EnvironmentError(
        "TMDB_API_KEY is not set. "
        "Export it before running: export TMDB_API_KEY=your_key_here"
    )


# ── Database ──────────────────────────────────────────────────────────────────

def get_db_connection(db_name: str) -> tuple:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_name)
    conn = sqlite3.connect(path)
    cur  = conn.cursor()
    return cur, conn


def ensure_films_table(cur: sqlite3.Cursor, conn: sqlite3.Connection):
    """Creates the Films table if it doesn't already exist."""
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Films (
            film_id INTEGER PRIMARY KEY,
            name    TEXT NOT NULL,
            genres  TEXT,
            rating  REAL
        )
    """)
    conn.commit()


# ── TMDB API ──────────────────────────────────────────────────────────────────

def fetch_top_films_for_actor(actor_id: int) -> list[dict]:
    """
    Queries TMDB for the top-rated films featuring a given actor.

    Args:
        actor_id: TMDB actor ID.

    Returns:
        List of up to MAX_FILMS dicts with keys: film_id, name, genres, rating.
    """
    params = {
        "api_key":   API_KEY,
        "with_cast": actor_id,
    }
    # Add sort and filter params from base URL manually
    url = (
        f"https://api.themoviedb.org/3/discover/movie"
        f"?api_key={API_KEY}"
        f"&language=en-US&sort_by=vote_average.desc"
        f"&include_adult=false&include_video=false&page=1"
        f"&with_cast={actor_id}"
    )
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    films = []
    for item in data.get("results", [])[:MAX_FILMS]:
        genre_ids = [str(g) for g in item.get("genre_ids", [])]
        films.append({
            "film_id": item["id"],
            "name":    item["original_title"],
            "genres":  ",".join(genre_ids),
            "rating":  item["vote_average"],
        })
    return films


# ── Core logic ────────────────────────────────────────────────────────────────

def get_actors_without_films(cur: sqlite3.Cursor, batch_size: int) -> list[int]:
    """Returns up to batch_size actor IDs that haven't had films populated yet."""
    cur.execute(
        "SELECT actor_id FROM Actors WHERE actor_films IS NULL OR actor_films = '' LIMIT ?",
        (batch_size,)
    )
    return [row[0] for row in cur.fetchall()]


def insert_films(cur: sqlite3.Cursor, conn: sqlite3.Connection, films: list[dict]) -> list[str]:
    """
    Inserts films into the Films table (ignoring duplicates).

    Returns:
        List of film IDs as strings, for storing in actor_films.
    """
    film_ids = []
    for film in films:
        cur.execute(
            "INSERT OR IGNORE INTO Films (film_id, name, genres, rating) VALUES (?, ?, ?, ?)",
            (film["film_id"], film["name"], film["genres"], film["rating"])
        )
        film_ids.append(str(film["film_id"]))
    conn.commit()
    return film_ids


def process_batch(cur: sqlite3.Cursor, conn: sqlite3.Connection):
    """Processes one batch of actors and populates their film data."""
    actor_ids = get_actors_without_films(cur, BATCH_SIZE)
    if not actor_ids:
        print("All actors already have film data populated.")
        return

    for actor_id in actor_ids:
        films  = fetch_top_films_for_actor(actor_id)
        film_ids = insert_films(cur, conn, films)

        cur.execute(
            "UPDATE Actors SET actor_films = ? WHERE actor_id = ?",
            (",".join(film_ids), actor_id)
        )
        conn.commit()

        cur.execute("SELECT actor_name FROM Actors WHERE actor_id = ?", (actor_id,))
        name = cur.fetchone()[0]
        print(f"  Populated {len(film_ids)} films for {name}")

    cur.execute("SELECT COUNT(*) FROM Actors WHERE actor_films != ''")
    done = cur.fetchone()[0]
    print(f"\nActors with films populated: {done}/100")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    cur, conn = get_db_connection(DB_NAME)
    ensure_films_table(cur, conn)
    process_batch(cur, conn)
    conn.close()


if __name__ == "__main__":
    main()
