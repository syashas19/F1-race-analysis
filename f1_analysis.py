"""F1 race results analysis.

Pulls real race results from the public Jolpica-F1 API (the Ergast successor),
caches them as CSV, then answers three questions with charts:
  1. How much does starting position decide who wins?
  2. Which drivers gain the most places from grid to flag?
  3. How have the top constructors scored across seasons?
"""
import argparse
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import requests

API = "https://api.jolpi.ca/ergast/f1"
DATA_DIR = Path("data")
CHART_DIR = Path("charts")


def fetch_season(season: int) -> list[dict]:
    """Download every race result row for one season (handles pagination)."""
    rows, offset, limit = [], 0, 100
    while True:
        resp = requests.get(f"{API}/{season}/results.json",
                            params={"limit": limit, "offset": offset}, timeout=30)
        resp.raise_for_status()
        mr = resp.json()["MRData"]
        for race in mr["RaceTable"]["Races"]:
            for res in race["Results"]:
                rows.append({
                    "season": int(race["season"]),
                    "round": int(race["round"]),
                    "race": race["raceName"],
                    "driver": f'{res["Driver"]["givenName"]} {res["Driver"]["familyName"]}',
                    "constructor": res["Constructor"]["name"],
                    "grid": int(res["grid"]),
                    "position": int(res["position"]),
                    "points": float(res["points"]),
                    "status": res["status"],
                })
        offset += limit
        if offset >= int(mr["total"]):
            return rows
        time.sleep(0.5)  # be polite to the free API


def load_data(start: int, end: int, refresh: bool = False) -> pd.DataFrame:
    DATA_DIR.mkdir(exist_ok=True)
    cache = DATA_DIR / f"results_{start}_{end}.csv"
    if cache.exists() and not refresh:
        return pd.read_csv(cache)
    rows = []
    for season in range(start, end + 1):
        print(f"Downloading {season}...")
        rows += fetch_season(season)
    df = pd.DataFrame(rows)
    df.to_csv(cache, index=False)
    return df


def win_rate_by_grid(df: pd.DataFrame) -> pd.Series:
    starts = df[df["grid"].between(1, 10)]
    return (starts["position"].eq(1).groupby(starts["grid"]).mean() * 100).round(1)


def places_gained(df: pd.DataFrame, min_races: int = 30) -> pd.Series:
    finished = df[(df["grid"] > 0) &
                  (df["status"].eq("Finished") | df["status"].str.startswith("+"))].copy()
    finished["gained"] = finished["grid"] - finished["position"]
    g = finished.groupby("driver")["gained"].agg(["mean", "count"])
    return g[g["count"] >= min_races]["mean"].sort_values(ascending=False).round(2)


def constructor_points(df: pd.DataFrame, top: int = 6) -> pd.DataFrame:
    pivot = df.pivot_table(index="season", columns="constructor",
                           values="points", aggfunc="sum", fill_value=0)
    best = pivot.sum().nlargest(top).index
    return pivot[best]


def save_charts(df: pd.DataFrame) -> None:
    CHART_DIR.mkdir(exist_ok=True)

    wr = win_rate_by_grid(df)
    ax = wr.plot(kind="bar", color="#e10600", figsize=(8, 4.5))
    ax.set(title="Win rate by starting position", xlabel="Grid position", ylabel="Win rate (%)")
    plt.xticks(rotation=0)
    plt.tight_layout(); plt.savefig(CHART_DIR / "win_rate_by_grid.png", dpi=150); plt.close()

    pg = places_gained(df)
    if pg.empty:
        print("Not enough races per driver for the places-gained chart; use a wider season range.")
    else:
        both = pd.concat([pg.head(10), pg.tail(10)]).drop_duplicates().sort_values()
        ax = both.plot(kind="barh", figsize=(8, 6),
                       color=["#2a9d8f" if v > 0 else "#e10600" for v in both])
        ax.set(title="Average places gained per race (grid to finish)", xlabel="Places gained")
        plt.tight_layout(); plt.savefig(CHART_DIR / "places_gained.png", dpi=150); plt.close()

    cp = constructor_points(df)
    ax = cp.plot(marker="o", figsize=(9, 5))
    ax.set(title="Points per season, top constructors", xlabel="Season", ylabel="Points")
    ax.set_xticks(cp.index)
    plt.tight_layout(); plt.savefig(CHART_DIR / "constructor_points.png", dpi=150); plt.close()


def main() -> None:
    p = argparse.ArgumentParser(description="Analyse F1 race results.")
    p.add_argument("--start", type=int, default=2018)
    p.add_argument("--end", type=int, default=2025)
    p.add_argument("--refresh", action="store_true", help="re-download instead of using the cache")
    a = p.parse_args()

    df = load_data(a.start, a.end, a.refresh)
    print(f"\n{len(df)} results across {df['race'].nunique()} race names, {a.start}-{a.end}\n")
    print("Win rate by grid position (%):")
    print(win_rate_by_grid(df).to_string(), "\n")
    pg = places_gained(df)
    print("Most places gained on average:\n", pg.head(5).to_string(), "\n")
    print("Most places lost on average:\n", pg.tail(5).to_string(), "\n")
    save_charts(df)
    print(f"Charts saved in {CHART_DIR}/")


if __name__ == "__main__":
    main()
