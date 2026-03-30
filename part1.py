"""
part1.py — Data Collection
==========================
Scrapes IMDB's top 100 most popular actors list and queries The Movie Database
(TMDB) API to build an actor profile database.

Run this script up to 4 times. Each run inserts 25 new rows into both the
Actors and Actors_Popularity tables. The database is fully populated after
the 4th run.

Usage:
    python part1.py

Environment:
    Set TMDB_API_KEY as an environment variable before running:
        export TMDB_API_KEY=your_key_here
"""

import os
import json
import sqlite3
import requests
from bs4 import BeautifulSoup

# ── Configuration ─────────────────────────────────────────────────────────────
IMDB_URL    = "https://www.imdb.com/list/ls022928819/"
TMDB_BASE   = "https://api.themoviedb.org/3/search/person"
DB_NAME     = "Popular_Actors.db"
BATCH_SIZE  = 25
MAX_ACTORS  = 100

API_KEY = os.environ.get("TMDB_API_KEY", "")
if not API_KEY:
    raise EnvironmentError(
        "TMDB_API_KEY is not set. "
        "Export it before running: export TMDB_API_KEY=your_key_here"
    )


# ── Database setup ────────────────────────────────────────────────────────────

def get_db_connection(db_name: str) -> tuple:
    """Connect to (or create) the SQLite database. Returns (cursor, connection)."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_name)
    conn = sqlite3.connect(path)
    cur  = conn.cursor()
    return cur, conn


# ── IMDB scraping ─────────────────────────────────────────────────────────────

def scrape_imdb_actors() -> list[tuple[str, str]]:
    """
    Scrapes the IMDB popular actors list.

    Returns:
        List of (rank_str, actor_name) tuples for the top 100 actors.
    """
    response = requests.get(IMDB_URL, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    name_tags = soup.find_all("h3", class_="lister-item-header")
    rank_tags = soup.find_all("span", class_="lister-item-index")

    actors = []
    for i in range(min(MAX_ACTORS, len(name_tags))):
        name = name_tags[i].find("a").text.strip()
        rank = rank_tags[i].text.strip()
        actors.append((rank, name))

    return actors


def create_actors_popularity_table(cur: sqlite3.Cursor, conn: sqlite3.Connection):
    """Creates the Actors_Popularity table if it doesn't already exist."""
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Actors_Popularity (
            popularity_rank INTEGER PRIMARY KEY,
            actor_name      TEXT NOT NULL
        )
    """)
    conn.commit()


def populate_actors_popularity_table(cur: sqlite3.Cursor, conn: sqlite3.Connection):
    """
    Inserts up to BATCH_SIZE rows into Actors_Popularity per run.
    Skips if the table already has MAX_ACTORS rows.
    """
    create_actors_popularity_table(cur, conn)
    cur.execute("SELECT COUNT(*) FROM Actors_Popularity")
    count = cur.fetchone()[0]

    if count >= MAX_ACTORS:
        print(f"Actors_Popularity already fully populated ({count} rows). Skipping.")
        return

    actors = scrape_imdb_actors()
    for rank, name in actors[count: count + BATCH_SIZE]:
        cur.execute(
            "INSERT OR IGNORE INTO Actors_Popularity (popularity_rank, actor_name) VALUES (?, ?)",
            (rank, name)
        )
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM Actors_Popularity")
    print(f"Actors_Popularity: {cur.fetchone()[0]} rows total.")


# ── TMDB API ──────────────────────────────────────────────────────────────────

def fetch_actor_from_tmdb(actor_name: str) -> dict | None:
    """
    Queries the TMDB search API for an actor by name.

    Returns:
        Dict with keys actor_id, actor_name, actor_films (empty string placeholder).
        Returns None if no result is found.
    """
    params = {"api_key": API_KEY, "query": actor_name}
    response = requests.get(TMDB_BASE, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    results = data.get("results", [])
    if not results:
        print(f"  WARNING: No TMDB result found for '{actor_name}'")
        return None

    top = results[0]
    return {
        "actor_id":    top["id"],
        "actor_name":  top["name"],
        "actor_films": "",   # populated later by populate_films.py
    }


def create_actors_table(cur: sqlite3.Cursor, conn: sqlite3.Connection):
    """Creates the Actors table if it doesn't already exist."""
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Actors (
            actor_id    INTEGER PRIMARY KEY,
            actor_name  TEXT NOT NULL,
            actor_films TEXT DEFAULT '',
            film_avg    REAL
        )
    """)
    conn.commit()


def populate_actors_table(cur: sqlite3.Cursor, conn: sqlite3.Connection):
    """
    Inserts up to BATCH_SIZE actor rows from TMDB into the Actors table per run.
    Skips if the table already has MAX_ACTORS rows.
    """
    create_actors_table(cur, conn)
    cur.execute("SELECT COUNT(*) FROM Actors")
    count = cur.fetchone()[0]

    if count >= MAX_ACTORS:
        print(f"Actors already fully populated ({count} rows). Skipping.")
        return

    actors = scrape_imdb_actors()
    for _, name in actors[count: count + BATCH_SIZE]:
        actor = fetch_actor_from_tmdb(name)
        if actor:
            cur.execute(
                "INSERT OR IGNORE INTO Actors (actor_id, actor_name, actor_films) VALUES (?, ?, ?)",
                (actor["actor_id"], actor["actor_name"], actor["actor_films"])
            )
            conn.commit()

    cur.execute("SELECT COUNT(*) FROM Actors")
    print(f"Actors: {cur.fetchone()[0]} rows total.")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    cur, conn = get_db_connection(DB_NAME)
    populate_actors_popularity_table(cur, conn)
    populate_actors_table(cur, conn)
    conn.close()
    print("Run complete. Run this script again if either table has fewer than 100 rows.")


if __name__ == "__main__":
    main()
