"""Record the backup demo video, with no window and no screen recorder.

Run with:  python tools_record_demo.py

Produces docs/MazeRunner_Demo.mp4 — a captioned walkthrough of the game for the
submission's "backup demo video" requirement, and the thing you play if the
live demo fails in front of the examiner.

HOW IT WORKS
    The game is rendered headlessly (SDL's "dummy" driver, so no window opens)
    while the same pathfinding bot that `autoplay.py` uses plays it. Each frame
    is pushed straight into ffmpeg over a pipe rather than saved as thousands
    of PNGs.

    Because the game times movement in milliseconds rather than frames, we can
    feed it our own clock: a fixed 1/30s per frame gives smooth, real-time
    playback that is identical every run.

    There is no audio, so the narration is burned in as captions.
"""

import os
import subprocess
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"      # must precede the pygame import

import pygame  # noqa: E402

import maze  # noqa: E402
from autoplay import choose_target, step_direction  # noqa: E402
from main import LOST, MENU, PLAYING, WON, Game  # noqa: E402
from settings import ENEMY_HEAD_START_MS, HEIGHT, WIDTH  # noqa: E402

OUT = "docs/MazeRunner_Demo.mp4"
FPS = 30
MS_PER_FRAME = 1000 // FPS

CAPTION_H = 76
C_CAP_BG = (10, 10, 16)
C_CAP = (240, 240, 248)
C_CAP_DIM = (150, 150, 170)


class Recorder:
    """Pipes raw frames into ffmpeg, so nothing touches the disk in between."""

    def __init__(self, path, width, height, fps):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.proc = subprocess.Popen(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-f", "rawvideo", "-pix_fmt", "rgb24",
                "-s", f"{width}x{height}", "-r", str(fps),
                "-i", "-",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-crf", "20", "-preset", "medium",
                # H.264 needs even dimensions; pad rather than crop so nothing
                # is lost off the edge of the frame.
                "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
                path,
            ],
            stdin=subprocess.PIPE,
        )

    def add(self, surface):
        self.proc.stdin.write(pygame.image.tostring(surface, "RGB"))

    def close(self):
        self.proc.stdin.close()
        return self.proc.wait()


def make_canvas():
    """A surface the size of the game plus a caption strip underneath."""
    return pygame.Surface((WIDTH, HEIGHT + CAPTION_H))


def compose(canvas, game_surface, fonts, title, sub):
    canvas.fill(C_CAP_BG)
    canvas.blit(game_surface, (0, 0))
    pygame.draw.rect(canvas, C_CAP_BG, (0, HEIGHT, WIDTH, CAPTION_H))

    if title:
        canvas.blit(fonts[0].render(title, True, C_CAP), (26, HEIGHT + 14))
    if sub:
        surf = fonts[1].render(sub, True, C_CAP_DIM)
        if surf.get_width() > WIDTH - 52:
            # Caption would run off the edge. Trim rather than silently clip,
            # so the text always ends in a readable way.
            while surf.get_width() > WIDTH - 70 and len(sub) > 10:
                sub = sub[:-1]
            surf = fonts[1].render(sub.rstrip() + "...", True, C_CAP_DIM)
        canvas.blit(surf, (26, HEIGHT + 44))
    return canvas


def main():
    game = Game(start_in_menu=False)
    fonts = (
        pygame.font.SysFont("consolas", 22, bold=True),
        pygame.font.SysFont("consolas", 16),
    )
    canvas = make_canvas()
    rec = Recorder(OUT, WIDTH, HEIGHT + CAPTION_H, FPS)

    def hold(seconds, title, sub):
        """Freeze on the current frame while a caption is read."""
        game.draw()
        for _ in range(int(seconds * FPS)):
            rec.add(compose(canvas, game.screen, fonts, title, sub))

    def play(level, seconds, title, sub, *, overlay=True, stop_on_end=True):
        """Let the bot play `level` for up to `seconds`, recording every frame."""
        game.level = level
        game.new_level()
        game.show_search = overlay

        now = 0
        for _ in range(int(seconds * FPS)):
            now += MS_PER_FRAME
            game.elapsed = now / 1000.0

            if game.state == PLAYING:
                target = choose_target(game)
                d = step_direction(game, target)
                if d:
                    game.player.try_move(game.grid, d, now)
                game.coins = [c for c in game.coins if c.cell != game.player.cell]

                if game.player.cell == game.exit_cell and game.exit_unlocked:
                    game.state = WON
                elif now >= ENEMY_HEAD_START_MS:
                    for e in game.enemies:
                        e.update(game.grid, game.player.cell, now)
                    if any(e.caught(game.player.cell) for e in game.enemies):
                        game.state = LOST

            game.draw()
            rec.add(compose(canvas, game.screen, fonts, title, sub))

            if stop_on_end and game.state in (WON, LOST):
                hold(2.0, "Level cleared" if game.state == WON else "Caught",
                     "Reaching the exit wins. Touching an enemy ends the run.")
                return game.state
        return game.state

    print("Recording:")

    # 1. Title card
    game.state = MENU
    print("  title screen")
    hold(3.0, "Maze Runner — AI-Controlled Enemy",
         "Problem Statement 15 - REVA University - Hackathon Abhinava")

    # 2. Level 1 — the basic idea
    print("  level 1  (the basic chase)")
    game.state = PLAYING
    play(1, 26, "Level 1 — reach the exit without being caught",
         "Collect every coin to unlock the exit. The enemy re-paths to you every step.")

    # 3. Level 1 again, explaining the overlay
    print("  level 1  (the search overlay)")
    play(1, 18, "Purple = every cell the BFS enemy searched",
         "BFS spreads evenly in all directions - it has no idea where you are.")

    # 4. Level 4 — two algorithms at once
    print("  level 4  (BFS vs A*)")
    play(4, 24, "Level 4 — a second enemy runs A*",
         "Orange is A*: it leans toward you. Same path, fewer cells - see the HUD.")

    # 5. Level 7 — the difficulty curve at its hardest
    print("  level 7  (difficulty at the top end)")
    play(7, 28, "Level 7 — bigger maze, faster enemies, more coins",
         "Tuned against 500 bot playthroughs: levels 1-3 ~70% win rate, later 20-40%.")

    # 6. Closing card
    game.state = MENU
    print("  closing card")
    hold(3.5, "233 tests · 500 bot playthroughs · 50-maze benchmark",
         "github.com/Hyperval/maze-runner")

    code = rec.close()
    pygame.quit()

    if code != 0 or not os.path.exists(OUT):
        print(f"\nffmpeg failed (exit {code}).")
        return 1

    size = os.path.getsize(OUT) / (1024 * 1024)
    print(f"\nWrote {OUT}  ({size:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
