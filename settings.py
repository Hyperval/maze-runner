"""Central configuration for the maze game.

Keeping every tunable number in one file means the rest of the code reads as
logic rather than magic numbers, and lets us tune difficulty without hunting
through the game loop.
"""

# --- Maze dimensions (in cells) -------------------------------------------
# Must be ODD numbers. The recursive-backtracker carver treats even indices as
# wall rows/columns, so an even size would leave a ragged border.
COLS = 31
ROWS = 21

CELL_SIZE = 26          # pixels per cell
HUD_HEIGHT = 56         # space reserved at the top for score/status text

WIDTH = COLS * CELL_SIZE
HEIGHT = ROWS * CELL_SIZE + HUD_HEIGHT

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
ENEMY_SPEEDUP_PER_LEVEL = 18
ENEMY_MIN_DELAY = 85

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
C_ENEMY = (235, 87, 87)
C_EXIT = (111, 207, 151)
C_PATH = (235, 87, 87, 90)      # enemy's chosen path (translucent)
C_VISITED = (124, 101, 214)     # cells the search expanded
C_TEXT = (230, 230, 240)
C_TEXT_DIM = (140, 140, 160)
C_WIN = (111, 207, 151)
C_LOSE = (235, 87, 87)
