from collections import deque
from pathfinding import _neighbours, _reconstruct

def my_bfs(grid, start, goal):
    """Member A Scratch BFS implementation.
    
    Guarantees shortest path on an unweighted grid by using a FIFO queue.
    """
    if start == goal:
        return [start], [start]

    queue = deque([start])    # 1. FIFO Queue
    seen = {start}            # 2. Seen set (marked immediately on enqueue)
    came_from = {}            # 3. Parent dictionary for backtracking
    visited_order = []

    while queue:
        current = queue.popleft()
        visited_order.append(current)

        if current == goal:
            return _reconstruct(came_from, start, goal), visited_order

        for nxt in _neighbours(grid, current):
            if nxt not in seen:
                seen.add(nxt)                 # Mark on enqueue to prevent duplicates
                came_from[nxt] = current
                queue.append(nxt)

    # Goal unreachable
    return [], visited_order
