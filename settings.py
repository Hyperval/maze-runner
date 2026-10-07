"""Central configuration for the maze game.

Keeping every tunable number in one file means the rest of the code reads as
logic rather than magic numbers, and lets us tune difficulty without hunting
through the game loop.

PYTHON NOTE: this file is just a list of variables. Other files say
`from settings import COLS` which copies the value in. Names in CAPITALS are
a convention meaning "constant" — Python doesn't enforce it, it's a signal to
other programmers not to change them while the game runs.
"""

# --- Maze dimensions (in cells) -------------------------------------------
# Must be ODD numbers. The recursive-backtracker carver treats even indices as
# wall rows/columns, so an even size would leave a ragged border.
COLS = 31
ROWS = 21

CELL_SIZE = 26          # pixels per cell
HUD_HEIGHT = 56         # space reserved at the top for score/status text

# The window never changes size, so it is built from the LARGEST maze we will
# ever generate (see MAX_COLS/MAX_ROWS below). Smaller mazes are centred in it.
MAX_COLS = 41
MAX_ROWS = 27

WIDTH = MAX_COLS * CELL_SIZE
HEIGHT = MAX_ROWS * CELL_SIZE + HUD_HEIGHT

FPS = 60

# --- Gameplay tuning -------------------------------------------------------
PLAYER_MOVE_DELAY = 90    # ms between player steps when a key is held
ENEMY_MOVE_DELAY = 190    # ms between enemy steps (higher = slower = easier)

# Every N enemy steps the enemy recomputes its path. Recomputing every single
# step is correct but wasteful; this also gives the player a small window to
# juke the enemy, which makes the chase feel fairer.
ENEMY_REPATH_INTERVAL = 1

# Difficulty progression: each level the enemy speeds up by this many ms,
# down to a floor so it never becomes impossible.
ENEMY_SPEEDUP_PER_LEVEL = 11

# IMPORTANT: this floor is deliberately kept ABOVE PLAYER_MOVE_DELAY (90).
# If the enemy's delay drops below the player's, the enemy is strictly faster
# and — because it always walks a shortest path — it catches you with
# certainty. Skill stops mattering. 100 keeps the hardest level winnable.
ENEMY_MIN_DELAY = 140

# Maze growth per level, in cells. Kept odd by stepping in 2s, and capped by
# MAX_COLS/MAX_ROWS so the maze can never outgrow the window.
MAZE_GROWTH_PER_LEVEL = 2

# Enemies stay frozen for this long at the start of each level. Without it the
# player is immediately under pressure with coins still scattered across the
# whole maze -- autoplay.py measured a <20% win rate for a perfect bot before
# this was added. A short grace period is what makes the level readable.
ENEMY_HEAD_START_MS = 2200

# A second enemy joins at this level, running a different algorithm so you can
# watch BFS and A* hunt the same player side by side.
SECOND_ENEMY_FROM_LEVEL = 4

# The second enemy moves this much slower than the first. Giving both the same
# speed doubled the threat overnight -- autoplay showed win rates falling from
# ~50% at level 3 to 7-20% from level 4 on, the exact level it joins. As a
# slower flanker it adds pressure without ending the run outright.
SECOND_ENEMY_DELAY_FACTOR = 1.65

# Set False to disable the second enemy entirely — a safety switch for the
# live demo. If anything misbehaves, flip this and the game still works.
SECOND_ENEMY_ENABLED = True

# --- Predictive enemy (Member B) -------------------------------------------
# A normal enemy paths to where the player IS, so it always trails. A
# predictive enemy paths to where the player is GOING, so it can cut them off.
# It joins at this level; set to 0 to disable it entirely.
PREDICTIVE_FROM_LEVEL = 6

# How far ahead along the player's route we are willing to aim, in cells.
# Longer lets the enemy commit to a deeper intercept, but a maze gives it more
# chances to be wrong, because the player can turn off at any junction.
PREDICT_LOOKAHEAD = 22

# The predictive enemy moves this much slower than a normal one. Interception
# is a real advantage, so it pays for it in speed - otherwise it is simply a
# better enemy rather than a different one.
PREDICTIVE_DELAY_FACTOR = 1.25

# --- Collectibles ----------------------------------------------------------
# Coins force the player to cross the maze instead of beelining for the exit,
# which makes the chase matter. The exit stays locked until all are collected.
COINS_ENABLED = True
COINS_BASE = 3                 # coins on level 1
COINS_PER_LEVEL = 0.5          # extra coins per level (rounded down)
COINS_MAX = 5

# Coins are chosen from a band of the distance-sorted cells rather than the
# farthest ones. Taking only the farthest put every coin in the opposite
# corner, so the player had to cross the entire maze for each one.
COIN_BAND_LO = 0.25            # skip the nearest 25% (too easy)
COIN_BAND_HI = 0.80            # skip the farthest 20% (too punishing)

# --- Maze generation -------------------------------------------------------
# Fraction of dead ends opened into loops. Measured across 20 mazes:
#   0.00 -> A* expands  9% fewer cells than BFS, avg path 124
#   0.35 -> A* expands ~29% fewer cells than BFS, avg path  ~80
# Loops give the player escape routes AND make the BFS/A* gap visible in the
# overlay, so this is tuned up from the generator's conservative default.
BRAID_CHANCE = 0.35

# --- Colours (R, G, B) -----------------------------------------------------
C_BG = (18, 18, 24)
C_WALL = (58, 62, 86)
C_FLOOR = (30, 32, 44)
C_PLAYER = (86, 204, 242)
C_ENEMY = (235, 87, 87)         # enemy 1 (BFS by default)
C_ENEMY_2 = (242, 153, 74)      # enemy 2 (A* by default)
C_ENEMY_P = (155, 89, 182)      # predictive enemy
C_PATH_P = (155, 89, 182, 90)   # its chosen path
C_VISITED_P = (155, 89, 182)    # cells its search expanded
C_AIM = (255, 214, 102)         # the cell it is aiming to intercept at
C_EXIT = (111, 207, 151)
C_EXIT_LOCKED = (90, 95, 120)   # exit before all coins are collected
C_COIN = (242, 201, 76)
C_PATH = (235, 87, 87, 90)      # enemy 1's chosen path (translucent)
C_PATH_2 = (242, 153, 74, 90)   # enemy 2's chosen path
C_VISITED = (124, 101, 214)     # cells enemy 1's search expanded
C_VISITED_2 = (214, 140, 101)   # cells enemy 2's search expanded
C_TEXT = (230, 230, 240)
C_TEXT_DIM = (140, 140, 160)
C_ACCENT = (86, 204, 242)
C_WIN = (111, 207, 151)
C_LOSE = (235, 87, 87)
