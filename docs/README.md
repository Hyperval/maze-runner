# Team Docs

## Read these first

| File | Who | What it covers |
|---|---|---|
| **[CODE_WALKTHROUGH.md](CODE_WALKTHROUGH.md)** | **Everyone** | Every file explained in plain language, plus the Python you need. **Start here.** |
| **[VIVA_PREP.md](VIVA_PREP.md)** | **Everyone** | Expected examiner questions with answers, and the demo script |

## Per-member guides

All four members' features are **implemented and tested**. These guides remain
as the record of what each part does and the questions you'll be asked about
your section — plus stretch work if you want to extend it.

| File | Owner | Their part of the build |
|---|---|---|
| [MEMBER_A.md](MEMBER_A.md) | Core logic | Pathfinding (BFS, A\*, distance maps), second enemy |
| [MEMBER_B.md](MEMBER_B.md) | Maze & balance | Generation, braiding, step-by-step carving, difficulty curve |
| [MEMBER_C.md](MEMBER_C.md) | Interface & testing | Menu, pause, HUD, search overlay, 210-check test suite |
| [MEMBER_D.md](MEMBER_D.md) | Analysis & docs | `benchmark.py`, `autoplay.py`, README, slides, demo video |

## What's built

- Maze generation with braiding; mazes grow with level, capped to the window
- Player movement, coins that lock the exit, win/loss, level progression
- One enemy; a second joins at level 4 running the **other** algorithm
- Live `TAB` algorithm switching and a `V` search overlay showing expanded cells
- Menu, pause (with an honest timer), restart, best-time tracking
- `benchmark.py` — BFS vs A\* over 50 mazes, writes `assets/benchmark.png`
- `autoplay.py` — headless bot playthroughs that find crashes and bad balance
- `test_pathfinding.py` — 210 checks, all passing

## Still to do (people, not code)

- [ ] Record the backup demo video — **Member D, do this early**
- [ ] Slides (3–5)
- [ ] Team details sheet + Annexure B signed by all four
- [ ] Everyone reads CODE_WALKTHROUGH.md and VIVA_PREP.md

## Verify everything still works

```bash
python test_pathfinding.py    # 210 checks
python autoplay.py 500        # balance report
python benchmark.py           # regenerates the comparison chart
python main.py                # play it
```
