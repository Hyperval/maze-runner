# Member B — Maze Generation & Difficulty Balance

**You own `maze.py` and the tuning in `settings.py`.**

Your work needs the least new code and has the most direct effect on whether
the game is *fun* — which is what the judges actually experience during the
demo. Take it seriously: a technically perfect game that's unplayable scores
badly on **Functionality (8)**.

---

## Part 1 (~45 min): Understand the generator, then prove you do

Read `maze.py`. The algorithm is a **recursive backtracker**:

1. Start at cell (1,1), mark it floor.
2. Look at neighbours **two cells away** that are still solid wall.
3. Pick one at random, knock out the wall *between* the two cells, move there.
4. No unvisited neighbours? Pop the stack and back up.
5. Stack empty means every cell has been visited.

**Why two cells away?** Carving at odd coordinates only means even coordinates
always stay as walls, giving clean one-cell-thick walls. Carving one cell at a
time would dissolve the whole grid into an open room.

### Prove you understand it
Add a `--watch` mode that draws the maze as it's being carved, one step at a
time. ~20 lines, looks great in the demo, and you can't write it without
understanding the stack. **This is your Innovation contribution.**

Hint: make `generate()` a generator function that `yield`s the grid after each
carve step, then have a small pygame loop draw each yielded frame.

---

## Part 2 (~1.5 hours): Difficulty curve

Right now every level is the same 31×21 maze with a slightly faster enemy.
That's thin. Your job is to make levels 1→5 feel like a real progression.

### What you can tune — all in `settings.py`

| Constant | Now | Effect |
|---|---|---|
| `COLS`, `ROWS` | 31, 21 | Maze size. **Must be odd numbers.** |
| `PLAYER_MOVE_DELAY` | 90 ms | Lower = player moves faster |
| `ENEMY_MOVE_DELAY` | 190 ms | Lower = enemy faster = harder |
| `ENEMY_SPEEDUP_PER_LEVEL` | 18 ms | How fast difficulty ramps |
| `ENEMY_MIN_DELAY` | 85 ms | Floor, so it never becomes impossible |
| `BRAID_CHANCE` | 0.35 | Fraction of dead ends opened into loops |

### The key relationship

If `ENEMY_MOVE_DELAY` drops below `PLAYER_MOVE_DELAY` (90), the enemy is
**faster than the player** and, because it always takes the shortest path, it
catches you with certainty. The game stops being winnable by skill.

`ENEMY_MIN_DELAY = 85` is below 90 — so at max level the enemy *is* faster.
**Decide if that's what you want.** Either raise the floor to ~100, or keep it
and give the player an escape mechanic. Your call, but make it deliberate and
be ready to explain it.

### Make maze size scale with level

In `main.py`'s `new_level()`, `maze.generate()` is called with no arguments.
Pass bigger dimensions as level rises:

```python
cols = min(41, COLS + (self.level - 1) * 2)   # keep it ODD
rows = min(27, ROWS + (self.level - 1) * 2)
```

Watch out: `WIDTH` and `HEIGHT` in `settings.py` are computed from `COLS`/`ROWS`
at import time. If the maze grows past the window, it gets cut off. Either cap
the growth (as above) or resize the window — capping is safer.

### Testing method

Play each level 3 times and record it:

| Level | Won? | Time | Felt |
|---|---|---|---|
| 1 | | | too easy / right / too hard |

Target: level 1 winnable first try, level 5 takes a few attempts. Put this table
in the slides — "we playtested and tuned" is exactly the kind of evidence that
earns **Problem Understanding (4)**.

---

## What you must be able to answer

- Why does the carver step two cells at a time?
- What is a "perfect" maze, and why did we deliberately break it with braiding?
  (Perfect = exactly one route between any two cells = all dead ends = player
  gets cornered with no counterplay.)
- Why must `COLS` and `ROWS` be odd?
- How did you choose the difficulty numbers? (Point at your playtest table.)
- What happens if the enemy is faster than the player?
