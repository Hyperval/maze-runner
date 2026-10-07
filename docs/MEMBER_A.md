# Member A — Core Logic / Pathfinding

**You own `pathfinding.py`.** This is the technical heart of the project and the
part judges will question hardest. Your job is split in two: *be able to explain
it*, then *extend it*.

---

## Part 1 (do this first, ~45 min): Rebuild BFS from memory

This is not busywork. In the viva, someone will point at the screen and ask
"how does the enemy decide where to go?" If you can rebuild BFS yourself, that
question is free marks. If you can't, we lose points on **Technical
Implementation (6)** and **Problem Understanding (4)**.

### Steps

1. Read `pathfinding.py`, specifically `bfs()`. Take your time.
2. Close it. Open a new file `scratch_bfs.py`.
3. Write BFS from scratch. You need:
   - a queue of cells still to explore (`collections.deque`)
   - a set of cells you've already seen, so you never revisit
   - a dict `came_from` mapping each cell to the cell you arrived from
4. Test it against the real one:

```python
import maze
from pathfinding import bfs
from scratch_bfs import my_bfs

g = maze.generate(seed=1)
mine, _ = my_bfs(g, (1, 1), (29, 19))
theirs, _ = bfs(g, (1, 1), (29, 19))
print(len(mine), len(theirs))   # must match
```

### If you get stuck

- **Infinite loop?** You're not marking cells as seen *when you add them to the
  queue*. Mark on enqueue, not on dequeue, or the same cell gets queued twice.
- **Path comes out backwards?** That's expected — you follow `came_from` from
  the goal back to the start, so reverse the list at the end.
- **KeyError in reconstruction?** The goal was never reached. Return `[]`.

### Checkpoint
You can explain, without notes: *why does BFS find the shortest path?*
(Answer: it's a FIFO queue, so every cell at distance 1 is finished before any
cell at distance 2 is touched. The first time you reach the goal, you got there
by the fewest steps possible.)

---

## Part 2 (~2 hours): Add a second enemy

Right now there's one enemy. Two enemies running **different** algorithms at
once is the single best Innovation feature (3 pts) — judges can watch BFS and
A\* hunt the same player simultaneously and see the difference live.

### Steps

1. In `main.py`, find `new_level()`. It creates `self.enemy = Enemy(...)`.
   Change it to a list: `self.enemies = [Enemy(...), Enemy(...)]`.
2. Give the second enemy `algorithm="A*"` and a different start cell. Reuse the
   existing `flood_distances` logic — pick the *second* best spawn, or just
   a cell far from both the first enemy and the player.
3. In `update()`, loop over `self.enemies` instead of touching one.
4. In `draw_entities()`, loop and draw each. Give them different colours —
   add `C_ENEMY_2` to `settings.py`.
5. The catch check becomes: caught if **any** enemy is on the player's cell.
6. In `draw_search()`, decide: draw both overlays (messy) or only the first
   enemy's (cleaner). Recommend a key to cycle which enemy's search is shown.

### Watch out for

- `draw_hud()` reads `self.enemy.algorithm` and
  `self.enemy.last_search_size`. Update it or it'll crash with
  `AttributeError`.
- `handle_events()` TAB handler also references `self.enemy`.
- `test_pathfinding.py` has an enemy-spawn block referencing `game.enemy`.
  Member C will need to update it — tell them when you change this.

### Make it safe
Keep the second enemy **behind a toggle** (a key, or a constant in
`settings.py`). If it misbehaves during the demo, you flip it off and still have
a working single-enemy game. Never let a new feature be able to break the demo.

### Checkpoint
Two enemies chase, each with its own colour, and the game still wins/loses
correctly. Run `python test_pathfinding.py` — it must still pass.

---

## Stretch (only if Part 2 is solid and tested)

Add **Dijkstra** with weighted terrain: mark some cells as "mud" costing 3 steps
instead of 1. This shows why BFS is just Dijkstra where every edge costs the
same — a genuinely strong point to make in the viva.

---

## What you must be able to answer

- How does BFS guarantee the shortest path?
- What is the heuristic in A\*, and why must it never overestimate?
- Why no diagonal movement? (It would let the enemy cut through wall corners.)
- Why recompute the path every step instead of once?
- What's the time complexity? (O(V+E); here V = cells, E ≈ 4V, so O(cells).)
