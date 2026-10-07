# Code Walkthrough

Read this before the viva. It explains every file in plain language, assuming
you know programming but not much Python. Work through it in order — each
section builds on the last.

**Total: about 1,100 lines across 8 files.** None of it is magic; by the end of
this document you should be able to point at any line and say what it does.

---

## The 30-second version

> The maze is a grid of 1s and 0s. The player and enemies each sit on one cell.
> Sixty times a second we read the keyboard, move everything one cell if its
> cooldown has expired, and redraw. The enemy decides where to move by running
> a search (BFS or A\*) from itself to the player and stepping onto the second
> cell of the route it finds.

Everything else is detail on top of that.

---

## Python things you need to know first

These five ideas cover ~90% of the syntax in this project.

**1. Indentation defines blocks.** There are no `{ }` braces. A line ending in
`:` starts a block, and everything indented under it belongs to that block.

```python
if x > 5:
    print("big")      # inside the if
print("always")       # outside it
```

**2. Lists and tuples.** A list `[1, 2, 3]` can be changed; a tuple `(1, 2)`
cannot. We use tuples for coordinates — `(col, row)` — because a position
shouldn't change in place, and because tuples can be dictionary keys.

**3. Dictionaries** map keys to values: `{"BFS": bfs_function}`. We use one to
look up an algorithm by name, which is how `TAB` swaps them at runtime.

**4. Classes bundle data with behaviour.** `class Enemy:` is a blueprint.
`Enemy(...)` makes one object from it. Inside the class, `self` means "this
particular object", so two enemies each have their own `self.cell`.

**5. List comprehensions** build a list in one line:

```python
[c for c in coins if c.cell != player.cell]
# means: a new list of every coin whose cell isn't the player's
```

We use this to drop a collected coin. Building a *new* list is safer than
deleting from the one you're looping over, which silently skips items.

---

## File 1: `settings.py` — all the numbers

Pure configuration. No logic. Every tunable value lives here so the rest of the
code reads as logic rather than mystery numbers.

Two constants matter more than the rest:

```python
PLAYER_MOVE_DELAY = 90    # ms between player steps
ENEMY_MIN_DELAY   = 140   # fastest the enemy can ever get
```

**`ENEMY_MIN_DELAY` must stay above `PLAYER_MOVE_DELAY`.** If the enemy's delay
drops below the player's, the enemy moves more often than you do, and since it
always walks a shortest path it catches you with mathematical certainty. Skill
stops mattering. We originally had 85 here and `autoplay.py` proved the late
levels were unwinnable.

**Viva question: "how did you choose these numbers?"**
> We measured them. `autoplay.py` plays the game automatically hundreds of
> times and reports the win rate per level. We tuned until levels 1–3 sat
> around 70–90% and later levels around 30–40%.

---

## File 2: `maze.py` — building the maze

The maze is a **list of lists**: `grid[row][col]`, where `1` is wall and `0` is
floor. Note the order — row first, then column. Getting this backwards is the
most common bug in grid code.

### The carving algorithm (recursive backtracker)

```
1. Start at cell (1,1), mark it floor.
2. Look at neighbours TWO cells away that are still solid.
3. Pick one at random. Knock out the wall BETWEEN them. Move there.
4. If there are no unvisited neighbours, pop the stack and back up.
5. Done when the stack is empty.
```

**Why two cells away?** So walls always land on even coordinates and stay one
cell thick. Carving one cell at a time would dissolve the grid into an open
room with no walls at all.

**Why must COLS and ROWS be odd?** The carver only ever stands on odd
coordinates. An even width would leave a ragged half-carved column at the edge.

### `carve_steps()` and the `yield` keyword

```python
def carve_steps(...):
    ...
    yield grid        # hand the grid back, then PAUSE here
```

A function containing `yield` is a **generator**. It doesn't run to completion —
each `yield` hands a value to whoever is looping over it and freezes right
there until the next iteration asks for more.

That's what lets the visualiser draw the maze being built one carve at a time
without storing hundreds of copies. `generate()` just runs the generator to the
end and keeps the final grid.

### Braiding

A freshly carved maze is **"perfect"**: exactly one route between any two cells,
which means it is nothing but dead ends. The player gets cornered with zero
counterplay.

`braid()` finds dead ends (cells with exactly one open side) and knocks out one
more wall with 35% probability, creating loops and therefore escape routes.

**This had a second effect we measured:** loops also widen A\*'s advantage over
BFS, from ~10% to ~26%, because the search finally has real alternatives to
discriminate between. See the benchmark table.

---

## File 3: `pathfinding.py` — the technical core

This is the file examiners will press hardest on. Three functions.

### `bfs(grid, start, goal)` — Breadth-First Search

```python
queue = deque([start])        # a FIFO queue: first in, first out
seen = {start}                # cells already queued, so we never revisit
came_from = {}                # cell -> the cell we arrived from

while queue:
    current = queue.popleft()        # take the OLDEST cell
    if current == goal: ...done
    for nxt in neighbours(current):
        if nxt not in seen:
            seen.add(nxt)
            came_from[nxt] = current
            queue.append(nxt)
```

**Why does this find the shortest path?** Because it's a FIFO queue, every cell
at distance 1 is processed before any cell at distance 2, which is processed
before any cell at distance 3. So the first time you touch the goal, you got
there in the fewest possible steps. That guarantee is a direct consequence of
the queue being first-in-first-out — swap it for a stack and you get DFS, which
finds *a* path, not the shortest.

**Mark cells as seen when you ENQUEUE them, not when you dequeue them.** Marking
on dequeue lets the same cell get queued several times before it's processed,
which wastes work and can loop forever.

**Reconstructing the path:** `came_from` is a trail of breadcrumbs. Start at the
goal, follow the links back to the start, then reverse the list.

### `astar(grid, start, goal)` — A\*

Same idea, but instead of a plain queue it uses a **priority queue** (a heap),
and always expands the cell with the lowest score:

```
f = g + h
g = steps actually taken to reach this cell
h = Manhattan distance remaining to the goal (|dx| + |dy|)
```

So A\* leans toward the goal instead of spreading out evenly in all directions.

**Why must `h` never overestimate?** If it did, A\* could skip the cell that's
actually on the shortest path because it looks worse than it really is, and you
lose the optimality guarantee. Manhattan distance on a 4-direction grid can
never overestimate, because the real walk is at least that long and usually
longer. A heuristic with this property is called **admissible**.

**The `counter` in the heap entries:** entries are `(f, counter, cell)`. If two
cells tie on `f`, Python compares the next item. Tuples of ints compare fine;
comparing the `cell` tuples would be arbitrary. The counter guarantees a tie is
broken before it ever reaches the cell.

### `flood_distances(grid, start)`

BFS with no goal — it just keeps expanding until it has measured the whole
reachable region, returning `{cell: distance}` for every cell.

We use it to place enemies and coins. **Why not just use Manhattan distance?**
Because Manhattan ignores walls: it will call two cells "adjacent" when a wall
between them makes the real walk 40 steps.

---

## File 4: `entities.py` — player, enemy, coin

### Why movement is timed in milliseconds

```python
if now - self._last_move < self.move_delay:
    return False        # cooldown still running, refuse the move
```

If we counted *frames* instead, the game would run faster on a better laptop.
Timing in milliseconds makes it behave identically everywhere.

### How the enemy actually moves

```python
self.recompute_path(grid, player_cell)    # search from me to the player
if len(self.path) >= 2:
    self.cell = self.path[1]              # step onto the SECOND cell
    self.path = self.path[1:]
```

**Why `path[1]` and not `path[0]`?** Because `path[0]` is the cell the enemy is
already standing on. The next step is index 1.

**Why recompute every step?** The player keeps moving. A path computed once
would be chasing where they *were*. At ~650 cells a search takes a fraction of a
millisecond, so recomputing is cheap.

Each `Enemy` object stores its own `algorithm`, so creating one with `"BFS"` and
another with `"A*"` makes them hunt independently — that's the whole two-enemy
feature, and it needed no new pathfinding code at all.

---

## File 5: `main.py` — the game itself

### The loop

```python
while True:
    self.handle_events()   # read keyboard/window events
    self.update()          # move everything, decide win/loss
    self.draw()            # paint the frame
    self.clock.tick(FPS)   # sleep so we run at 60fps, not 5000fps
```

Every real-time game is this loop. Everything else hangs off it.

### The state machine

```python
MENU, PLAYING, PAUSED, WON, LOST = "menu", "playing", "paused", "won", "lost"
```

`self.state` holds exactly one of these. `update()` returns immediately unless
the state is `PLAYING`, which is what makes pausing work — nothing moves,
but drawing continues, so the frozen frame stays on screen.

Using strings rather than numbers means debug output reads `"playing"` instead
of `2`.

### Enemy placement — the bug worth knowing

Our first version put the enemy on the cell farthest from the player. That's
the opposite corner — **which is exactly where the exit is**. The enemy sat on
the goal and camped it. Level unwinnable.

```python
def score(cell):
    return min(from_player[cell], from_exit[cell])
first_cell = max(cells, key=score)
```

Maximising the **smaller** of the two distances forces a spawn well away from
both. The second enemy additionally maximises distance from the first, or the
two walk in lockstep and the comparison is invisible.

### Keeping the pause clock honest

`pygame.time.get_ticks()` keeps counting while paused. If we ignored that, the
timer would jump forward the moment you resumed. So we record when the pause
began, add the duration to `paused_total`, and subtract it:

```python
self.elapsed = (now - self.start_time - self.paused_total) / 1000.0
```

### Why the window is a fixed size

`WIDTH`/`HEIGHT` are computed once from `MAX_COLS`/`MAX_ROWS`. Levels grow the
maze but it's capped at those maxima, and smaller mazes are centred using
`offset_x`/`offset_y`. If the maze could outgrow the window, it would be drawn
off-screen.

---

## File 6: `benchmark.py` — measuring BFS vs A\*

Standalone: it imports the game's modules but never modifies them, so it cannot
break the demo.

Two Python details worth knowing:

```python
matplotlib.use("Agg")     # BEFORE importing pyplot
```
"Agg" draws to a file instead of opening a window. Without it the script blocks
forever waiting for you to close a plot.

```python
begin = time.perf_counter()
for _ in range(20): search(...)      # repeat, because one run is too fast
```
`perf_counter` is the high-resolution clock. A single search is faster than the
clock's resolution, so we time 20 and divide.

### What it found

| Braid | BFS cells | A\* cells | A\* saves | BFS ms | A\* ms | Path |
|---|---|---|---|---|---|---|
| 0.00 | 183.5 | 163.9 | 10.7% | 0.141 | 0.216 | 130.2 |
| 0.12 | 188.0 | 160.8 | 14.5% | 0.145 | 0.212 | 108.5 |
| 0.35 | 214.1 | 157.9 | 26.2% | 0.169 | 0.219 | 87.5 |
| 0.50 | 236.1 | 176.0 | 25.5% | 0.212 | 0.279 | 81.2 |
| 0.80 | 256.3 | 171.9 | 33.0% | 0.250 | 0.302 | 65.5 |

**Two findings, and the second one is the interesting one.**

**1. A\*'s advantage depends on how open the maze is.** In a tight maze it saves
only ~11%, because the corridors are so constrained there's barely any choice
for the heuristic to discriminate between. Open it up with loops and the saving
climbs past 30%.

**2. A\* expands fewer cells but takes MORE wall-clock time.** 0.219ms vs
0.169ms at our settings. This looks like a contradiction and it is not:

- BFS uses a `deque`. Adding and removing is O(1) — a couple of pointer moves.
- A\* uses a **heap**. Every push and pop is O(log n), and it computes the
  Manhattan heuristic for every neighbour on top.

So A\* does *less* work in the sense of touching fewer cells, but *more* work
per cell. At 650 cells the per-cell overhead dominates. On a much larger map,
or where visiting a cell is expensive (reading from disk, querying a server),
A\* wins decisively.

**This is an excellent viva answer** — it shows you measured rather than
assumed, and that you understand the difference between an algorithm's
complexity and its real-world constant factors.

---

## File 7: `autoplay.py` — the robot tester

Runs the game headlessly with a bot playing it, hundreds of times, hunting for
crashes and unwinnable levels.

```python
os.environ["SDL_VIDEODRIVER"] = "dummy"   # BEFORE importing pygame
```
Tells SDL to render to nothing, so no window opens and runs finish in seconds.

The bot walks the shortest route to its objective (nearest coin, then the exit)
using the same BFS the enemy uses, and **routes around the enemies** by
treating the cells near them as temporary walls:

```python
safe_grid = [row[:] for row in game.grid]    # copy each row
```

**`row[:]` makes a copy of the row.** A plain `list(grid)` would copy the outer
list but share the inner row lists — so writing to `safe_grid` would corrupt
the real maze. This mutable-aliasing trap catches everyone once.

### What it found — the headline result

The first run reported **levels 3–10 unwinnable, 0% win rate**. Investigating
in stages:

1. The bot was ignoring enemies and walking straight into them. Added evasion →
   still only 0–20%. So the bot wasn't the whole story.
2. Coins were spawning in the farthest cells, so every coin meant crossing the
   entire maze under pursuit. Moved them to a middle distance band and added a
   2.2-second head start → levels 1–3 reached 47–73%.
3. Levels 4+ still collapsed — exactly where the second enemy joins. Slowing it
   by 1.45× helped only slightly, so that wasn't the root cause either.
4. **Real cause:** `ENEMY_MIN_DELAY` was 100ms against the player's 90ms — only
   1.1× faster than something that never rests and always takes the shortest
   route. Raising it to 140ms fixed the curve.

**Final: L1 73%, L2 93%, L3 80%, later levels 20–40%.**

The honest framing for the viva: the bot is a **floor, not a ceiling**. It only
dodges one cell ahead and never plans a route that keeps the enemy at distance,
so a human who learns a level will beat these numbers.

---

## File 8: `test_pathfinding.py` — 210 checks

Run after **every** change:

```bash
python test_pathfinding.py
```

The most valuable checks:

| Check | The bug it guards against |
|---|---|
| Every cell reachable, 20 mazes | A maze where the enemy can't reach you — chase silently breaks |
| A\* path length == BFS path length | A broken heuristic that finds a non-optimal route |
| A\* expands ≤ BFS | A heuristic that actively makes things worse |
| Enemy > 8 steps from exit | The exit-camping bug |
| `ENEMY_MIN_DELAY > PLAYER_MOVE_DELAY` | The enemy becoming strictly faster than you |
| 300 random moves + rendering | Any crash from an input nobody thought of |

The last one is a **fuzz test** — it does random things and only asserts "don't
crash". It finds the bug that would otherwise appear in front of the examiner.

---

## If you only memorise five things

1. **BFS uses a FIFO queue, so it finds the shortest path.** Everything at
   distance *d* is finished before anything at *d+1* is touched.
2. **A\* scores cells `f = g + h`**, where `h` is Manhattan distance and must
   never overestimate, or optimality is lost.
3. **A\* expanded ~26% fewer cells but ran slower in wall-clock time**, because
   its heap costs O(log n) per operation against the deque's O(1).
4. **The enemy spawn bug:** "farthest from the player" is the exit corner, so it
   camped the goal. Fixed by maximising `min(dist_to_player, dist_to_exit)`.
5. **We tuned difficulty by measurement, not feel** — `autoplay.py` ran hundreds
   of bot playthroughs and found the enemy was only 1.1× slower than the player.

---

## Suggested reading order

1. `settings.py` — 5 minutes, it's just numbers
2. `maze.py` → `generate()` and `braid()`
3. `pathfinding.py` → `bfs()` first, then `astar()`
4. `entities.py` → `Enemy.update()`
5. `main.py` → `run()`, then `update()`, then `new_level()`
6. The two tools last — they're independent of the game

Each person should be able to explain their own file **and** `pathfinding.py`,
because that's the one that gets asked about.
