import os, sys
os.environ["SDL_VIDEODRIVER"]="dummy"
sys.path.insert(0, r"C:\Users\akhil\maze-runner")
import pygame, random
from main import Game, PLAYING, WON, LOST

random.seed(7)
g = Game()
out = r"C:\Users\akhil\maze-runner\assets"

# Put the player mid-maze so the chase is in progress.
import maze as M
cells = M.floor_cells(g.grid)
g.player.cell = cells[len(cells)//2]

for algo in ("BFS","A*"):
    g.enemy.algorithm = algo
    g.enemy.recompute_path(g.grid, g.player.cell)
    g.elapsed = 12.4
    g.draw()
    pygame.image.save(g.screen, os.path.join(out, f"demo_{algo.replace('*','star')}.png"))
    print(f"{algo:3s} expanded {g.enemy.last_search_size:3d}  path {len(g.enemy.path):3d}")

# Win banner
g.player.cell = g.exit_cell; g.state = WON; g.draw()
pygame.image.save(g.screen, os.path.join(out,"demo_win.png"))
print("saved 3 frames")
