# Member D — Documentation, Presentation & Backup Demo

**You own the submission itself.** The other three can build something
excellent and still lose marks if the README is thin, the slides are late, or
the live demo fails with no backup.

You also have the hackathon's single most important insurance policy: **the
backup video.**

---

## Priority order (do them in this order)

### 1. Backup demo video — DO THIS FIRST, by hour 8

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
- **Re-record at hour 10** if features changed. The old one is still your
  fallback until the new one exists.

### 2. Team Details Sheet

Required deliverable. Fill in the table at the bottom of `README.md`:
team name, every member's name and roll number, the problem statement chosen
(#15), and one line of contribution each.

Also: **Annexure B (SEE Examination Evaluation sheet)** must be filled in
*in advance* by each member and signed before handing to the examiner. Chase
your teammates for these — it's the easiest thing to forget and it's mandatory.

### 3. Slide deck — 3 to 5 slides, no more

| Slide | Content |
|---|---|
| 1 | Problem statement #15, team name, members |
| 2 | Solution + screenshot of the game with the search overlay on |
| 3 | Tech stack and architecture — the 5 modules and how they connect |
| 4 | **Challenges faced** (see below — this is your strongest slide) |
| 5 | Future scope (pull from the README's list) |

### 4. README polish

`README.md` is already written and detailed. Your job: keep it **true** as
features change. If Member A adds a second enemy and the README doesn't mention
it, that's a mark lost on **Code Quality & Documentation (2)**.

Check at hour 10: does every feature listed actually exist? Does
`pip install -r requirements.txt && python main.py` work on a clean machine?

---

## Your strongest slide: Challenges Faced

Judges hear "it was hard to integrate" from every team. Specific, real bugs
with real fixes stand out. You already have three:

**1. The enemy camped the exit.**
We first spawned the enemy at the cell farthest from the player. That's the
opposite corner — which is exactly where the exit is. The enemy sat on the goal
and the level was unwinnable. Fixed by maximising the *smaller* of (distance to
player, distance to exit), using true walking distance rather than straight-line
distance so walls count.

**2. A\* barely beat BFS.**
We expected A\* to expand far fewer cells. It only saved 9%. The cause: in a
tight maze, corridors are so constrained there are barely any choices for the
heuristic to discriminate between. We opened ~35% of dead ends into loops,
which raised A\*'s saving to ~30% *and* made the game fairer by giving the
player escape routes.

**3. Straight-line distance was the wrong measure.**
Manhattan distance calls two cells "close" when a wall between them makes the
real walk 40 steps. We added a flood-fill that measures true walking distance
and used that for enemy placement.

Include the measured table from the README on this slide — real numbers beat
claims.

---

## Second tester

From hour 9, your other job is breaking the game. You didn't write it, which
makes you the best person to find what the authors assumed. Try the dumb
things: hold every key at once, spam restart, let the enemy catch you at the
exact moment you touch the exit, leave it running for 10 minutes.

Report what breaks. Don't fix it yourself — tell the owner.

---

## Hour 11.5 final checklist

- [ ] Code pushed to Git, repo accessible to the examiner
- [ ] README accurate, run instructions verified on a clean machine
- [ ] Slides done, exported to PDF (don't rely on PowerPoint opening)
- [ ] Backup video recorded **and** uploaded, link in README
- [ ] Screenshots in `assets/`
- [ ] Team details sheet filled
- [ ] Annexure B signed by all 4 members
- [ ] Everyone knows which part they're presenting
- [ ] Full demo rehearsed end to end, exactly as you'll present it
- [ ] Laptop charged, charger packed
