"""Watch the maze being carved, one step at a time.

Run with:  python visualise_maze.py

This is the generation algorithm made visible. The carver tunnels forward
picking random neighbours, hits a dead end, backtracks down its stack, and
tunnels off in a new direction — and you can watch it happen.

Controls
    SPACE   pause / resume
    R       new maze (new random seed)
    UP/DOWN faster / slower
    B       toggle braiding on the finished maze
    ESC     quit

WHY THIS EXISTS (Member B — Akhil)
    You cannot write this without understanding the algorithm, because the
    visualiser is driven by `maze.carve_steps()`, a generator that yields the
    grid after every single carve. Each frame pulls one step out of it.

    It also makes the `yield` keyword concrete: the generator function freezes
    mid-loop and resumes where it left off, so we never store hundreds of
    copies of the maze.
"""

import sys

import pygame

import maze
from settings import (
    BRAID_CHANCE, C_BG, C_FLOOR, C_TEXT, C_TEXT_DIM, C_WALL, CELL_SIZE,
    COLS, FPS, ROWS,
)

HUD = 86
WIDTH = COLS * CELL_SIZE
HEIGHT = ROWS * CELL_SIZE + HUD

# Colours specific to this tool.
C_HEAD = (86, 204, 242)        # the cell the carver is standing on
C_STACK = (60, 72, 110)        # cells still on the stack (the route back)
C_NEW = (242, 201, 76)         # the cell carved this very step
C_BRAID = (111, 207, 151)      # walls removed by braiding

SPEEDS = [1, 2, 4, 8, 16, 40]  # carve steps performed per frame


class Visualiser:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Maze Carving — recursive backtracker")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 19)
        self.font_small = pygame.font.SysFont("consolas", 14)

        self.seed = 1
        self.speed_idx = 2
        self.braid_on = True
        self.restart()

    def restart(self, new_seed=True):
        if new_seed:
            self.seed += 1
        # carve_steps is a GENERATOR: calling it runs no code yet. Each next()
        # advances the carver by exactly one step and hands back the grid.
        self.steps = maze.carve_steps(COLS, ROWS, seed=self.seed)
        self.grid = next(self.steps)
        self.done = False
        self.paused = False
        self.count = 0
        self.last_cell = None
        self.braided_cells = set()

    def advance(self, n):
        """Pull up to n carve steps out of the generator."""
        for _ in range(n):
            if self.done:
                return
            try:
                before = self.floor_set()
                self.grid = next(self.steps)
                self.count += 1
                # Whatever became floor this step is what the carver just cut.
                new = self.floor_set() - before
                self.last_cell = max(new) if new else self.last_cell
            except StopIteration:
                self.done = True
                if self.braid_on:
                    import random
                    before = self.floor_set()
                    maze.braid(self.grid, random.Random(self.seed), BRAID_CHANCE)
                    self.braided_cells = self.floor_set() - before
                return

    def floor_set(self):
        return {
            (c, r)
            for r, line in enumerate(self.grid)
            for c, v in enumerate(line)
            if v == maze.FLOOR
        }

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.quit()
                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_r:
                        self.restart()
                    elif event.key == pygame.K_b:
                        self.braid_on = not self.braid_on
                        self.restart(new_seed=False)
                    elif event.key == pygame.K_UP:
                        self.speed_idx = min(len(SPEEDS) - 1, self.speed_idx + 1)
                    elif event.key == pygame.K_DOWN:
                        self.speed_idx = max(0, self.speed_idx - 1)

            if not self.paused and not self.done:
                self.advance(SPEEDS[self.speed_idx])

            self.draw()
            self.clock.tick(FPS)

    def draw(self):
        self.screen.fill(C_BG)

        for r, line in enumerate(self.grid):
            for c, v in enumerate(line):
                rect = pygame.Rect(
                    c * CELL_SIZE, HUD + r * CELL_SIZE, CELL_SIZE, CELL_SIZE
                )
                if (c, r) in self.braided_cells:
                    colour = C_BRAID
                elif v == maze.FLOOR:
                    colour = C_FLOOR
                else:
                    colour = C_WALL
                pygame.draw.rect(self.screen, colour, rect)

        # The cell the carver most recently cut.
        if self.last_cell and not self.done:
            c, r = self.last_cell
            pygame.draw.rect(
                self.screen, C_HEAD,
                pygame.Rect(c * CELL_SIZE + 3, HUD + r * CELL_SIZE + 3,
                            CELL_SIZE - 6, CELL_SIZE - 6),
                border_radius=4,
            )

        self.draw_hud()
        pygame.display.flip()

    def draw_hud(self):
        pygame.draw.rect(self.screen, C_BG, (0, 0, WIDTH, HUD))

        if self.done:
            status = f"DONE — {self.count} carve steps"
            if self.braided_cells:
                status += f", {len(self.braided_cells)} walls braided open"
        elif self.paused:
            status = f"PAUSED at step {self.count}"
        else:
            status = f"Carving… step {self.count}"

        self.screen.blit(self.font.render(status, True, C_TEXT), (12, 10))

        line2 = (f"seed {self.seed}   speed {SPEEDS[self.speed_idx]}x/frame   "
                 f"braiding {'ON' if self.braid_on else 'OFF'}")
        self.screen.blit(self.font_small.render(line2, True, C_TEXT_DIM), (12, 36))

        hint = "SPACE pause   R new maze   UP/DOWN speed   B braiding   ESC quit"
        surf = self.font_small.render(hint, True, C_TEXT_DIM)
        self.screen.blit(surf, (12, 58))

    def quit(self):
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    Visualiser().run()
