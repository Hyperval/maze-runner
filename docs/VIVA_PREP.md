# Viva Preparation

**Problem Statement #15 — Maze Runner with AI-Controlled Enemy**

Worth protecting: **Problem Understanding & Explanation (4 pts)** directly, and
**Technical Implementation (6 pts)** indirectly — because an examiner who
suspects you can't explain your code marks the technical section down too.

---

## The three rules

1. **Never say "I don't know" and stop.** Say what you *do* know, then say what
   you'd check. "I didn't write that part, but it works by X — Rahul owns it and
   can give the detail" is a fine answer. Silence is not.
2. **Answer only what's asked.** Volunteering extra invites questions you
   haven't prepared for.
3. **If you don't understand the question, ask them to repeat it.** Guessing at
   a misheard question looks worse than asking.

---

## Tier 1 — Everyone must be able to answer these

### "What does your project do?"
> A maze game where the player has to reach the exit while an enemy chases them
> using pathfinding. The enemy recalculates the shortest route to the player on
> every step, using either BFS or A\*, and you can switch between them live and
> watch the difference.

Practise this until it's 15 seconds and automatic. It's the first question
every time.

### "What's the purple area on screen?"
> Those are the cells the search algorithm expanded while looking for the
> player. It makes the AI visible instead of invisible — you can see BFS spread
> out evenly in all directions, while A\* leans toward the player.

### "Why BFS? Why not something else?"
> On a grid where every move costs the same, BFS is guaranteed to find the
> shortest path, and it's simple enough that we could implement and verify it
> ourselves. We added A\* alongside it so we could compare.

### "What's your tech stack?"
> Python with pygame-ce for graphics and input. No external datasets, no
> network, no hardware — everything is generated at runtime.

### "What would you do differently with more time?"
Pick **one** and be specific. Good answers:
> An enemy that predicts where the player is heading instead of chasing where
> they currently are, so it can cut them off at a junction.

> Dijkstra with weighted terrain — mud cells costing more to cross — which
> would show why BFS is really just Dijkstra with all edge costs equal.

Bad answer: "add more levels and better graphics."

---

## Tier 2 — Algorithms (Member A leads, everyone should follow)

### "How does BFS guarantee the shortest path?"
> It uses a FIFO queue, so it finishes exploring everything at distance 1 before
> it touches anything at distance 2, and so on. The first time it reaches the
> goal, it must have got there by the fewest possible steps.

### "What is A\*, and how is it different?"
> A\* scores each cell as f = g + h. g is the steps actually taken to reach it,
> h is an estimate of the steps remaining — we use Manhattan distance. It always
> expands the lowest-f cell, so instead of spreading out evenly it leans toward
> the goal. It finds the same shortest path, but usually expands fewer cells.

### "Why must the heuristic never overestimate?"
> If it overestimates, A\* might skip the cell that's actually on the shortest
> path because it looks worse than it is, and you lose the optimality
> guarantee. Manhattan distance on a grid with no diagonal movement can never
> overestimate, because the real path is at least that long and usually longer.

### "Which is better, BFS or A\*?"
This is a trap. The honest answer scores better:
> It depends on the maze. We measured it across 20 generated mazes. In a tight
> maze with no loops, A\* only expanded about 9% fewer cells than BFS, because
> the corridors are so constrained there's barely any choice for the heuristic
> to discriminate between. Once we opened dead ends into loops, A\*'s advantage
> rose to about 30%. So A\* helps most when there are real alternative routes.

**Have the README table open on screen when you say this.** Measured evidence
is rare in a hackathon and examiners notice it.

### "What's the time complexity?"
> O(V + E) for BFS, where V is the number of cells and E the connections
> between them. On a grid each cell has at most 4 neighbours, so E is about 4V,
> which makes it O(number of cells). Our maze is 31×21, so roughly 650 cells —
> fast enough to recompute every single step.

### "Why recompute the path every step instead of once?"
> Because the player keeps moving. A path computed once would be chasing where
> the player *was*. It's cheap enough at this maze size to just recompute.

### "Why no diagonal movement?"
> The walls are drawn on the grid, so a diagonal move would let the enemy slip
> through the corner point where two walls meet. Restricting to four directions
> keeps the enemy physically inside the corridors.

---

## Tier 3 — Maze generation (Member B leads)

### "How do you generate the maze?"
> A recursive backtracker. Start at a cell, pick a random unvisited neighbour
> two cells away, knock out the wall between them, move there, repeat. When
> there's nowhere to go, back up the stack. It's depth-first search used to
> carve instead of to search.

### "Why two cells away?"
> So that walls always land on even coordinates and stay one cell thick. If we
> carved one cell at a time, the whole grid would dissolve into an open room.

### "What's braiding?"
> A plain generated maze is 'perfect' — exactly one route between any two
> cells, which means it's all dead ends. The player gets cornered with no way
> out and it isn't fun. We open about 35% of dead ends into loops so there are
> escape routes. It also made the BFS-vs-A\* difference bigger, because now
> there are genuinely alternative routes to choose between.

### "How did you pick the difficulty numbers?"
> We playtested. [Show the playtest table.] The key constraint is that the
> enemy's move delay has to stay above the player's, or it catches you with
> certainty and skill stops mattering.

---

## Tier 4 — Implementation (Member C leads)

### "Walk me through the game loop."
> Handle events, update game state, draw the frame, tick the clock to cap the
> frame rate. Standard pygame structure.

### "Why milliseconds instead of frame counts for movement?"
> So the game plays identically on a fast and a slow machine. If we counted
> frames, the enemy would be faster on a better laptop.

### "How do you detect collisions?"
> Everything moves one whole cell at a time on the grid, so a collision is just
> checking whether two things are on the same cell. No rectangle overlap maths
> needed.

### "How did you test it?"
> A headless test suite — 87 checks that run without opening a window. It
> verifies every cell in the maze is reachable, that paths never cross walls,
> that A\* always finds the same length path as BFS while expanding no more
> cells, and that the enemy never spawns on the exit.

---

## Tier 5 — The hard ones

### "Did you write this yourselves?"
Be honest and specific. Confidence comes from detail:
> We used AI assistance for the initial scaffolding, then each of us took
> ownership of a module. I rewrote the BFS implementation myself to make sure I
> understood it — [show `scratch_bfs.py`] — and I can walk you through any part
> of this file.

Then *actually do it* if asked. This is exactly why Member A's Part 1 exists.

### "What was the hardest bug?"
> The enemy spawning on the exit. We placed it at the cell farthest from the
> player, which is the opposite corner — exactly where the exit is. It camped
> the goal and the level was impossible. We fixed it by maximising the smaller
> of the distance to the player and the distance to the exit, using real
> walking distance instead of straight-line distance so walls are counted.

### "What's the weakest part of your project?"
Don't say "nothing." Pick something real and show you understand it:
> The Manhattan heuristic isn't great in a twisty maze — when the real route
> winds a lot, straight-line distance is a poor guide and A\* ends up expanding
> almost as much as BFS. A better heuristic would account for the maze
> structure, but computing one would cost more than it saves.

### "Can it handle a bigger maze?"
> Yes — the maze size is a constant in settings. BFS is linear in the number of
> cells, so a maze four times bigger takes about four times longer to search,
> which is still well under a frame. The real limit is the window size.

### "What happens if the enemy can't reach the player?"
> It can't happen in our mazes — the generator guarantees every cell is
> connected, and we test that across 20 generated mazes. But the code handles it
> anyway: the search returns an empty path and the enemy just doesn't move,
> rather than crashing.

---

## Demo script (3–4 minutes, rehearse it twice)

| Time | Do | Say |
|---|---|---|
| 0:00 | Title screen | "Problem statement 15 — maze game with a pathfinding enemy." |
| 0:20 | Start level 1, move around | "Player reaches the exit, enemy chases." |
| 0:45 | Press V to show overlay | "Purple is what the search explored, red is the route it chose." |
| 1:15 | Press TAB to A\* | "Same situation under A\* — notice fewer cells expanded, same path length." |
| 1:45 | Point at HUD counter | "That number is the cells expanded — it's the comparison, live." |
| 2:15 | Reach the exit, win | "Next level, the enemy gets faster." |
| 2:45 | Show the README table | "We measured this across 20 mazes — here's where A\* actually helps." |
| 3:15 | Close | "Future scope: a predictive enemy that cuts you off." |

**Rules for the demo**
- Play on a level you've practised. Don't improvise.
- If it crashes: *don't panic, don't apologise repeatedly.* Say "let me show you
  the recorded demo" and open the video. Having it ready is worth more than it
  never crashing.
- Whoever presents each section should be the person who owns that module.

---

## Final 10 minutes before the viva

- Game already running, on the title screen
- README open in a second window at the measured-comparison table
- Backup video open in a third window, ready to play
- Phone on silent
- Decide who answers first — one person leads, others add detail when asked
