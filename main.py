"""Maze Runner with AI-Controlled Enemy -- entry point.

Run with:  python main.py

Controls
    Arrow keys / WASD   move
    SPACE               start / confirm
    TAB                 switch the enemies' algorithms (BFS <-> A*)
    V                   toggle the search visualisation
    P                   pause
    R                   restart / next level
    M                   back to menu
    ESC                 quit

HOW THE WHOLE FILE IS ORGANISED
    Game.__init__   builds the window and fonts once
    Game.new_level  sets up one level (maze, player, enemies, coins)
    Game.run        the loop: events -> update -> draw, 60 times a second
    Game.update     moves everything and decides win/loss
    Game.draw_*     one small method per thing drawn on screen

PYTHON NOTE: `if __name__ == "__main__":` at the bottom means "only run this
when this file is executed directly, not when another file imports it". That's
why the test files can `from main import Game` without launching a window.
"""

import sys

import pygame

import maze
from entities import Coin, Enemy, Player
from pathfinding import ALGORITHMS, flood_distances
from settings import (
    BRAID_CHANCE, C_ACCENT, C_BG, C_COIN, C_ENEMY, C_ENEMY_2, C_EXIT,
    C_EXIT_LOCKED, C_FLOOR, C_LOSE, C_PATH, C_PATH_2, C_PLAYER, C_TEXT,
    C_TEXT_DIM, C_VISITED, C_VISITED_2, C_WALL, C_WIN, CELL_SIZE, COINS_BASE,
    COIN_BAND_HI, COIN_BAND_LO, COINS_ENABLED, COINS_MAX, COINS_PER_LEVEL,
    COLS, ENEMY_HEAD_START_MS, ENEMY_MIN_DELAY,
    ENEMY_MOVE_DELAY, ENEMY_REPATH_INTERVAL, ENEMY_SPEEDUP_PER_LEVEL, FPS,
    HEIGHT, HUD_HEIGHT, MAX_COLS, MAX_ROWS, MAZE_GROWTH_PER_LEVEL,
    PLAYER_MOVE_DELAY, ROWS, SECOND_ENEMY_DELAY_FACTOR, SECOND_ENEMY_ENABLED,
    SECOND_ENEMY_FROM_LEVEL,
    WIDTH,
)

# Key bindings mapped to (dcol, drow) grid directions.
DIRECTIONS = {
    pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
    pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
    pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
    pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
}

# Game states. Using named strings rather than numbers makes debugging output
# readable -- printing self.state shows "playing", not "2".
MENU, PLAYING, PAUSED, WON, LOST = "menu", "playing", "paused", "won", "lost"


class Game:
    def __init__(self, start_in_menu=True):
        pygame.init()
        pygame.display.set_caption("Maze Runner -- AI Enemy")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("consolas", 20)
        self.font_small = pygame.font.SysFont("consolas", 15)
        self.font_big = pygame.font.SysFont("consolas", 46, bold=True)
        self.font_title = pygame.font.SysFont("consolas", 60, bold=True)

        # Surface used for translucent overlays (paths + visited cells).
        self.overlay = pygame.Surface((WIDTH, HEIGHT - HUD_HEIGHT), pygame.SRCALPHA)

        self.algorithm = "BFS"
        self.show_search = True
        self.level = 1
        self.best_times = {}        # level number -> fastest time in seconds

        self.new_level(reset_level=True)
        # new_level sets state to PLAYING; the menu sits in front of it so the
        # first thing you see is the title screen, with a real level ready
        # behind it the moment you press SPACE.
        self.state = MENU if start_in_menu else PLAYING

    # -- setup -------------------------------------------------------------

    def level_dimensions(self):
        """Maze size for the current level, growing but capped.

        Capping at MAX_COLS/MAX_ROWS matters: the window is built once from
        those maxima, so a maze bigger than them would be drawn off-screen.
        Sizes step by 2 to stay odd, which the carver requires.
        """
        cols = min(MAX_COLS, COLS + (self.level - 1) * MAZE_GROWTH_PER_LEVEL)
        rows = min(MAX_ROWS, ROWS + (self.level - 1) * MAZE_GROWTH_PER_LEVEL)
        # Force odd. If growth ever lands on an even number, step back one.
        if cols % 2 == 0:
            cols -= 1
        if rows % 2 == 0:
            rows -= 1
        return cols, rows

    def enemy_delay(self):
        """How many ms between enemy steps at this level.

        Clamped at ENEMY_MIN_DELAY, which is kept above PLAYER_MOVE_DELAY so
        the enemy is never strictly faster than the player.
        """
        return max(
            ENEMY_MIN_DELAY,
            ENEMY_MOVE_DELAY - (self.level - 1) * ENEMY_SPEEDUP_PER_LEVEL,
        )

    def new_level(self, reset_level=False):
        """Generate a fresh maze and place the player, exit, enemies and coins."""
        if reset_level:
            self.level = 1

        self.cols, self.rows = self.level_dimensions()
        self.grid = maze.generate(self.cols, self.rows, braid_chance=BRAID_CHANCE)

        # Smaller mazes are centred in the fixed-size window.
        self.offset_x = (WIDTH - self.cols * CELL_SIZE) // 2
        self.offset_y = HUD_HEIGHT + (HEIGHT - HUD_HEIGHT - self.rows * CELL_SIZE) // 2

        # Player starts top-left, exit sits bottom-right -- both carved open
        # by the generator, so they're always reachable.
        self.player_start = (1, 1)
        self.exit_cell = (self.cols - 2, self.rows - 2)

        cells = maze.floor_cells(self.grid)
        from_player = flood_distances(self.grid, self.player_start)
        from_exit = flood_distances(self.grid, self.exit_cell)

        self.player = Player(self.player_start, PLAYER_MOVE_DELAY)
        self.enemies = self._spawn_enemies(cells, from_player, from_exit)
        self.coins = self._place_coins(cells, from_player)

        self.state = PLAYING
        self.start_time = pygame.time.get_ticks()
        self.paused_total = 0       # ms spent paused, subtracted from the clock
        self.pause_started = 0
        self.elapsed = 0.0

    def _spawn_enemies(self, cells, from_player, from_exit):
        """Place one or two enemies well away from the player and the exit.

        Naively picking the cell farthest from the player puts the enemy in the
        opposite corner -- which is exactly where the exit is, so it would sit
        on the goal and camp it forever.

        Instead we maximise the SMALLER of (distance to player, distance to
        exit). That forces a start well away from both: the player gets
        reaction time, and the route to the exit stays open. Distances are
        true walking distances, not straight-line, so walls count.
        """
        delay = self.enemy_delay()

        def score(cell):
            return min(from_player.get(cell, 0), from_exit.get(cell, 0))

        first_cell = max(cells, key=score)
        enemies = [
            Enemy(first_cell, delay, self.algorithm, ENEMY_REPATH_INTERVAL,
                  colour=C_ENEMY, path_colour=C_PATH, visited_colour=C_VISITED)
        ]

        # The second enemy runs the OTHER algorithm, so the two can be compared
        # live. It also needs to start away from the first enemy, or they walk
        # in lockstep and the comparison is invisible.
        if SECOND_ENEMY_ENABLED and self.level >= SECOND_ENEMY_FROM_LEVEL:
            other = self._other_algorithm(self.algorithm)
            from_first = flood_distances(self.grid, first_cell)

            second_cell = max(
                cells,
                key=lambda c: min(score(c), from_first.get(c, 0)),
            )
            enemies.append(
                Enemy(second_cell, int(delay * SECOND_ENEMY_DELAY_FACTOR),
                      other, ENEMY_REPATH_INTERVAL,
                      colour=C_ENEMY_2, path_colour=C_PATH_2,
                      visited_colour=C_VISITED_2)
            )
        return enemies

    @staticmethod
    def _other_algorithm(name):
        """Given 'BFS' return 'A*', and vice versa."""
        names = list(ALGORITHMS)
        return names[(names.index(name) + 1) % len(names)]

    def _place_coins(self, cells, from_player):
        """Scatter coins on floor cells away from the player's start.

        Coins are picked from the cells FARTHEST from the player so they can't
        all spawn in the starting corner, which would make them free.
        """
        if not COINS_ENABLED:
            return []

        count = int(min(COINS_MAX, COINS_BASE + (self.level - 1) * COINS_PER_LEVEL))

        candidates = [
            c for c in cells
            if c != self.player_start and c != self.exit_cell
        ]
        # Sort nearest-first by true walking distance from the player's start.
        candidates.sort(key=lambda c: from_player.get(c, 0))

        # Take coins from a middle BAND of that ordering. Using only the
        # farthest cells put every coin in the opposite corner, so the player
        # had to cross the whole maze for each one -- autoplay measured that as
        # near-unwinnable. Using only the nearest would make them free.
        lo = int(len(candidates) * COIN_BAND_LO)
        hi = int(len(candidates) * COIN_BAND_HI)
        band = candidates[lo:hi] or candidates

        if len(band) <= count:
            chosen = band
        else:
            step = len(band) // count
            chosen = [band[i * step] for i in range(count)]

        return [Coin(c) for c in chosen]

    @property
    def exit_unlocked(self):
        """True once every coin has been collected.

        PYTHON NOTE: @property lets you write `self.exit_unlocked` (no
        parentheses) and have this code run. It reads like a variable but is
        computed fresh each time.
        """
        return len(self.coins) == 0

    # -- main loop ---------------------------------------------------------

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit()

                elif event.key == pygame.K_SPACE:
                    if self.state == MENU:
                        self.level = 1
                        self.new_level(reset_level=True)
                    elif self.state == WON:
                        self.level += 1
                        self.new_level()
                    elif self.state == LOST:
                        self.new_level()

                elif event.key == pygame.K_m:
                    self.state = MENU

                elif event.key == pygame.K_p:
                    self.toggle_pause()

                elif event.key == pygame.K_r:
                    # After a win, R advances; otherwise it retries.
                    if self.state == WON:
                        self.level += 1
                        self.new_level()
                    elif self.state != MENU:
                        self.new_level()

                elif event.key == pygame.K_TAB:
                    self.cycle_algorithm()

                elif event.key == pygame.K_v:
                    self.show_search = not self.show_search

    def toggle_pause(self):
        """Pause and unpause, keeping the on-screen timer honest.

        The timer is derived from pygame.time.get_ticks(), which keeps running
        while paused. If we ignored that, the clock would jump forward by the
        pause duration the moment you resumed. So we record when the pause
        started and add the duration to `paused_total`, which update()
        subtracts.
        """
        now = pygame.time.get_ticks()
        if self.state == PLAYING:
            self.state = PAUSED
            self.pause_started = now
        elif self.state == PAUSED:
            self.paused_total += now - self.pause_started
            self.state = PLAYING

    def cycle_algorithm(self):
        """Swap every enemy to the next algorithm, keeping them different."""
        self.algorithm = self._other_algorithm(self.algorithm)
        for i, enemy in enumerate(self.enemies):
            # Enemy 0 gets the selected algorithm, enemy 1 gets the other one,
            # so the pair always demonstrates a contrast.
            enemy.algorithm = (
                self.algorithm if i == 0 else self._other_algorithm(self.algorithm)
            )
            enemy.recompute_path(self.grid, self.player.cell)

    def update(self):
        if self.state != PLAYING:
            return

        now = pygame.time.get_ticks()
        self.elapsed = (now - self.start_time - self.paused_total) / 1000.0

        # Read held keys so movement repeats smoothly while a key is down.
        keys = pygame.key.get_pressed()
        direction = (0, 0)
        for key, offset in DIRECTIONS.items():
            if keys[key]:
                direction = offset
                break
        self.player.try_move(self.grid, direction, now)

        # Collect any coin the player is standing on.
        # PYTHON NOTE: we rebuild the list without the collected coin rather
        # than removing while looping -- modifying a list you're iterating over
        # is a classic source of skipped items.
        self.coins = [c for c in self.coins if c.cell != self.player.cell]

        # Check the win before the enemies move, so reaching the exit on the
        # same tick an enemy arrives counts as a win, not a loss.
        if self.player.cell == self.exit_cell and self.exit_unlocked:
            self.state = WON
            best = self.best_times.get(self.level)
            if best is None or self.elapsed < best:
                self.best_times[self.level] = self.elapsed
            return

        # Enemies hold still for the first moments of a level. This grace
        # period is what makes the level readable: without it the player is
        # under pressure before they can even see where the coins are.
        if self.elapsed * 1000 >= ENEMY_HEAD_START_MS:
            for enemy in self.enemies:
                enemy.update(self.grid, self.player.cell, now)

        # Any enemy on the player's cell ends the run.
        if any(e.caught(self.player.cell) for e in self.enemies):
            self.state = LOST

    # -- rendering ---------------------------------------------------------

    def cell_rect(self, cell, inset=0):
        """Pixel rect for a grid cell, offset by the centring margins."""
        col, row = cell
        return pygame.Rect(
            self.offset_x + col * CELL_SIZE + inset,
            self.offset_y + row * CELL_SIZE + inset,
            CELL_SIZE - inset * 2,
            CELL_SIZE - inset * 2,
        )

    def draw(self):
        self.screen.fill(C_BG)

        if self.state == MENU:
            self.draw_menu()
        else:
            self.draw_maze()
            if self.show_search:
                self.draw_search()
            self.draw_coins()
            self.draw_entities()
            self.draw_hud()
            if self.state in (WON, LOST):
                self.draw_banner()
            elif self.state == PAUSED:
                self.draw_pause()

        pygame.display.flip()

    def draw_menu(self):
        title = self.font_title.render("MAZE RUNNER", True, C_ACCENT)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 110))

        sub = self.font.render("AI-Controlled Enemy  -  BFS vs A*", True, C_TEXT)
        self.screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 185))

        lines = [
            "",
            "Arrow keys / WASD   move",
            "SPACE               start",
            "TAB                 switch algorithm (BFS <-> A*)",
            "V                   show/hide the search overlay",
            "P                   pause",
            "R                   restart level",
            "M                   back to this menu",
            "ESC                 quit",
            "",
            "Collect every coin to unlock the exit.",
            "A second enemy joins at level %d." % SECOND_ENEMY_FROM_LEVEL,
        ]
        y = 260
        for line in lines:
            surf = self.font_small.render(line, True, C_TEXT_DIM)
            self.screen.blit(surf, (WIDTH // 2 - 220, y))
            y += 24

        prompt = self.font.render("Press SPACE to start", True, C_WIN)
        self.screen.blit(
            prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT - 110)
        )

    def draw_maze(self):
        for row in range(self.rows):
            for col in range(self.cols):
                colour = C_WALL if self.grid[row][col] == maze.WALL else C_FLOOR
                pygame.draw.rect(self.screen, colour, self.cell_rect((col, row)))

        # The exit is dull and outlined while locked, bright once unlocked --
        # so the player can see at a glance whether coins remain.
        if self.exit_unlocked:
            pygame.draw.rect(self.screen, C_EXIT, self.cell_rect(self.exit_cell, 3))
            pygame.draw.rect(self.screen, C_WIN, self.cell_rect(self.exit_cell), 2)
        else:
            pygame.draw.rect(
                self.screen, C_EXIT_LOCKED, self.cell_rect(self.exit_cell, 6)
            )
            pygame.draw.rect(
                self.screen, C_EXIT_LOCKED, self.cell_rect(self.exit_cell), 2
            )

    def draw_search(self):
        """Draw the cells each search expanded, then the path it chose.

        This is the part that makes the AI legible instead of magic -- you can
        see BFS flood the maze while A* drives at the player. With two enemies
        the two coloured regions overlap, and the difference in size is the
        whole comparison in one picture.
        """
        self.overlay.fill((0, 0, 0, 0))

        for enemy in self.enemies:
            for col, row in enemy.visited:
                rect = pygame.Rect(
                    self.offset_x + col * CELL_SIZE,
                    self.offset_y - HUD_HEIGHT + row * CELL_SIZE,
                    CELL_SIZE, CELL_SIZE,
                )
                pygame.draw.rect(self.overlay, (*enemy.visited_colour, 85), rect)

        for enemy in self.enemies:
            if len(enemy.path) >= 2:
                points = [
                    (self.offset_x + c * CELL_SIZE + CELL_SIZE // 2,
                     self.offset_y - HUD_HEIGHT + r * CELL_SIZE + CELL_SIZE // 2)
                    for c, r in enemy.path
                ]
                pygame.draw.lines(self.overlay, enemy.path_colour, False, points, 3)

        self.screen.blit(self.overlay, (0, HUD_HEIGHT))

    def draw_coins(self):
        for coin in self.coins:
            rect = self.cell_rect(coin.cell, 8)
            pygame.draw.ellipse(self.screen, C_COIN, rect)

    def draw_entities(self):
        # Enemies drawn as circles, player as a rounded square -- distinct
        # shapes as well as distinct colours, so it stays readable.
        for enemy in self.enemies:
            pygame.draw.ellipse(self.screen, enemy.colour, self.cell_rect(enemy.cell, 3))

        pygame.draw.rect(
            self.screen, C_PLAYER, self.cell_rect(self.player.cell, 3), border_radius=5
        )

    def draw_hud(self):
        pygame.draw.rect(self.screen, C_BG, (0, 0, WIDTH, HUD_HEIGHT))

        coins_left = len(self.coins)
        coin_text = "EXIT OPEN" if coins_left == 0 else f"Coins {coins_left}"
        left = self.font.render(
            f"Level {self.level}   {self.elapsed:5.1f}s   Steps {self.player.steps}   {coin_text}",
            True, C_TEXT,
        )
        self.screen.blit(left, (12, 8))

        # Showing each enemy's expanded-cell count turns the BFS-vs-A*
        # difference into numbers the judges can watch change live.
        parts = [
            f"{e.algorithm}: {e.last_search_size} cells" for e in self.enemies
        ]
        right = self.font_small.render("   |   ".join(parts), True, C_TEXT_DIM)
        self.screen.blit(right, (12, 32))

        hint = self.font_small.render(
            "TAB algo   V overlay   P pause   R restart   M menu", True, C_TEXT_DIM
        )
        self.screen.blit(hint, (WIDTH - hint.get_width() - 12, 32))

    def draw_pause(self):
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((10, 10, 16, 170))
        self.screen.blit(shade, (0, 0))

        text = self.font_big.render("PAUSED", True, C_ACCENT)
        sub = self.font_small.render("P to resume   -   M for menu", True, C_TEXT)
        self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 40))
        self.screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 18))

    def draw_banner(self):
        """Dim the maze and show the win/lose message."""
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((10, 10, 16, 190))
        self.screen.blit(shade, (0, 0))

        if self.state == WON:
            title, colour = "ESCAPED!", C_WIN
            best = self.best_times.get(self.level)
            best_txt = f"   (best {best:.1f}s)" if best is not None else ""
            subtitle = (
                f"Level {self.level} cleared in {self.elapsed:.1f}s{best_txt}"
                "  --  SPACE for next level"
            )
        else:
            caught_by = next(
                (e.algorithm for e in self.enemies if e.caught(self.player.cell)),
                self.algorithm,
            )
            title, colour = "CAUGHT", C_LOSE
            subtitle = f"The {caught_by} enemy got you  --  SPACE to retry"

        text = self.font_big.render(title, True, colour)
        sub = self.font_small.render(subtitle, True, C_TEXT)
        self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 44))
        self.screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 14))

    def quit(self):
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    Game().run()
