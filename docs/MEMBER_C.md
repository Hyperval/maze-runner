# Member C — Interface, Output & Testing

**You own what the judges actually see**, plus `test_pathfinding.py`.

The rubric gives **Presentation & Demo (2)** and part of **Functionality (8)** to
things in your lane. Also: you own "does this break when I do something weird",
which is what loses teams marks at the worst moment.

---

## Part 1 (~1 hour): Menu & game-state screens

Right now the game drops you straight into level 1, and the only way out is
ESC. Add a proper front end.

### What to build
1. **Title screen** — game name, "Press SPACE to start", controls list.
2. **Pause** — P key freezes everything and shows an overlay.
3. **Game over** — already exists as a banner; make it show best time per level.

### How
`main.py` already has a state machine: `PLAYING`, `WON`, `LOST` (see the
constants near the top, and `self.state`). You're adding `MENU` and `PAUSED`.

- In `update()`, return early unless `self.state == PLAYING` (it already does
  this — extend the idea).
- In `draw()`, branch: if `MENU`, call a new `draw_menu()` and skip the maze.
- In `handle_events()`, SPACE on `MENU` starts the game; P toggles `PAUSED`.

### Watch out
`self.start_time` is set in `new_level()` and `elapsed` is computed from
`pygame.time.get_ticks()`. If you pause, the clock keeps running and the timer
jumps. Fix: track accumulated paused time and subtract it.

---

## Part 2 (~45 min): Sound

Cheap points, big demo impact. `pygame.mixer` is already available.

```python
pygame.mixer.init()
step = pygame.mixer.Sound("assets/step.wav")
step.play()
```

Need: footstep, caught, win, and optionally a low pulse that gets faster as the
enemy closes in (use `len(self.enemy.path)` as the distance — it's already
computed).

Get free sounds from **freesound.org** or generate with **sfxr/jsfxr**
(bfxr.net — click "Pickup", download, done). Keep files in `assets/`.

**Guard every sound call** so a missing file can't crash the demo:

```python
try:
    pygame.mixer.init()
    SOUND_ON = True
except pygame.error:
    SOUND_ON = False
```

---

## Part 3 (~1 hour): Testing — your most important job

`test_pathfinding.py` has 87 checks. Run it after *every* change anyone makes:

```bash
python test_pathfinding.py
```

### Add tests for
- Player cannot walk through walls (call `try_move` into a wall, assert the
  cell didn't change)
- Move cooldown works (two moves in the same millisecond → only one happens)
- Win triggers when the player reaches the exit
- Loss triggers when the enemy reaches the player
- The game survives 200 random moves without crashing (fuzz test)

### The fuzz test is the highest-value one

```python
import random
game = Game()
for _ in range(200):
    d = random.choice([(0,-1),(1,0),(0,1),(-1,0)])
    game.player.try_move(game.grid, d, now)
    game.enemy.update(game.grid, game.player.cell, now)
```

This is how you find the crash that would otherwise happen *in front of the
examiner*.

### Breaking things on purpose
Try: holding two arrow keys at once, spamming R during the win banner, pressing
TAB repeatedly mid-chase, ALT-TABbing away and back, resizing the window.
Write down anything that misbehaves and tell the owner of that file.

---

## Part 4 (~30 min): Screenshots for submission

The deliverables list requires sample output. There's a working headless
screenshot script pattern — ask Akhil for `shot.py`, or capture live with a
screen grab. Need at least:

- BFS overlay mid-chase
- A\* overlay from the same position (the comparison shot)
- Win screen
- Lose screen

Save to `assets/`. Member D needs these for the slides, so get them done by
hour 8 — don't leave it to the end.

---

## What you must be able to answer

- How does the game loop work? (handle events → update state → draw → tick)
- What is the state machine and why use one?
- Why is movement timed in milliseconds instead of frames?
  (So the game plays the same on a fast and a slow machine.)
- What's the purple overlay showing? (Cells the search expanded.)
- How did you test it, and what bugs did you find?
