"""Measure BFS against A* across many generated mazes, and chart the result.

Run with:  python benchmark.py

This is a STANDALONE script. It imports the game's modules but never modifies
them, so running it cannot break the game or the demo.

It answers one question with evidence instead of assertion: does A* actually
expand fewer cells than BFS, and does that depend on the maze?

Outputs:
    - a summary table printed to the terminal
    - assets/benchmark.png, a two-panel chart for the slides

PYTHON NOTE: `if __name__ == "__main__":` at the bottom means the code only
runs when you execute this file directly. Everything above is just function
definitions, which do nothing until called.
"""

import time

import matplotlib
# Use the "Agg" backend BEFORE importing pyplot. Agg draws to a file instead of
# opening a window -- essential in a script, which would otherwise block
# waiting for you to close a plot window.
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import maze  # noqa: E402
from pathfinding import astar, bfs  # noqa: E402

# How many mazes to average over. More = steadier numbers, slower run.
SAMPLES = 50

# The maze openness values to test. 0.0 is a "perfect" maze (no loops at all);
# higher values open more dead ends into loops.
BRAID_VALUES = [0.0, 0.12, 0.35, 0.5, 0.8]

# Times a single search is repeated before timing it. One search is far too
# fast to measure reliably -- the clock's resolution is coarser than the work.
TIMING_REPEATS = 20


def time_search(search, grid, start, goal):
    """Return the average milliseconds for one call to `search`."""
    begin = time.perf_counter()        # perf_counter is the high-resolution clock
    for _ in range(TIMING_REPEATS):
        search(grid, start, goal)
    total = time.perf_counter() - begin
    return (total / TIMING_REPEATS) * 1000.0


def run_one(braid_chance, samples=SAMPLES):
    """Benchmark both algorithms across `samples` mazes at one braid level.

    Returns a dict of averages. Seeds are fixed (0, 1, 2, ...) so re-running
    the script gives identical numbers -- reproducibility matters when an
    examiner asks "how do you know?".
    """
    bfs_cells = astar_cells = 0
    bfs_ms = astar_ms = 0.0
    path_len = 0
    optimal_mismatches = 0

    for seed in range(samples):
        grid = maze.generate(seed=seed, braid_chance=braid_chance)
        cols, rows = len(grid[0]), len(grid)
        start, goal = (1, 1), (cols - 2, rows - 2)

        path_b, seen_b = bfs(grid, start, goal)
        path_a, seen_a = astar(grid, start, goal)

        # A* must find a path of the same length as BFS. If it ever doesn't,
        # the heuristic is broken -- worth catching here rather than in a viva.
        if len(path_a) != len(path_b):
            optimal_mismatches += 1

        bfs_cells += len(seen_b)
        astar_cells += len(seen_a)
        path_len += len(path_b)

        bfs_ms += time_search(bfs, grid, start, goal)
        astar_ms += time_search(astar, grid, start, goal)

    return {
        "braid": braid_chance,
        "bfs_cells": bfs_cells / samples,
        "astar_cells": astar_cells / samples,
        "bfs_ms": bfs_ms / samples,
        "astar_ms": astar_ms / samples,
        "path_len": path_len / samples,
        "saving": 100.0 * (1 - (astar_cells / bfs_cells)) if bfs_cells else 0.0,
        "mismatches": optimal_mismatches,
    }


def print_table(rows):
    print()
    print(f"BFS vs A*  --  averaged over {SAMPLES} mazes per row")
    print("=" * 78)
    print(f"{'braid':>6} {'BFS cells':>10} {'A* cells':>9} {'A* saves':>9} "
          f"{'BFS ms':>8} {'A* ms':>7} {'path':>6} {'bad':>4}")
    print("-" * 78)
    for r in rows:
        print(f"{r['braid']:>6.2f} {r['bfs_cells']:>10.1f} {r['astar_cells']:>9.1f} "
              f"{r['saving']:>8.1f}% {r['bfs_ms']:>8.3f} {r['astar_ms']:>7.3f} "
              f"{r['path_len']:>6.1f} {r['mismatches']:>4d}")
    print("-" * 78)
    print("'bad' counts mazes where A* failed to match BFS's shortest path.")
    print("It must be 0 -- any other number means the heuristic is broken.")
    print()


def make_chart(rows, path="assets/benchmark.png"):
    """Two panels: cells expanded, and A*'s percentage saving."""
    braids = [r["braid"] for r in rows]
    labels = [f"{b:.2f}" for b in braids]
    x = range(len(rows))
    width = 0.38

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    # Panel 1: grouped bars comparing cells expanded.
    ax1.bar([i - width / 2 for i in x], [r["bfs_cells"] for r in rows],
            width, label="BFS", color="#7c65d6")
    ax1.bar([i + width / 2 for i in x], [r["astar_cells"] for r in rows],
            width, label="A*", color="#d68c65")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(labels)
    ax1.set_xlabel("Braid chance (how open the maze is)")
    ax1.set_ylabel("Cells expanded (avg)")
    ax1.set_title("Search effort: BFS vs A*")
    ax1.legend()
    ax1.grid(axis="y", alpha=0.3)

    # Panel 2: the headline finding -- A*'s advantage grows with openness.
    ax2.plot(labels, [r["saving"] for r in rows],
             marker="o", color="#2d9d78", linewidth=2)
    ax2.set_xlabel("Braid chance (how open the maze is)")
    ax2.set_ylabel("Cells A* saves (%)")
    ax2.set_title("A* advantage vs maze openness")
    ax2.grid(alpha=0.3)
    ax2.set_ylim(bottom=0)

    plt.tight_layout()           # stops the labels from being clipped
    plt.savefig(path, dpi=130)
    print(f"Chart written to {path}")


def main():
    rows = []
    for braid in BRAID_VALUES:
        print(f"  running braid={braid:.2f} ...", flush=True)
        rows.append(run_one(braid))

    print_table(rows)
    make_chart(rows)

    best = max(rows, key=lambda r: r["saving"])
    worst = min(rows, key=lambda r: r["saving"])
    print("FINDING:")
    print(f"  A* saves the most at braid {best['braid']:.2f} ({best['saving']:.1f}%)")
    print(f"  and the least at braid {worst['braid']:.2f} ({worst['saving']:.1f}%).")
    print("  A tight maze constrains the corridors so much that there is")
    print("  barely any choice for the heuristic to discriminate between.")
    print("  Loops give the search real alternatives, so A* pulls ahead.")


if __name__ == "__main__":
    main()
