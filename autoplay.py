"""Run the game headlessly with a bot playing it, to hunt for bugs.

Run with:  python autoplay.py           (100 runs)
           python autoplay.py 500       (500 runs)

"Headless" means no window opens -- we tell SDL to use the "dummy" video
driver, so pygame renders to nothing. That lets hundreds of playthroughs
finish in seconds instead of hours.

The bot plays properly: it walks the shortest path to its current objective
(the nearest uncollected coin, or the exit once they're all gone) using the
same BFS the enemy uses. So a level the bot cannot win is a level a human
almost certainly cannot win either -- which is exactly the bug we want to find
before an examiner does.

What it reports:
    - crashes, with the level that caused them
    - levels the bot never escapes (too hard / unwinnable)
    - levels that end suspiciously fast (enemy spawned too close)
"""

import os
import sys
import traceback

# This MUST happen before pygame is imported, or SDL will try to open a window.
os.environ["SDL_VIDEODRIVER"] = "dummy"

import maze  # noqa: E402
from pathfinding import bfs  # noqa: E402
from settings import ENEMY_HEAD_START_MS  # noqa: E402

RUNS = 100
MAX_STEPS = 4000        # give up on a level after this many bot moves


def choose_target(game):
    """What the bot is heading for right now.

    Nearest uncollected coin first; once all coins are gone, the exit.
    """
    if game.coins:
        # Pick the coin with the shortest route from where we stand.
        best, best_len = None, None
        for coin in game.coins:
            path, _ = bfs(game.grid, game.player.cell, coin.cell)
            if path and (best_len is None or len(path) < best_len):
                best, best_len = coin.cell, len(path)
        if best is not None:
            return best
    return game.exit_cell


def danger_cells(game, radius=1):
    """Cells occupied by an enemy, plus everything within `radius` of one.

    A bot that ignores enemies walks straight into them, which would make the
    game look unwinnable when really the bot is just suicidal. A human dodges,
    so the bot must too, or the balance numbers are meaningless.
    """
    blocked = set()
    for enemy in game.enemies:
        ec, er = enemy.cell
        for dc in range(-radius, radius + 1):
            for dr in range(-radius, radius + 1):
                blocked.add((ec + dc, er + dr))
    return blocked


def step_direction(game, target):
    """The single (dcol, drow) step that moves us along the path to `target`.

    First we try to route AROUND the enemies by treating the cells near them
    as temporary walls. If no such route exists (we're cornered), we fall back
    to the direct path and take our chances -- which is also what a human does.
    """
    blocked = danger_cells(game)

    # Copy the grid and mark danger cells as walls. We copy row by row because
    # a plain `list(grid)` would share the inner row lists and corrupt the real
    # maze -- a classic Python mutable-aliasing bug.
    safe_grid = [row[:] for row in game.grid]
    for (c, r) in blocked:
        if 0 <= r < len(safe_grid) and 0 <= c < len(safe_grid[0]):
            if (c, r) != game.player.cell:
                safe_grid[r][c] = maze.WALL

    path, _ = bfs(safe_grid, game.player.cell, target)
    if len(path) < 2:
        # Cornered: no safe route. Use the direct one.
        path, _ = bfs(game.grid, game.player.cell, target)
    if len(path) < 2:
        return None

    (c0, r0), (c1, r1) = path[0], path[1]
    return (c1 - c0, r1 - r0)


def play_one(game, level):
    """Play a single level to completion. Returns (outcome, steps_taken).

    We drive our own clock instead of pygame's. The move cooldowns are
    measured in milliseconds, so if we used the real clock the bot would be
    throttled to human speed. Feeding in a fake `now` that jumps forward lets
    thousands of steps run instantly.
    """
    from main import LOST, WON

    game.level = level
    game.new_level()

    now = 0
    steps = 0

    while steps < MAX_STEPS:
        now += 100          # fake 100ms per tick, enough to clear any cooldown

        target = choose_target(game)
        direction = step_direction(game, target)
        if direction is None:
            return "stuck", steps

        game.player.try_move(game.grid, direction, now)
        game.coins = [c for c in game.coins if c.cell != game.player.cell]

        if game.player.cell == game.exit_cell and game.exit_unlocked:
            return "won", steps

        # Mirror the head start the real game gives the player, or the bot is
        # measured under harsher conditions than a human ever faces.
        if now >= ENEMY_HEAD_START_MS:
            for enemy in game.enemies:
                enemy.update(game.grid, game.player.cell, now)

        if any(e.caught(game.player.cell) for e in game.enemies):
            return "caught", steps

        steps += 1

    return "timeout", steps


def main():
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else RUNS

    from main import Game
    game = Game(start_in_menu=False)

    # Tally per level so we can see exactly where difficulty breaks down.
    stats = {}
    crashes = []

    for i in range(runs):
        level = (i % 10) + 1          # cycle levels 1..10
        try:
            outcome, steps = play_one(game, level)
        except Exception:
            crashes.append((level, traceback.format_exc()))
            continue

        row = stats.setdefault(level, {"won": 0, "caught": 0,
                                       "stuck": 0, "timeout": 0, "fast": 0})
        row[outcome] += 1
        # "fast" = lost within 15 steps, which usually means the enemy spawned
        # far too close to the player.
        if outcome == "caught" and steps < 15:
            row["fast"] += 1

    print()
    print(f"Autoplay: {runs} runs, bot plays the shortest route to each objective")
    print("=" * 70)
    print(f"{'level':>5} {'won':>5} {'caught':>7} {'stuck':>6} {'timeout':>8} "
          f"{'fast loss':>10} {'win rate':>9}")
    print("-" * 70)

    problems = []
    for level in sorted(stats):
        r = stats[level]
        total = r["won"] + r["caught"] + r["stuck"] + r["timeout"]
        rate = 100.0 * r["won"] / total if total else 0.0
        print(f"{level:>5} {r['won']:>5} {r['caught']:>7} {r['stuck']:>6} "
              f"{r['timeout']:>8} {r['fast']:>10} {rate:>8.0f}%")

        # The bot is a FLOOR, not a ceiling: it only dodges one cell ahead and
        # never plans a route that keeps the enemy at distance, so a human who
        # learns the level will beat these numbers. We therefore only flag a
        # level as broken when the bot essentially never escapes.
        if rate == 0:
            problems.append(f"level {level} is UNWINNABLE even for a pathfinding bot")
        elif rate < 15:
            problems.append(f"level {level} win rate only {rate:.0f}% -- likely too hard")
        if r["stuck"]:
            problems.append(f"level {level}: bot got stuck {r['stuck']}x (unreachable objective)")
        if r["fast"]:
            problems.append(f"level {level}: {r['fast']} losses within 15 steps (enemy spawns too close)")

    print("-" * 70)

    if crashes:
        print(f"\n{len(crashes)} CRASHES:")
        for level, tb in crashes[:3]:
            print(f"\n--- level {level} ---")
            print(tb)
    else:
        print("\nNo crashes.")

    if problems:
        print("\nISSUES FOUND:")
        for p in problems:
            print(f"  - {p}")
    else:
        print("All levels winnable, no balance problems detected.")


if __name__ == "__main__":
    main()
