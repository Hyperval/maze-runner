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
        # The direction of the last successful move. The predictive enemy reads
        # this to work out where we are heading; (0, 0) means standing still.
        self.heading = (0, 0)

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
        self.heading = direction
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

        # No route, or we are already standing on the target. Force a replan on
        # the next tick, otherwise the repath counter stays at zero, we never
        # recompute, and the enemy is frozen for the rest of the level.
        self._steps_since_repath = self.repath_interval
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


class PredictiveEnemy(Enemy):
    """An enemy that intercepts instead of trailing.

    A normal Enemy paths to the cell the player is standing on. By the time it
    gets there the player has moved, so it is permanently one step behind and
    can only win by being faster. This one asks a different question:

        "Where will the player BE, and can I get there first?"

    It works in two stages.

    STAGE 1 - predict the player's route.
        Walk forward from the player's cell in the direction they are moving.
        Keep going while the way ahead is open. When it is blocked, look at the
        other exits:
          - exactly one way on (a corridor bend) -> follow it, the player has
            no other option either
          - two or more (a junction)             -> STOP. We genuinely cannot
            know which way they will turn, and guessing is worse than not
            guessing.
        That gives a list of cells the player is likely to walk through, in
        order, and it is honest about where its knowledge runs out.

    STAGE 2 - find the first cell we can reach before they do.
        The player reaches route[i] after roughly i * player_delay milliseconds.
        We reach it after (our distance) * our_delay milliseconds. Walking the
        route from the far end backwards, we take the DEEPEST cell where we
        arrive no later than the player. Deepest, not nearest, because a deeper
        cut-off is further ahead of them and harder to escape.

        No cell qualifies? Then interception is not on, and we fall back to
        chasing the player's current cell like a normal enemy.

    Cost: one extra flood fill per repath, which is the same O(cells) as the
    search we already run, so it roughly doubles this enemy's thinking cost.
    """

    def __init__(self, *args, lookahead=14, player_delay=90, **kwargs):
        super().__init__(*args, **kwargs)
        self.lookahead = lookahead
        self.player_delay = player_delay

        # Exposed so the renderer and the HUD can show what it is doing.
        self.predicted_route = []
        self.aim_cell = None
        self.intercepting = False
        self.planning_cells = 0      # cells touched by the intercept flood fill

    def predict_route(self, grid, player_cell, heading):
        """The cells we think the player is about to walk through, in order."""
        if heading == (0, 0):
            return [player_cell]          # standing still - nothing to predict

        route = [player_cell]
        cell, direction = player_cell, heading

        for _ in range(self.lookahead):
            ahead = (cell[0] + direction[0], cell[1] + direction[1])

            if is_walkable(grid, ahead):
                cell = ahead
                route.append(cell)
                continue

            # Blocked. Where else could they go, other than back the way they came?
            backwards = (-direction[0], -direction[1])
            options = []
            for d in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                if d == backwards:
                    continue
                nxt = (cell[0] + d[0], cell[1] + d[1])
                if is_walkable(grid, nxt):
                    options.append((d, nxt))

            if len(options) == 1:
                direction, cell = options[0]      # forced bend, follow it
                route.append(cell)
            else:
                break        # junction or dead end - stop guessing

        return route

    def choose_target(self, grid, player_cell, heading):
        """Pick the cell to path to: an intercept point, or the player."""
        from pathfinding import flood_distances

        self.predicted_route = self.predict_route(grid, player_cell, heading)
        self.intercepting = False
        self.planning_cells = 0

        if len(self.predicted_route) > 1:
            # One flood fill gives our true walking distance to every cell.
            my_distance = flood_distances(grid, self.cell)
            # Count it. The flood fill touches the whole maze, so leaving it out
            # of the reported cost would make this enemy look far cheaper than
            # it is - it is the single most expensive thing it does.
            self.planning_cells = len(my_distance)

            # Deepest first: a cut-off further along their route is better.
            for i in range(len(self.predicted_route) - 1, 0, -1):
                cell = self.predicted_route[i]
                steps = my_distance.get(cell)
                if steps is None:
                    continue
                if steps * self.move_delay <= i * self.player_delay:
                    self.aim_cell = cell
                    self.intercepting = True
                    return cell

        # Cannot beat them anywhere: behave like a normal chaser.
        self.aim_cell = player_cell
        return player_cell

    def update(self, grid, target_cell, now, heading=(0, 0)):
        """Same contract as Enemy.update, plus the player's heading.

        We only re-plan on the steps where a repath is due, so the extra flood
        fill does not run every frame.
        """
        if now - self._last_move < self.move_delay:
            return False

        if self._steps_since_repath >= self.repath_interval:
            aim = self.choose_target(grid, target_cell, heading)
            self.recompute_path(grid, aim)
            # Report the TOTAL cost: planning the intercept plus the path search.
            self.last_search_size += self.planning_cells

        if len(self.path) >= 2:
            self.cell = self.path[1]
            self.path = self.path[1:]
            self._steps_since_repath += 1
            self._last_move = now
            return True

        # We are already standing on the intercept point: hold position and
        # ambush. Forcing a replan next tick is what stops that becoming a
        # permanent freeze if the player changes direction.
        self._steps_since_repath = self.repath_interval
        return False
