"""The player, the enemy, and collectible coins.

Everything moves on the grid one whole cell at a time rather than by pixels.
That keeps collision trivial (two things collide when they're on the same cell)
and means the enemy's pathfinding result maps directly onto its movement.

Movement is throttled by a millisecond delay rather than by frame count, so
the game plays identically regardless of frame rate.

PYTHON NOTE: `class` defines a blueprint; `Player(...)` builds one object from
it. `__init__` runs once when the object is created and sets up its starting
values. `self` is that specific object — `self.cell` means "this player's cell",
so two Enemy objects each keep their own separate position and path.
"""

from maze import is_walkable
from pathfinding import ALGORITHMS


class Player:
    """Grid-aligned player controlled by the arrow keys / WASD."""

    def __init__(self, cell, move_delay):
        self.cell = cell
        self.move_delay = move_delay
        self._last_move = 0
        self.steps = 0

    def try_move(self, grid, direction, now):
        """Attempt one step in `direction`, a (dcol, drow) tuple.

        Returns True if the player actually moved. Movement is refused while
        the move cooldown is still running, or if the target cell is a wall.

        PYTHON NOTE: the leading underscore in `_last_move` is a convention
        meaning "internal, don't touch from outside this class".
        """
        if direction == (0, 0):
            return False
        if now - self._last_move < self.move_delay:
            return False

        target = (self.cell[0] + direction[0], self.cell[1] + direction[1])
        if not is_walkable(grid, target):
            return False

        self.cell = target
        self._last_move = now
        self.steps += 1
        return True


class Enemy:
    """Chases the player using whichever search algorithm is selected.

    The enemy keeps its last computed path and the cells its search expanded,
    so the renderer can draw both. Recomputing on a fixed interval (rather than
    every frame) keeps the cost predictable and is plenty responsive at this
    maze size.

    Each Enemy is independent: giving one algorithm="BFS" and another
    algorithm="A*" lets both hunt the same player simultaneously, which is
    exactly the side-by-side comparison we want to demo.
    """

    def __init__(self, cell, move_delay, algorithm="BFS", repath_interval=1,
                 colour=None, path_colour=None, visited_colour=None):
        self.cell = cell
        self.move_delay = move_delay
        self.algorithm = algorithm
        self.repath_interval = repath_interval

        # Each enemy carries its own colours so the renderer stays simple —
        # it just asks the enemy what colour to draw it.
        self.colour = colour
        self.path_colour = path_colour
        self.visited_colour = visited_colour

        self._last_move = 0
        self._steps_since_repath = repath_interval   # force a path on step one
        self.path = []
        self.visited = []
        self.last_search_size = 0        # cells expanded, shown in the HUD

    def recompute_path(self, grid, target_cell):
        """Run the selected search from the enemy to the player."""
        search = ALGORITHMS[self.algorithm]
        self.path, self.visited = search(grid, self.cell, target_cell)
        self.last_search_size = len(self.visited)
        self._steps_since_repath = 0

    def update(self, grid, target_cell, now):
        """Advance the enemy at most one cell. Returns True if it moved."""
        if now - self._last_move < self.move_delay:
            return False

        if self._steps_since_repath >= self.repath_interval:
            self.recompute_path(grid, target_cell)

        # path[0] is the cell we're standing on, so the next step is path[1].
        if len(self.path) >= 2:
            self.cell = self.path[1]
            self.path = self.path[1:]
            self._steps_since_repath += 1
            self._last_move = now
            return True

        # No route (shouldn't happen in a connected maze, but don't crash).
        return False

    def caught(self, player_cell):
        return self.cell == player_cell


class Coin:
    """A pickup the player must collect before the exit unlocks.

    Deliberately tiny — it only needs to know where it is. Collection is just
    an equality check against the player's cell, the same test the enemy uses
    for catching the player.
    """

    def __init__(self, cell):
        self.cell = cell
