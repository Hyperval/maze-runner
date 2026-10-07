"""Tests for the maze, pathfinding, and game logic.

Run with:  python test_pathfinding.py

These run headless (no game window opens), so they're safe on any machine and
quick enough to re-run after every change. Run them after ANY edit -- if the
count drops or a FAIL appears, something you just changed broke something else.

PYTHON NOTE: this is a hand-rolled test script rather than a framework like
pytest, so there's nothing extra to install. `check(name, condition)` records a
pass or a failure; at the end we print the tally and exit non-zero if anything
failed, which is what a CI system would look at.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")   # must precede pygame import

import maze
from pathfinding import astar, bfs, flood_distances
from settings import (
    COLS, ENEMY_HEAD_START_MS, ENEMY_MIN_DELAY, MAX_COLS, MAX_ROWS,
    PLAYER_MOVE_DELAY, ROWS, SECOND_ENEMY_FROM_LEVEL,
)

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

print("\nStep-by-step carving (the generation visualiser)")
steps = list(maze.carve_steps(seed=1))
check("carve_steps yields many intermediate grids", len(steps) > 50, f"got {len(steps)}")
final = maze.generate(seed=1, braid_chance=0.0)
check("carving ends at the same maze generate() produces", steps[-1] == final)

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

sealed = [[maze.WALL for _ in range(COLS)] for _ in range(ROWS)]
sealed[1][1] = maze.FLOOR
sealed[5][5] = maze.FLOOR
p, _ = bfs(sealed, (1, 1), (5, 5))
check("unreachable goal returns empty path", p == [])

print("\nMember A's from-scratch BFS (scratch_bfs.py)")
# Member A rebuilt BFS from memory to prove they can explain it under
# questioning. This keeps that implementation honest: it must agree with the
# reference implementation on every maze, or one of the two is wrong.
try:
    from scratch_bfs import my_bfs

    for seed in range(8):
        g = maze.generate(seed=seed)
        g_cols, g_rows = len(g[0]), len(g)
        s_cell, t_cell = (1, 1), (g_cols - 2, g_rows - 2)
        mine, _ = my_bfs(g, s_cell, t_cell)
        ref, _ = bfs(g, s_cell, t_cell)
        check(f"seed {seed}: scratch BFS finds the same shortest length",
              len(mine) == len(ref), f"{len(mine)} vs {len(ref)}")
        check(f"seed {seed}: scratch BFS path is legal",
              path_is_legal(g, mine, s_cell, t_cell))
except ImportError:
    print("  (scratch_bfs.py not present -- skipped)")

print("\nBalance invariants")
check("enemy is never faster than the player",
      ENEMY_MIN_DELAY > PLAYER_MOVE_DELAY,
      f"enemy floor {ENEMY_MIN_DELAY}ms vs player {PLAYER_MOVE_DELAY}ms")
check("players get a head start each level", ENEMY_HEAD_START_MS > 0)

print("\nGame setup")
import pygame  # noqa: E402
from main import LOST, MENU, PLAYING, WON, Game  # noqa: E402

game = Game()
check("game opens on the menu", game.state == MENU, f"got {game.state}")

for level in range(1, 11):
    game.level = level
    game.new_level()

    dp = flood_distances(game.grid, game.player_start)
    de = flood_distances(game.grid, game.exit_cell)

    check(f"L{level}: maze fits the window",
          game.cols <= MAX_COLS and game.rows <= MAX_ROWS,
          f"{game.cols}x{game.rows}")
    check(f"L{level}: maze dimensions are odd",
          game.cols % 2 == 1 and game.rows % 2 == 1)
    check(f"L{level}: maze is centred on screen",
          game.offset_x >= 0 and game.offset_y >= 0)

    for i, enemy in enumerate(game.enemies):
        # Guards the bug where the enemy spawned on the exit and camped it.
        check(f"L{level}: enemy {i} not camping the exit",
              de.get(enemy.cell, 0) > 8, f"{de.get(enemy.cell, 0)} steps away")
        check(f"L{level}: enemy {i} not on top of the player",
              dp.get(enemy.cell, 0) > 8, f"{dp.get(enemy.cell, 0)} steps away")

    check(f"L{level}: every coin is reachable",
          all(c.cell in dp for c in game.coins))
    check(f"L{level}: no coin sits on the exit",
          all(c.cell != game.exit_cell for c in game.coins))
    check(f"L{level}: exit starts locked when coins exist",
          game.exit_unlocked == (len(game.coins) == 0))

    expected = 2 if level >= SECOND_ENEMY_FROM_LEVEL else 1
    check(f"L{level}: has {expected} enemy/enemies",
          len(game.enemies) == expected, f"got {len(game.enemies)}")

    if len(game.enemies) == 2:
        check(f"L{level}: the two enemies use different algorithms",
              game.enemies[0].algorithm != game.enemies[1].algorithm)
        check(f"L{level}: the two enemies start apart",
              game.enemies[0].cell != game.enemies[1].cell)

print("\nPlayer movement")
game.level = 1
game.new_level()
start_cell = game.player.cell

# Walking into a wall must be refused.
walls = [d for d in ((0, -1), (-1, 0)) ]
for d in walls:
    target = (start_cell[0] + d[0], start_cell[1] + d[1])
    if not maze.is_walkable(game.grid, target):
        game.player.try_move(game.grid, d, 10_000)
        check(f"cannot walk through wall {d}", game.player.cell == start_cell)

# The move cooldown must throttle repeated moves at the same instant.
game.player.cell = start_cell
moved_first = game.player.try_move(game.grid, (1, 0), 50_000)
moved_again = game.player.try_move(game.grid, (1, 0), 50_000)
check("move cooldown blocks a second move in the same millisecond",
      not moved_again or not moved_first)

print("\nWin and loss conditions")
game.level = 1
game.new_level()
game.coins = []                       # simulate all coins collected
game.player.cell = game.exit_cell
game.update()
check("reaching the unlocked exit wins", game.state == WON, f"got {game.state}")

game.new_level()
if game.coins:
    game.player.cell = game.exit_cell
    game.update()
    check("exit does nothing while coins remain",
          game.state == PLAYING, f"got {game.state}")

game.new_level()
game.start_time -= ENEMY_HEAD_START_MS + 500      # expire the head start
game.player.cell = game.enemies[0].cell
game.update()
check("being caught loses", game.state == LOST, f"got {game.state}")

print("\nPause keeps the clock honest")
game.new_level()
game.toggle_pause()
check("P pauses", game.state == "paused", f"got {game.state}")
game.toggle_pause()
check("P resumes", game.state == PLAYING, f"got {game.state}")
check("paused time is recorded", game.paused_total >= 0)

print("\nFuzz: 300 random moves must not crash")
import random  # noqa: E402
random.seed(99)
game.new_level()
crashed = None
try:
    now = 0
    for _ in range(300):
        now += 100
        d = random.choice([(0, -1), (1, 0), (0, 1), (-1, 0)])
        game.player.try_move(game.grid, d, now)
        for e in game.enemies:
            e.update(game.grid, game.player.cell, now)
        game.draw()
except Exception as exc:          # noqa: BLE001 - we want any failure
    crashed = exc
check("300 random moves with rendering survive", crashed is None, str(crashed))

pygame.quit()

print(f"\n{'=' * 50}")
print(f"{PASSED} passed, {len(FAILED)} failed")
if FAILED:
    for name in FAILED:
        print(f"  - {name}")
    raise SystemExit(1)
print("All tests passed.")
