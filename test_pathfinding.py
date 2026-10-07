"""Tests for the maze and pathfinding logic.

Run with:  python test_pathfinding.py

These run headless (no game window), so they're safe to run on any machine
and quick enough to re-run after every change. Member C owns this file during
the testing block.
"""

import maze
from pathfinding import astar, bfs, flood_distances
from settings import COLS, ROWS

PASSED = 0
FAILED = []


def check(name, condition, detail=""):
    global PASSED
    if condition:
        PASSED += 1
        print(f"  PASS  {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL  {name}  {detail}")


def path_is_legal(grid, path, start, goal):
    """A path must start and end where asked, step one cell at a time, and
    never pass through a wall."""
    if not path:
        return False
    if path[0] != start or path[-1] != goal:
        return False
    for a, b in zip(path, path[1:]):
        if abs(a[0] - b[0]) + abs(a[1] - b[1]) != 1:
            return False
        if not maze.is_walkable(grid, b):
            return False
    return True


print("\nMaze generation")
for seed in range(10):
    grid = maze.generate(seed=seed)
    cells = maze.floor_cells(grid)
    check(f"seed {seed}: maze has floor cells", len(cells) > 50, f"got {len(cells)}")

grid = maze.generate(seed=0)
check("border is solid wall",
      all(grid[0][c] == maze.WALL for c in range(COLS))
      and all(grid[ROWS - 1][c] == maze.WALL for c in range(COLS)))
check("start corner is walkable", maze.is_walkable(grid, (1, 1)))
check("exit corner is walkable", maze.is_walkable(grid, (COLS - 2, ROWS - 2)))
check("same seed gives same maze", maze.generate(seed=3) == maze.generate(seed=3))
check("different seeds differ", maze.generate(seed=3) != maze.generate(seed=4))

print("\nConnectivity -- the enemy must always be able to reach the player")
for seed in range(20):
    grid = maze.generate(seed=seed)
    cells = maze.floor_cells(grid)
    reach = flood_distances(grid, cells[0])
    check(f"seed {seed}: every cell reachable",
          len(reach) == len(cells), f"{len(reach)}/{len(cells)}")

print("\nBFS and A* correctness")
for seed in range(10):
    grid = maze.generate(seed=seed)
    start, goal = (1, 1), (COLS - 2, ROWS - 2)
    pb, vb = bfs(grid, start, goal)
    pa, va = astar(grid, start, goal)

    check(f"seed {seed}: BFS path legal", path_is_legal(grid, pb, start, goal))
    check(f"seed {seed}: A* path legal", path_is_legal(grid, pa, start, goal))
    # The headline property: A* must match BFS's optimal length, while
    # expanding no more cells than BFS did.
    check(f"seed {seed}: A* path is optimal", len(pa) == len(pb),
          f"BFS {len(pb)} vs A* {len(pa)}")
    check(f"seed {seed}: A* expands <= BFS", len(va) <= len(vb),
          f"BFS {len(vb)} vs A* {len(va)}")

print("\nEdge cases")
grid = maze.generate(seed=1)
p, v = bfs(grid, (1, 1), (1, 1))
check("start == goal returns single-cell path", p == [(1, 1)])

# A walled-off cell must report 'no path' rather than crashing or looping.
sealed = [row[:] for row in maze.generate(seed=1)]
for r in range(ROWS):
    for c in range(COLS):
        sealed[r][c] = maze.WALL
sealed[1][1] = maze.FLOOR
sealed[5][5] = maze.FLOOR
p, _ = bfs(sealed, (1, 1), (5, 5))
check("unreachable goal returns empty path", p == [])

print("\nEnemy spawn placement")
import pygame  # noqa: E402  (imported late; only needed for this block)
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
from main import Game  # noqa: E402

game = Game()
for level in range(5):
    game.new_level()
    dp = flood_distances(game.grid, game.player_start)
    de = flood_distances(game.grid, game.exit_cell)
    e = game.enemy.cell
    # The bug this guards against: the enemy spawning on or beside the exit
    # and camping the goal, making the level unwinnable.
    check(f"level {level}: enemy not camping exit", de.get(e, 0) > 10,
          f"only {de.get(e, 0)} steps from exit")
    check(f"level {level}: enemy not on top of player", dp.get(e, 0) > 10,
          f"only {dp.get(e, 0)} steps from player")
pygame.quit()

print(f"\n{'=' * 46}")
print(f"{PASSED} passed, {len(FAILED)} failed")
if FAILED:
    for name in FAILED:
        print(f"  - {name}")
    raise SystemExit(1)
print("All tests passed.")
