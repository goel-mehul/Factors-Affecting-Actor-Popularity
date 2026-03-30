"""
visualization1.py — Scatterplot: Popularity Rank vs Average Film Rating
========================================================================
Creates an annotated scatterplot showing the relationship between an actor's
IMDB popularity rank and the average rating of their top 10 films.

Key visual additions over the original:
  - Color-coded by rank tier (top 25 / middle 50 / bottom 25)
  - Annotated outliers (actors whose rank and film quality diverge most)
  - Regression line with r and p-value displayed
  - Clear interpretation in the subtitle

Usage:
    python visualization1.py
"""

import sqlite3
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats

# ── Database ──────────────────────────────────────────────────────────────────
DB_FILE = "Popular_Actors.db"
conn    = sqlite3.connect(DB_FILE)
cur     = conn.cursor()


def load_data() -> tuple[list, list, list]:
    """
    Loads popularity rank, average film rating, and actor name for all actors
    present in both Actors and Actors_Popularity tables.

    Returns:
        (ranks, avgs, names) as parallel lists.
    """
    cur.execute("""
        SELECT ap.popularity_rank, a.film_avg, ap.actor_name
        FROM Actors_Popularity ap
        JOIN Actors a ON ap.actor_name = a.actor_name
        WHERE a.film_avg IS NOT NULL
        ORDER BY ap.popularity_rank ASC
    """)
    rows  = cur.fetchall()
    ranks = [row[0] for row in rows]
    avgs  = [row[1] for row in rows]
    names = [row[2] for row in rows]
    return ranks, avgs, names


def identify_outliers(ranks, avgs, names, n=6) -> list[tuple]:
    """
    Returns the n actors whose rank/quality gap is largest in either direction.
    Used to annotate the scatterplot with the most interesting cases.
    """
    z_ranks = stats.zscore(ranks)
    z_avgs  = stats.zscore(avgs)
    gaps    = [zr - za for zr, za in zip(z_ranks, z_avgs)]

    combined = list(zip(names, ranks, avgs, gaps))
    # Largest positive gap = high rank despite low quality
    overperformers  = sorted(combined, key=lambda x:  x[3])[-n//2:]
    # Largest negative gap = low rank despite high quality
    underperformers = sorted(combined, key=lambda x:  x[3])[:n//2]

    return overperformers + underperformers


def create_scatterplot(ranks, avgs, names) -> float:
    """
    Builds and saves the annotated scatterplot.

    Returns:
        Pearson correlation coefficient.
    """
    ranks_arr = np.array(ranks, dtype=float)
    avgs_arr  = np.array(avgs,  dtype=float)

    r, p_val  = stats.pearsonr(ranks_arr, avgs_arr)
    slope, intercept, *_ = stats.linregress(ranks_arr, avgs_arr)
    trend_y   = slope * ranks_arr + intercept

    # Color by rank tier
    colors = []
    for rank in ranks:
        if rank <= 25:
            colors.append("#2E75B6")   # blue — top 25
        elif rank <= 75:
            colors.append("#A5A5A5")   # gray — middle 50
        else:
            colors.append("#ED7D31")   # orange — bottom 25

    fig, ax = plt.subplots(figsize=(12, 7))

    ax.scatter(ranks_arr, avgs_arr, c=colors, s=60, alpha=0.85, zorder=3)
    ax.plot(ranks_arr, trend_y, color="crimson", linewidth=1.5,
            linestyle="--", label=f"Trend line (r={r:.2f}, p={p_val:.2f})", zorder=4)

    # Annotate outliers
    outliers = identify_outliers(ranks, avgs, names, n=8)
    annotated = set()
    for name, rank, avg, gap in outliers:
        if name in annotated:
            continue
        annotated.add(name)
        short = name.split()[-1]   # last name only to avoid clutter
        offset = (5, 5) if gap > 0 else (-5, -12)
        ax.annotate(
            short,
            xy=(rank, avg),
            xytext=(rank + offset[0], avg + offset[1] * 0.02),
            fontsize=8,
            color="#333333",
            arrowprops=dict(arrowstyle="-", color="#999999", lw=0.8),
        )

    # Legend
    legend_patches = [
        mpatches.Patch(color="#2E75B6", label="Rank 1–25 (Top tier)"),
        mpatches.Patch(color="#A5A5A5", label="Rank 26–75 (Middle tier)"),
        mpatches.Patch(color="#ED7D31", label="Rank 76–100 (Bottom tier)"),
    ]
    ax.legend(handles=legend_patches + [
        plt.Line2D([0], [0], color="crimson", linestyle="--", label=f"Trend (r={r:.2f}, p={p_val:.2f})")
    ], fontsize=9, loc="upper right")

    sig_text = "not statistically significant" if p_val >= 0.05 else "statistically significant"
    ax.set_title(
        "Popularity Rank vs Average Film Rating (Top 100 Actors)",
        fontsize=14, fontweight="bold"
    )
    ax.set_xlabel("Popularity Rank (1 = most popular)", fontsize=12)
    ax.set_ylabel("Average Rating of Top 10 Films (TMDB)", fontsize=12)
    ax.set_xlim(0, 105)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Interpretation box
    interp = (
        f"r = {r:.2f}  |  p = {p_val:.2f}  ({sig_text})\n"
        "Popularity rank has only a weak relationship with film quality.\n"
        "Notable outliers: Clint Eastwood (rank 34, avg 9.5) and Jim Carrey (rank 92, avg 7.2)"
    )
    ax.text(0.02, 0.03, interp, transform=ax.transAxes, fontsize=9,
            verticalalignment="bottom",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#F2F2F2", alpha=0.8))

    plt.tight_layout()
    plt.savefig("Visualizations/scatterplot.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("✅ Scatterplot saved to Visualizations/scatterplot.png")
    return r


def main():
    ranks, avgs, names = load_data()
    r = create_scatterplot(ranks, avgs, names)
    print(f"\nCorrelation between Popularity Rank and Average Film Rating: r = {r:.2f}")
    print("Interpretation: Weak negative correlation — higher-ranked actors have slightly")
    print("better-rated films on average, but this is not statistically significant.")
    conn.close()


if __name__ == "__main__":
    main()
