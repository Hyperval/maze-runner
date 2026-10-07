"""Pathfinding algorithms for the enemy AI.

This is the technical core of the project. Both searches return the same shape
of result so the game loop can swap between them at runtime:

    (path, visited_order)

    path          - list of (col, row) cells from start to goal, inclusive.
                    Empty list if the goal is unreachable.
    visited_order - the cells the algorithm expanded, in the order it expanded
                    them. The game draws these so you can literally watch the
                    search spread out across the maze.

Why keep both BFS and A*?
    BFS explores every cell at distance 1, then every cell at distance 2, and
    so on. On an unweighted grid that guarantees the shortest path, but it
    expands a lot of cells that lead nowhere near the player.

    A* explores in the same way except it prefers cells that *look* closer to
    the goal, using Manhattan distance as the heuristic. It finds the same
    shortest path but expands far fewer cells. Press TAB in game and watch the
    purple visited-region shrink -- that difference is the whole point.
"""

from collections import deque
import heapq

# The four grid-aligned moves. No diagonals: the maze walls are drawn on the
# grid, so allowing diagonals would let the enemy clip through wall corners.
NEIGHBOUR_OFFSETS = ((0, -1), (1, 0), (0, 1), (-1, 0))


def _neighbours(grid, cell):
    """Yield the walkable cells orthogonally adjacent to `cell`.

    `grid` is a 2D list indexed grid[row][col] where 1 is a wall and 0 is
    floor. Bounds are checked here so neither search has to worry about it.
    """
    col, row = cell
    rows = len(grid)
    cols = len(grid[0])

    for dcol, drow in NEIGHBOUR_OFFSETS:
        ncol, nrow = col + dcol, row + drow
        if 0 <= ncol < cols and 0 <= nrow < rows and grid[nrow][ncol] == 0:
            yield (ncol, nrow)


def _reconstruct(came_from, start, goal):
    """Walk the parent pointers backwards from goal to start.

    `came_from[cell]` holds the cell we arrived from. Following those links
    from the goal gives the route in reverse, so we flip it at the end.
    """
    if goal not in came_from and goal != start:
        return []                      # goal was never reached

    path = [goal]
    while path[-1] != start:
        path.append(came_from[path[-1]])
    path.reverse()
    return path


def bfs(grid, start, goal):
    """Breadth-first search. Guarantees the shortest path on an unweighted grid.

    We hold a FIFO queue of cells to visit. Because we always pop the oldest
    cell, we finish exploring everything at distance d before touching anything
    at distance d+1 -- which is exactly why the first time we touch the goal,
    we touched it by a shortest route.
    """
    if start == goal:
        return [start], [start]

    queue = deque([start])
    came_from = {}
    seen = {start}
    visited_order = []

    while queue:
        current = queue.popleft()
        visited_order.append(current)

        if current == goal:
            return _reconstruct(came_from, start, goal), visited_order

        for nxt in _neighbours(grid, current):
            if nxt not in seen:
                seen.add(nxt)
                came_from[nxt] = current
                queue.append(nxt)

    # Queue drained without finding the goal -- no route exists.
    return [], visited_order


def manhattan(a, b):
    """Grid distance ignoring walls. Never overestimates the real distance,
    which is the property A* needs to stay optimal."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(grid, start, goal):
    """A* search. Same shortest path as BFS, far fewer cells expanded.

    Each cell is scored f = g + h:
        g - steps actually taken to reach this cell
        h - Manhattan guess of steps remaining to the goal
    We always expand the lowest-f cell, so the search leans toward the goal
    instead of spreading out evenly in all directions.
    """
    if start == goal:
        return [start], [start]

    # Entries are (f, tie_breaker, cell). The counter keeps the comparison
    # from ever reaching the tuple's cell element, which isn't orderable.
    counter = 0
    open_heap = [(manhattan(start, goal), counter, start)]
    came_from = {}
    g_score = {start: 0}
    closed = set()
    visited_order = []

    while open_heap:
        _, _, current = heapq.heappop(open_heap)

        if current in closed:
            continue               # stale duplicate left over from a re-push
        closed.add(current)
        visited_order.append(current)

        if current == goal:
            return _reconstruct(came_from, start, goal), visited_order

        for nxt in _neighbours(grid, current):
            tentative_g = g_score[current] + 1

            # Only keep this route if it beats any route we already have.
            if tentative_g < g_score.get(nxt, float("inf")):
                came_from[nxt] = current
                g_score[nxt] = tentative_g
                counter += 1
                heapq.heappush(
                    open_heap,
                    (tentative_g + manhattan(nxt, goal), counter, nxt),
                )

    return [], visited_order


# Registry so the game loop can cycle algorithms without knowing their names.
ALGORITHMS = {
    "BFS": bfs,
    "A*": astar,
}


def flood_distances(grid, start):
    """Map every reachable cell to its true step-distance from `start`.

    This is BFS without a goal: we expand until the whole reachable region is
    measured. We use it to place the enemy, because Manhattan distance would
    happily call two cells "far apart" when a single wall between them makes
    the real walk 40 steps -- or call them far when they're adjacent around a
    corner.
    """
    dist = {start: 0}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for nxt in _neighbours(grid, current):
            if nxt not in dist:
                dist[nxt] = dist[current] + 1
                queue.append(nxt)
    return dist
