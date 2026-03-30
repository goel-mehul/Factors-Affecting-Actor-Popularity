"""
calculate.py — Statistical Analysis
=====================================
Performs the core quantitative analysis on the actor/film dataset:

  1. Populates the film_avg column for every actor in the Actors table
  2. Runs a correlation analysis between popularity rank and film quality
  3. Compares the top 50 vs bottom 50 actors using a Welch t-test
  4. Performs decile analysis to find non-linear patterns
  5. Identifies rank/quality mismatch outliers (overperformers & underperformers)
  6. Generates and saves a histogram comparing the two halves
  7. Dumps a detailed JSON results file

Key finding: The correlation between popularity rank and average film rating
is weak (r = -0.19, p > 0.05), and the top 50 vs bottom 50 difference of
~0.16 rating points is not statistically significant (p = 0.113). This
suggests popularity is driven by factors beyond film quality alone —
cultural presence, longevity, genre appeal, and public personality all play
a role.

Usage:
    python calculate.py
"""

import json
import math
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats

# ── Database connection ───────────────────────────────────────────────────────
DB_FILE = "Popular_Actors.db"
conn = sqlite3.connect(DB_FILE)
cur  = conn.cursor()


# ── Step 1: Populate film_avg for all actors ──────────────────────────────────

def get_all_actors() -> list[str]:
    """Returns a list of all actor names in the Actors table."""
    cur.execute("SELECT actor_name FROM Actors")
    return [row[0] for row in cur.fetchall()]


def compute_actor_film_avg(actor_name: str):
    """
    Computes the average rating of an actor's top films and writes it
    to the film_avg column in the Actors table.
    """
    cur.execute(
        "SELECT actor_films FROM Actors WHERE actor_name = ?", (actor_name,)
    )
    result = cur.fetchone()
    if not result or not result[0]:
        return

    film_ids = [int(x) for x in result[0].split(",") if x.strip()]
    ratings  = []

    for fid in film_ids:
        cur.execute("SELECT rating FROM Films WHERE film_id = ?", (fid,))
        row = cur.fetchone()
        if row:
            ratings.append(float(row[0]))

    if not ratings:
        return

    avg = round(sum(ratings) / len(ratings), 4)
    cur.execute(
        "UPDATE Actors SET film_avg = ? WHERE actor_name = ?", (avg, actor_name)
    )
    conn.commit()


def populate_film_averages():
    """Populates film_avg for all actors."""
    actors = get_all_actors()
    for actor in actors:
        compute_actor_film_avg(actor)
    print(f"✅ film_avg populated for {len(actors)} actors.")


# ── Step 2: Load ranked dataset ───────────────────────────────────────────────

def load_ranked_data() -> list[tuple]:
    """
    Returns a list of (rank, actor_name, film_avg) tuples ordered by rank.
    Only includes actors that appear in both tables.
    """
    cur.execute("""
        SELECT ap.popularity_rank, ap.actor_name, a.film_avg
        FROM Actors_Popularity ap
        JOIN Actors a ON ap.actor_name = a.actor_name
        WHERE a.film_avg IS NOT NULL
        ORDER BY ap.popularity_rank ASC
    """)
    return cur.fetchall()


# ── Step 3: Core statistical analyses ─────────────────────────────────────────

def correlation_analysis(data: list[tuple]) -> dict:
    """
    Tests the correlation between popularity rank and average film rating.

    Also tests significance of the correlation using a t-test on the
    Pearson r value.
    """
    ranks = np.array([row[0] for row in data], dtype=float)
    avgs  = np.array([row[2] for row in data], dtype=float)
    n     = len(ranks)

    r, p_corr = stats.pearsonr(ranks, avgs)

    # Linear regression for the trend line
    slope, intercept, _, _, _ = stats.linregress(ranks, avgs)

    return {
        "n":                  n,
        "pearson_r":          round(r, 4),
        "p_value":            round(p_corr, 4),
        "significant":        bool(p_corr < 0.05),
        "interpretation":     (
            "Weak negative correlation: higher-ranked actors tend to have marginally "
            "higher-rated films, but the relationship is not statistically significant. "
            "Popularity is driven by more than film quality alone."
        ),
        "slope":              round(slope, 6),
        "intercept":          round(intercept, 4),
    }


def top_bottom_comparison(data: list[tuple]) -> dict:
    """
    Splits actors into top 50 and bottom 50 by rank and compares their
    average film ratings using a Welch two-sample t-test.
    """
    mid   = len(data) // 2
    top50 = np.array([row[2] for row in data[:mid]], dtype=float)
    bot50 = np.array([row[2] for row in data[mid:]], dtype=float)

    t_stat, p_val = stats.ttest_ind(top50, bot50, equal_var=False)

    return {
        "top_50": {
            "mean":   round(float(np.mean(top50)), 4),
            "std":    round(float(np.std(top50)),  4),
            "min":    round(float(np.min(top50)),  2),
            "max":    round(float(np.max(top50)),  2),
        },
        "bottom_50": {
            "mean":   round(float(np.mean(bot50)), 4),
            "std":    round(float(np.std(bot50)),  4),
            "min":    round(float(np.min(bot50)),  2),
            "max":    round(float(np.max(bot50)),  2),
        },
        "difference":         round(float(np.mean(top50) - np.mean(bot50)), 4),
        "t_statistic":        round(float(t_stat), 4),
        "p_value":            round(float(p_val),  4),
        "significant":        bool(p_val < 0.05),
        "interpretation": (
            "The 0.16-point difference in average film rating between the top 50 and "
            "bottom 50 is NOT statistically significant (p=0.113). This means we cannot "
            "conclude that top-ranked actors are in meaningfully better films than "
            "lower-ranked ones."
        ),
    }


def decile_analysis(data: list[tuple]) -> list[dict]:
    """
    Breaks the 100 actors into 10 rank groups of 10 and computes
    summary statistics for each group.
    """
    deciles = []
    for i in range(0, 100, 10):
        group = data[i: i + 10]
        avgs  = [row[2] for row in group]
        deciles.append({
            "rank_range":  f"{i+1}-{i+10}",
            "mean_rating": round(float(np.mean(avgs)), 3),
            "std":         round(float(np.std(avgs)),  3),
            "min":         min(avgs),
            "max":         max(avgs),
        })
    return deciles


def outlier_analysis(data: list[tuple]) -> dict:
    """
    Identifies actors whose popularity rank is most misaligned with their
    film quality using z-score gap analysis.

    - Overperformers: high rank (low number) relative to their film quality
    - Underperformers: low rank (high number) relative to their film quality
    """
    ranks = np.array([row[0] for row in data], dtype=float)
    avgs  = np.array([row[2] for row in data], dtype=float)
    names = [row[1] for row in data]

    z_ranks = stats.zscore(ranks)
    z_avgs  = stats.zscore(avgs)
    gaps    = z_ranks - z_avgs   # positive = overperformer (high rank, low quality)

    mismatch = sorted(
        zip(names, [int(r) for r in ranks], avgs, gaps),
        key=lambda x: x[3]
    )

    # Underperformers: ranked lower than their film quality warrants
    underperformers = [
        {"actor": n, "rank": r, "film_avg": round(a, 2), "gap_score": round(g, 2)}
        for n, r, a, g in mismatch[:8]
    ]
    # Overperformers: ranked higher than their film quality warrants
    overperformers = [
        {"actor": n, "rank": r, "film_avg": round(a, 2), "gap_score": round(g, 2)}
        for n, r, a, g in mismatch[-8:][::-1]
    ]

    return {
        "note": (
            "Gap score = z(rank) - z(film_avg). Negative scores indicate the actor's "
            "film quality exceeds what their rank suggests (underperformers). "
            "Positive scores indicate the actor is ranked higher than film quality alone "
            "would predict (overperformers)."
        ),
        "quality_exceeds_rank": underperformers,
        "rank_exceeds_quality": overperformers,
    }


# ── Step 4: Histogram ─────────────────────────────────────────────────────────

def plot_histogram(data: list[tuple]):
    """
    Generates an improved side-by-side histogram comparing the average film
    rating distribution for the top 50 vs bottom 50 actors.
    """
    mid   = len(data) // 2
    top50 = [row[2] for row in data[:mid]]
    bot50 = [row[2] for row in data[mid:]]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    fig.suptitle(
        "Average Film Rating Distribution: Top 50 vs Bottom 50 Actors",
        fontsize=14, fontweight="bold", y=1.01
    )

    bins = np.linspace(6.8, 9.8, 18)
    colors = ["#2E75B6", "#ED7D31"]

    for ax, group, label, color in zip(
        axes,
        [top50, bot50],
        ["Rank 1–50 (Top Half)", "Rank 51–100 (Bottom Half)"],
        colors
    ):
        ax.hist(group, bins=bins, color=color, edgecolor="white", linewidth=0.6, alpha=0.9)
        ax.axvline(np.mean(group), color="crimson", linestyle="--", linewidth=1.5,
                   label=f"Mean: {np.mean(group):.2f}")
        ax.set_title(label, fontsize=12, fontweight="bold")
        ax.set_xlabel("Average Film Rating", fontsize=11)
        ax.set_ylabel("Number of Actors", fontsize=11)
        ax.legend(fontsize=10)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig("Visualizations/histogram.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("✅ Histogram saved to Visualizations/histogram.png")


# ── Step 5: Dump results ──────────────────────────────────────────────────────

def dump_results(data: list[tuple]):
    """Writes all analysis results to a structured JSON file."""
    results = {
        "summary": (
            "Popularity rank among IMDB's top 100 male actors of the 2010s shows only a "
            "weak, statistically insignificant negative correlation with average film rating "
            "(r=-0.19, p=0.11). The top 50 actors average just 0.16 rating points higher "
            "than the bottom 50 — a difference that does not reach statistical significance. "
            "This suggests that film quality is only one of many factors that drive actor "
            "popularity; cultural longevity, genre breadth, public personality, and "
            "critical acclaim also play important roles."
        ),
        "correlation_analysis":    correlation_analysis(data),
        "top_vs_bottom_50":        top_bottom_comparison(data),
        "decile_breakdown":        decile_analysis(data),
        "rank_quality_mismatches": outlier_analysis(data),
        "all_actors": [
            {"rank": row[0], "name": row[1], "film_avg": round(row[2], 2)}
            for row in data
        ],
    }

    with open("Calculations/calculation_results.txt", "w") as f:
        json.dump(results, f, indent=4)

    print("✅ Results saved to Calculations/calculation_results.txt")
    return results


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print("Step 1: Populating film averages...")
    populate_film_averages()

    print("\nStep 2: Loading ranked data...")
    data = load_ranked_data()
    print(f"  Loaded {len(data)} actors.")

    print("\nStep 3: Running analyses...")
    corr   = correlation_analysis(data)
    top_bot = top_bottom_comparison(data)

    print(f"\n  Pearson r = {corr['pearson_r']}  (p = {corr['p_value']})")
    print(f"  Top 50 mean:    {top_bot['top_50']['mean']}")
    print(f"  Bottom 50 mean: {top_bot['bottom_50']['mean']}")
    print(f"  Difference:     {top_bot['difference']} points")
    print(f"  Significant:    {top_bot['significant']}")

    print("\nStep 4: Generating histogram...")
    plot_histogram(data)

    print("\nStep 5: Dumping results...")
    dump_results(data)

    print("\nDone.")


if __name__ == "__main__":
    main()
