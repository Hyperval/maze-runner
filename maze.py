"""Maze generation and the grid data structure.

The maze is a 2D list, grid[row][col], where 1 is a wall and 0 is floor.

PYTHON NOTE: a "2D list" is a list of lists. grid[3] gives you row 3 (itself a
list), and grid[3][5] gives you the cell at column 5 of that row. Note the
order is [row][col], NOT [col][row] — mixing these up is the single most common
bug in grid code.

We generate it with a recursive backtracker (depth-first carving):
    1. Start at a cell, mark it as floor.
    2. Pick a random unvisited neighbour two cells away.
    3. Knock out the wall between them and move there.
    4. If there are no unvisited neighbours, back up and try again.

The result is a "perfect" maze -- exactly one route between any two cells,
no loops. That matters for us in two ways: the enemy can always reach the
player (so the chase never silently breaks), and the single-route property
makes the chase genuinely tense, because you can't circle around the enemy.

`braid()` then optionally knocks out a few extra walls to create loops, which
gives the player escape routes and makes higher levels playable.
"""

import random

from settings import BRAID_CHANCE, COLS, ROWS

WALL = 1
FLOOR = 0


def generate(cols=COLS, rows=ROWS, seed=None, braid_chance=BRAID_CHANCE):
    """Build and return a new maze grid.

    `seed` makes generation reproducible, which is what we use to re-run the
    exact same maze when demoing or debugging.
    `braid_chance` is the fraction of dead ends to open up into loops.

    PYTHON NOTE: `cols=COLS` means "if the caller doesn't pass cols, use COLS".
    So generate() and generate(cols=41) are both valid calls.
    """
    # carve_steps does the real work; we just want the final grid, so we run
    # the generator to completion and keep the last state.
    grid = None
    for grid in carve_steps(cols, rows, seed):
        pass

    if braid_chance > 0:
        braid(grid, random.Random(seed), braid_chance)

    return grid


def carve_steps(cols=COLS, rows=ROWS, seed=None):
    """Carve a maze, yielding the grid after every single carve step.

    This exists for the generation visualiser: drawing each yielded grid in
    turn shows the carver tunnelling through the maze and backtracking out of
    dead ends.

    PYTHON NOTE: a function containing `yield` is a *generator*. It doesn't run
    all at once — each `yield` hands a value back to whoever is looping over
    it, then pauses right there until the next loop iteration. That's how we
    can watch the maze being built one step at a time without storing every
    intermediate copy.
    """
    rng = random.Random(seed)

    # Start with everything solid; carving will open it up.
    grid = [[WALL for _ in range(cols)] for _ in range(rows)]

    # Carving happens on odd coordinates only, so walls always land on the
    # even ones and we get a clean one-cell-thick wall between corridors.
    start = (1, 1)
    grid[start[1]][start[0]] = FLOOR
    stack = [start]
    yield grid

    while stack:
        col, row = stack[-1]        # stack[-1] is the last item = "current cell"

        # Neighbours are two cells away -- one cell is the wall between us.
        candidates = []
        for dcol, drow in ((0, -2), (2, 0), (0, 2), (-2, 0)):
            ncol, nrow = col + dcol, row + drow
            if 1 <= ncol < cols - 1 and 1 <= nrow < rows - 1:
                if grid[nrow][ncol] == WALL:
                    candidates.append((ncol, nrow))

        if not candidates:
            stack.pop()                 # dead end, back up
            continue

        ncol, nrow = rng.choice(candidates)
        # Knock out the wall sitting between the current cell and the new one.
        grid[(row + nrow) // 2][(col + ncol) // 2] = FLOOR
        grid[nrow][ncol] = FLOOR
        stack.append((ncol, nrow))
        yield grid


def braid(grid, rng, chance):
    """Open some dead ends into loops.

    A perfect maze is all dead ends, which means the player gets cornered with
    no counterplay. Removing a wall next to some dead ends creates alternate
    routes so the chase stays winnable.
    """
    rows, cols = len(grid), len(grid[0])

    for row in range(1, rows - 1):
        for col in range(1, cols - 1):
            if grid[row][col] != FLOOR:
                continue

            open_sides = [
                (col + dc, row + dr)
                for dc, dr in ((0, -1), (1, 0), (0, 1), (-1, 0))
                if grid[row + dr][col + dc] == FLOOR
            ]

            # Exactly one open side means this cell is a dead end.
            if len(open_sides) == 1 and rng.random() < chance:
                walls = [
                    (col + dc, row + dr)
                    for dc, dr in ((0, -1), (1, 0), (0, 1), (-1, 0))
                    if 0 < col + dc < cols - 1
                    and 0 < row + dr < rows - 1
                    and grid[row + dr][col + dc] == WALL
                ]
                if walls:
                    wcol, wrow = rng.choice(walls)
                    grid[wrow][wcol] = FLOOR


def floor_cells(grid):
    """Every walkable cell, as a list of (col, row)."""
    return [
        (col, row)
        for row, line in enumerate(grid)
        for col, value in enumerate(line)
        if value == FLOOR
    ]


def is_walkable(grid, cell):
    """True if `cell` is inside the grid and not a wall."""
    col, row = cell
    if not (0 <= row < len(grid) and 0 <= col < len(grid[0])):
        return False
    return grid[row][col] == FLOOR
