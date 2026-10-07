# Maze Runner with AI-Controlled Enemy

**REVA University — B25CS0311 Portfolio Building — Hackathon अभिनव (Abhinava)**
Problem Statement #15 · 07/10/2026

---

## Problem Statement

Build a maze game where the player navigates to an exit while an enemy character
chases them using a basic pathfinding algorithm (BFS or A\*).

## Approach

The maze is generated at runtime with a recursive-backtracker carver, then
"braided" to open some dead ends into loops so the player has escape routes.
Each enemy recomputes a route to the player's current cell on every step using
either BFS or A\*, and walks one cell along it. Both searches expose the cells
they expanded, which the game draws as a translucent overlay — so the AI's
reasoning is visible on screen rather than hidden.

From level 4 a **second enemy** joins running the *other* algorithm, so BFS and
A\* hunt the same player simultaneously and the difference in how much of the
maze each one searches is visible in a single frame.

## Tech Stack

| Component | Choice |
|---|---|
| Language | Python 3.10+ |
| Graphics / input | pygame-ce 2.5.8 |
| Algorithms | BFS, A\* (Manhattan heuristic), recursive-backtracker generation |
| Testing | Custom headless test suite (`test_pathfinding.py`) |

No external datasets, no network, no hardware.

## How to Run

```bash
pip install -r requirements.txt
python main.py
```

Run the tests (headless, no window opens):

```bash
python test_pathfinding.py
```

## Controls

| Key | Action |
|---|---|
| Arrow keys / WASD | Move |
| `SPACE` | Start / next level / retry |
| `TAB` | Switch enemy algorithms (BFS ↔ A\*) |
| `V` | Toggle search visualisation |
| `P` | Pause |
| `R` | Restart level |
| `M` | Back to menu |
| `ESC` | Quit |

Collect every coin to unlock the exit.

## Project Structure

```
maze-runner/
├── main.py              Game loop, rendering, input, state machine
├── pathfinding.py       BFS, A*, flood-fill distance maps
├── maze.py              Maze generation (incl. step-by-step carving)
├── entities.py          Player, Enemy and Coin
├── settings.py          All tunable constants
├── visualise_maze.py    Watch the maze being carved, step by step
├── benchmark.py         Measures BFS vs A*, writes assets/benchmark.png
├── autoplay.py          Headless bot playthroughs; finds crashes + bad balance
├── tools_screenshot.py  Generates the demo screenshots
├── test_pathfinding.py  Headless test suite (210 checks)
├── docs/                Per-member guides, code walkthrough, viva prep
└── assets/              Demo screenshots and the benchmark chart
```

**New to the codebase? Read [docs/CODE_WALKTHROUGH.md](docs/CODE_WALKTHROUGH.md)**
— every file explained in plain language, with the Python concepts you need.

## How the Enemy Works

Each time the enemy is due to move:

1. Run the selected search from the enemy's cell to the player's cell.
2. The search returns the route **and** the list of cells it expanded.
3. The enemy steps to the second cell in that route (the first is where it
   already stands).
4. The renderer draws the expanded cells in purple and the chosen route in red.

**BFS** uses a FIFO queue, so it finishes every cell at distance *d* before
touching distance *d+1*. The first time it reaches the goal, it got there by a
shortest route — guaranteed.

**A\*** scores each cell `f = g + h`, where `g` is steps taken so far and `h` is
the Manhattan distance left to the goal. Because the heuristic never
overestimates, A\* finds the same shortest path, but it leans toward the goal
instead of spreading evenly.

### Measured: does A\* actually help?

Produced by `benchmark.py`, averaged over **50 generated mazes** per row:

| Braid chance | BFS cells | A\* cells | A\* saving | BFS ms | A\* ms | Avg path |
|---|---|---|---|---|---|---|
| 0.00 | 183.5 | 163.9 | 10.7% | 0.141 | 0.216 | 130.2 |
| 0.12 | 188.0 | 160.8 | 14.5% | 0.145 | 0.212 | 108.5 |
| 0.35 | 214.1 | 157.9 | 26.2% | 0.169 | 0.219 | 87.5 |
| 0.50 | 236.1 | 176.0 | 25.5% | 0.212 | 0.279 | 81.2 |
| 0.80 | 256.3 | 171.9 | 33.0% | 0.250 | 0.302 | 65.5 |

**A\* expands fewer cells but takes more wall-clock time.** That is not a
contradiction: BFS uses a deque (O(1) per push/pop) while A\* uses a heap
(O(log n)) and computes a heuristic for every neighbour. At ~650 cells the
per-cell overhead outweighs the cells saved. On a much larger map, or where
visiting a cell is expensive, A\* wins decisively.

The interesting result is that **A\*'s advantage depends on how open the maze
is.** In a tight, perfect maze (braid 0.00) the corridors are so constrained
that there are barely any choices to make, and A\* saves only ~9%. As loops are
added the search has real alternatives, the Manhattan heuristic starts to
discriminate between them, and the saving climbs past 30%.

A single frame can look worse than the average: when the route winds heavily,
straight-line distance is a poor guide and A\* expands almost as much as BFS.
This is the honest limitation of the Manhattan heuristic in a twisty maze.

We ship with braid chance **0.35** — it keeps the A\* advantage visible *and*
gives the player escape routes, which makes the chase fairer.

## Design Decisions Worth Noting

**Enemy placement.** Spawning the enemy at the cell farthest from the player
puts it in the opposite corner — which is exactly where the exit is, so it
camps the goal and the level becomes unwinnable. We instead maximise the
*smaller* of (distance to player, distance to exit), using true walking
distances rather than Manhattan, so walls are respected.

**Braided maze.** A perfect maze is all dead ends, so the player gets cornered
with no counterplay. Opening ~35% of dead ends creates loops to escape through.

**Grid-aligned movement.** Entities move one whole cell at a time rather than by
pixels. Collision becomes an equality check, and the pathfinding result maps
directly onto movement with no interpolation.

**Time-based movement.** Move cooldowns are in milliseconds, not frames, so the
game plays identically regardless of frame rate.

## Testing

`test_pathfinding.py` runs 87 headless checks covering:

- Maze generation: solid border, walkable corners, seed reproducibility
- Connectivity: every floor cell reachable, across 20 generated mazes
- Path legality: correct endpoints, one-step moves, never crosses a wall
- A\* optimality: path length always equals BFS, expands no more cells
- Edge cases: start equals goal, unreachable goal returns empty rather than hanging
- Enemy spawn: never camping the exit, never on top of the player

## Screenshots

| | |
|---|---|
| `assets/demo_BFS.png` | BFS chase with search overlay |
| `assets/demo_Astar.png` | Same position under A\* |
| `assets/demo_win.png` | Win state |

## Future Scope

- Multiple enemies running different algorithms simultaneously
- Dijkstra with weighted terrain (mud slows movement) to show why uniform-cost
  search generalises BFS
- Enemy that predicts where the player is heading instead of chasing the
  current cell
- Fog of war limiting player vision radius
- Replay export of a chase for analysis

## Team

| Role | Member | Contribution |
|---|---|---|
| A — Core logic | *(name, roll no.)* | Pathfinding (BFS, A\*, distance maps) |
| B — Supporting logic | *(name, roll no.)* | Maze generation, entity movement |
| C — Interface / testing | *(name, roll no.)* | Rendering, HUD, search overlay, test suite |
| D — Docs / presentation | *(name, roll no.)* | README, slides, demo recording |
