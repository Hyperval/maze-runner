# Member D — Analysis Tooling, Documentation & Presentation

**You own two things: the measurement tools, and the submission itself.**

Your code is different from the others' — you're not building game features,
you're building the tools that *prove the game works and measure how well*.
That output goes straight into your own slides, so the two halves of your job
feed each other.

You also hold the hackathon's single most important insurance policy: **the
backup video.**

---

## Priority order — do them in this order

---

## 1. Backup demo video — FIRST, done by hour 8

Not at hour 11. The rubric explicitly asks for it, and if the live demo crashes
in front of the examiner, this video is the difference between 8/8 and 3/8 on
**Functionality**.

- Record with OBS (free), Xbox Game Bar (`Win+G`, built into Windows), or any
  screen recorder.
- 3–4 minutes. Show: title → start → chase with overlay on → TAB to switch
  algorithm → win → next level.
- Narrate it, or add captions. Don't rely on the room being quiet.
- Save as `assets/demo_video.mp4` **and** upload to Drive with a shareable link
  in the README. If the laptop dies, you still have the link.
- **Re-record at hour 10** if features changed. The old one stays your fallback
  until the new one exists.

Get this done and the rest of your day is calm.

---

## 2. CODE: `benchmark.py` — the BFS vs A\* measurement tool (~1.5 hours)

This is your main coding task. It's a **standalone script** — it imports the
game's modules but never modifies them, so you cannot possibly break the demo.
Safest code on the team to be writing.

### What it must do

1. Generate N mazes (N = 50 or so) with different seeds.
2. For each, run BFS and A\* from the player start to the exit.
3. Record: cells expanded by each, path length, time taken by each.
4. Print a summary table.
5. Save a bar chart to `assets/benchmark.png` using matplotlib (already
   installed).
6. Repeat the whole thing at several `braid_chance` values, so the chart shows
   how A\*'s advantage changes as the maze opens up.

### Starting points

Everything you need already exists:

```python
import maze
from pathfinding import bfs, astar
from settings import COLS, ROWS

grid = maze.generate(seed=0, braid_chance=0.35)
path, visited = bfs(grid, (1, 1), (COLS - 2, ROWS - 2))
# len(path)    = route length
# len(visited) = cells the search expanded   <-- this is the headline number
```

For timing, use `time.perf_counter()`, not `time.time()` — it's the
high-resolution one meant for measuring short durations.

```python
import time
start = time.perf_counter()
bfs(grid, s, g)
elapsed_ms = (time.perf_counter() - start) * 1000
```

### Hints for when you get stuck

- **Timings come out as 0.0** — a single search is too fast to measure. Run it
  100 times in a loop and divide, or use `timeit`.
- **Results jump around between runs** — you're using random seeds. Pass a
  fixed `seed=` to `maze.generate()` so your numbers are reproducible. Examiners
  like reproducible.
- **matplotlib opens a window and blocks** — you don't want that in a script.
  Call `matplotlib.use("Agg")` before importing pyplot, then `plt.savefig()`
  instead of `plt.show()`.
- **Chart is unreadable** — label the axes, add a legend, and set
  `plt.tight_layout()` before saving.

### Expected result

You should reproduce something close to the table already in the README:

| Braid chance | BFS expanded | A\* expanded | A\* saving |
|---|---|---|---|
| 0.00 | 167.6 | 152.2 | 9.2% |
| 0.35 | ~221 | ~161 | ~27% |
| 0.80 | 260.3 | 166.7 | 36.0% |

**If your numbers differ meaningfully, that's interesting, not a failure** —
find out why and say so. Different maze size, different start/goal, different
sample count all change it.

### Why this is worth doing
Most hackathon teams claim "A\* is faster." You will have a chart with measured
numbers across 50 mazes. That's the difference between an assertion and
evidence, and it carries **Technical Implementation (6)** and **Innovation (3)**.

---

## 3. CODE: `autoplay.py` — the robot tester (~45 min)

You're the team's second tester. Automate it.

### What it does
Runs the game headlessly with a bot playing it, hundreds of times, looking for
crashes and impossible levels — the bugs that would otherwise surface in front
of the examiner.

### Core idea

```python
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"   # no window opens
from main import Game, WON, LOST
```

Then loop: pick a move for the player, advance the enemy, check the state.

The simplest bot moves randomly. A better one follows the BFS path *to the
exit* — you already have `bfs()`, so the bot can use the same pathfinding the
enemy does, just aimed at the exit instead of the player.

### What to look for and report
- Any crash or exception — report immediately, with the seed that caused it
- Levels where the bot can *never* win, even playing optimally (the enemy is
  too fast — tell Member B)
- Levels that end instantly (enemy spawned too close — tell Member A)

### Hints
- `pygame.time.get_ticks()` moves in real time, so the cooldowns will throttle
  your bot to real speed. Pass your own increasing `now` value instead to run
  thousands of steps instantly.
- Wrap each run in `try/except` and record the seed on failure, so a crash
  gives you a reproducible case rather than just "it broke once."

### Why this matters
"We ran 500 automated playthroughs and found two levels that were unwinnable"
is a genuinely strong line in the viva.

---

## 4. Team Details Sheet

Required deliverable. Fill in the table at the bottom of `README.md`: team name,
every member's name and roll number, problem statement chosen (#15), and one
line of contribution each.

Also: **Annexure B (SEE Examination Evaluation sheet)** must be filled in *in
advance* by each member and signed before handing to the examiner. Chase your
teammates — it's the easiest thing to forget and it's mandatory.

---

## 5. Slide deck — 3 to 5 slides, no more

| Slide | Content |
|---|---|
| 1 | Problem statement #15, team name, members |
| 2 | Solution + screenshot of the game with the search overlay on |
| 3 | Tech stack and architecture — the modules and how they connect |
| 4 | **Challenges faced** (below) + **your benchmark chart** |
| 5 | Future scope (pull from the README) |

Slide 4 is your strongest, and it's built from your own output.

---

## 6. README accuracy check — hour 10

`README.md` is already detailed. Your job is keeping it **true** as features
change. If Member A adds a second enemy and the README doesn't mention it,
that's a mark lost on **Code Quality & Documentation (2)**.

Verify on a clean machine: does `pip install -r requirements.txt && python
main.py` actually work?

---

## Your strongest slide: Challenges Faced

Judges hear "integration was hard" from every team. Specific bugs with specific
fixes stand out. You already have three:

**1. The enemy camped the exit.**
We first spawned the enemy at the cell farthest from the player. That's the
opposite corner — exactly where the exit is. It sat on the goal and the level
was unwinnable. Fixed by maximising the *smaller* of (distance to player,
distance to exit), using true walking distance so walls count.

**2. A\* barely beat BFS.**
We expected A\* to expand far fewer cells; it saved only 9%. In a tight maze the
corridors are so constrained there's barely any choice for the heuristic to
discriminate between. Opening ~35% of dead ends into loops raised A\*'s saving
to ~30% *and* made the game fairer by giving the player escape routes.

**3. Straight-line distance was the wrong measure.**
Manhattan distance calls two cells "close" when a wall between them makes the
real walk 40 steps. We added a flood-fill measuring true walking distance and
used that for enemy placement.

Put your benchmark chart next to these. Real numbers beat claims.

---

## Stretch, only if everything above is done: collectibles

A small gameplay feature that's well within reach and visibly a *feature* to a
judge: place 3 coins on random floor cells; the exit stays locked until all 3
are collected.

- `maze.floor_cells(grid)` gives you every valid position — pick 3 at random,
  away from the player start.
- Collected when the player's cell equals a coin's cell — same equality check
  the enemy catch already uses.
- Draw them as small circles; draw the exit differently while locked.
- Gate the win condition on `len(self.coins) == 0`.

This forces the player to cross the maze instead of beelining to the exit,
which makes the chase matter much more.

---

## What you must be able to answer

- What did you measure, and what did you find?
- Why does A\*'s advantage depend on the maze being open?
- How many playthroughs did you automate, and what did they find?
- How do you know the game is winnable at every level?

---

## Hour 11.5 final checklist

- [ ] Code pushed to Git, repo accessible to the examiner
- [ ] `benchmark.py` runs and regenerates the chart
- [ ] `autoplay.py` runs clean
- [ ] README accurate, run instructions verified on a clean machine
- [ ] Slides done, exported to PDF (don't rely on PowerPoint opening)
- [ ] Backup video recorded **and** uploaded, link in README
- [ ] Screenshots in `assets/`
- [ ] Team details sheet filled
- [ ] Annexure B signed by all 4 members
- [ ] Everyone knows which part they're presenting
- [ ] Full demo rehearsed end to end, exactly as you'll present it
- [ ] Laptop charged, charger packed
