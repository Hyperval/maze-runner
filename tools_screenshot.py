"""Capture demo screenshots without opening a window.

Run with:  python tools_screenshot.py

Writes PNGs into assets/ for the README, the slides and the submission's
"sample output" requirement. Using the dummy video driver means this works
over SSH, in CI, or on a machine with no display.
"""

import os
import random
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"      # must precede the pygame import

import pygame  # noqa: E402

import maze  # noqa: E402
from main import LOST, MENU, PLAYING, WON, Game  # noqa: E402

OUT = "assets"


def save(game, name):
    game.draw()
    path = os.path.join(OUT, name)
    pygame.image.save(game.screen, path)
    print(f"  {path}")


def main():
    random.seed(7)
    os.makedirs(OUT, exist_ok=True)
    game = Game()

    print("Writing screenshots:")

    # 1. Title screen
    game.state = MENU
    save(game, "demo_menu.png")

    # 2 & 3. A chase in progress, same position under each algorithm.
    game.level = 5                 # level 5 has two enemies and more coins
    game.new_level()
    cells = maze.floor_cells(game.grid)
    game.player.cell = cells[len(cells) // 2]
    game.elapsed = 12.4

    for label in ("BFS", "A*"):
        # Put the FIRST enemy on the algorithm we're showcasing.
        game.enemies[0].algorithm = label
        for enemy in game.enemies:
            enemy.recompute_path(game.grid, game.player.cell)
        counts = ", ".join(
            f"{e.algorithm} expanded {e.last_search_size}" for e in game.enemies
        )
        print(f"    [{label}] {counts}")
        save(game, f"demo_{label.replace('*', 'star')}.png")

    # 4. Win screen
    game.coins = []
    game.player.cell = game.exit_cell
    game.state = WON
    save(game, "demo_win.png")

    # 5. Lose screen
    game.new_level()
    game.player.cell = game.enemies[0].cell
    game.state = LOST
    save(game, "demo_lose.png")

    pygame.quit()
    print("Done.")


if __name__ == "__main__":
    main()
