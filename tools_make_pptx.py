"""Build the presentation as an editable PowerPoint file.

Run with:  python tools_make_pptx.py

Produces docs/MazeRunner_Slides.pptx -- five 16:9 slides matching the deck,
with speaker notes on every slide. Editable in PowerPoint, Google Slides or
LibreOffice Impress, and it opens with no internet connection.

Fonts: we ask for Segoe UI and Consolas, which ship with Windows, so the deck
renders correctly on any lab machine without downloading anything.
"""

import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

OUT = "docs/MazeRunner_Slides.pptx"

# --- palette (same colours as the game and the web deck) -------------------
INK = RGBColor(0x12, 0x12, 0x18)        # near-black background
INK_SOFT = RGBColor(0x17, 0x17, 0x1F)   # second background tone
CARD = RGBColor(0x1B, 0x1B, 0x24)
CARD_EDGE = RGBColor(0x2E, 0x2E, 0x3C)
PAPER = RGBColor(0xF2, 0xF2, 0xF7)
MUTED = RGBColor(0x9B, 0xA3, 0xB4)
BODY = RGBColor(0xC9, 0xCE, 0xDA)
DIM = RGBColor(0x6A, 0x71, 0x79)
CYAN = RGBColor(0x56, 0xCC, 0xF2)        # player / accent
PURPLE = RGBColor(0x7C, 0x65, 0xD6)      # BFS
ORANGE = RGBColor(0xF2, 0x99, 0x4A)      # A*
GREEN = RGBColor(0x2D, 0x9D, 0x78)
RED = RGBColor(0xEB, 0x57, 0x57)
CYAN_DARK = RGBColor(0x15, 0x50, 0x6B)
CYAN_PALE = RGBColor(0xEA, 0xF8, 0xFE)
CYAN_EDGE = RGBColor(0x8F, 0xD9, 0xF5)

SANS = "Segoe UI"
MONO = "Consolas"

W, H = Inches(13.333), Inches(7.5)       # 16:9
MARGIN = Inches(0.85)


def blank(prs, bg):
    """Add a slide with no placeholders and a solid background."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = bg
    return slide


def textbox(slide, x, y, w, h):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    return tf


def para(tf, text, size, colour, *, bold=False, font=SANS, space_after=0,
         first=False, align=None, line=None):
    """Add a paragraph (reusing the empty first one PowerPoint creates)."""
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.name = font
    p.font.color.rgb = colour
    p.space_after = Pt(space_after)
    if align is not None:
        p.alignment = align
    if line is not None:
        p.line_spacing = line
    return p


def card(slide, x, y, w, h, *, fill=CARD, edge=CARD_EDGE, edge_w=1.0):
    from pptx.enum.shapes import MSO_SHAPE
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    shape.adjustments[0] = 0.06
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = edge
    shape.line.width = Pt(edge_w)
    shape.shadow.inherit = False
    # We write text in our own textbox so we control padding precisely.
    shape.text_frame.text = ""
    return shape


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def heading(slide, title, subtitle=None):
    tf = textbox(slide, MARGIN, Inches(0.62), W - MARGIN * 2, Inches(1.5))
    para(tf, title, 38, PAPER, bold=True, first=True, space_after=7)
    if subtitle:
        para(tf, subtitle, 16, MUTED, line=1.3)


# --------------------------------------------------------------------------

def slide_cover(prs):
    s = blank(prs, INK)

    tf = textbox(s, MARGIN, Inches(1.15), W - MARGIN * 2, Inches(3.0))
    para(tf, "PROBLEM STATEMENT 15", 14, CYAN, font=MONO, first=True, space_after=12)
    para(tf, "Maze Runner", 66, PAPER, bold=True, space_after=10)
    para(tf, "A maze game where the enemy hunts you with real pathfinding — BFS and A*",
         22, MUTED, line=1.25)

    labels = ["TEAM", "BUILT WITH", "SHIPPED"]
    bodies = [
        "Akhil Sathish Kumar\nAkshay N\nAbdullah Subhaan K\nChristen Mendis",
        "Python 3 + pygame-ce\nNo dataset, no network,\nno hardware",
        "226 tests passing\n500 bot playthroughs\n50-maze benchmark",
    ]
    cw = (W - MARGIN * 2 - Inches(0.5)) / 3
    for i, (label, body) in enumerate(zip(labels, bodies)):
        x = MARGIN + i * (cw + Inches(0.25))
        card(s, x, Inches(4.45), cw, Inches(1.95))
        tf = textbox(s, x + Inches(0.3), Inches(4.7), cw - Inches(0.6), Inches(1.5))
        para(tf, label, 12, PURPLE, font=MONO, first=True, space_after=7)
        for j, line in enumerate(body.split("\n")):
            para(tf, line, 13.5, PAPER, line=1.3)

    tf = textbox(s, MARGIN, H - Inches(0.75), W - MARGIN * 2, Inches(0.4))
    para(tf, "REVA University  ·  B25CS0311 Portfolio Building  ·  "
             "Hackathon Abhinava  ·  07/10/2026", 11, DIM, font=MONO, first=True)

    notes(s, "AKHIL — 20 seconds. Open here. 'Good morning. We're presenting "
             "problem statement 15 - a maze game where the enemy chases the "
             "player using pathfinding. I'm Akhil, and this is Akshay, Abdullah "
             "and Christen.' Then hand to Akshay. Do NOT read the three cards "
             "out; the examiners can see them. The demo is where the marks are.")


def slide_solution(prs):
    s = blank(prs, INK)
    heading(s, "You can see the AI thinking",
            "Both enemies search the maze every step. We draw the cells each one "
            "expanded, so the difference is one picture, not a claim.")

    img = "assets/demo_BFS.png"
    if os.path.exists(img):
        s.shapes.add_picture(img, MARGIN, Inches(2.35), width=Inches(7.2))

    x = MARGIN + Inches(7.5)
    cw = W - x - MARGIN

    for i, (name, colour, text) in enumerate([
        ("BFS — 175 cells", PURPLE,
         "A FIFO queue, so it finishes every cell at distance d before touching "
         "d+1. Shortest path guaranteed — but it floods outward in all directions."),
        ("A* — 100 cells", ORANGE,
         "Scores each cell f = g + h, where h is Manhattan distance. Same shortest "
         "path, but it leans toward the player instead of spreading evenly."),
    ]):
        y = Inches(2.45) + i * Inches(1.95)
        card(s, x, y, cw, Inches(1.72))
        bar = s.shapes.add_shape(1, x, y, Inches(0.055), Inches(1.72))  # MSO_SHAPE.RECTANGLE
        bar.fill.solid()
        bar.fill.fore_color.rgb = colour
        bar.line.fill.background()
        bar.shadow.inherit = False

        tf = textbox(s, x + Inches(0.3), y + Inches(0.22), cw - Inches(0.6), Inches(1.3))
        para(tf, name, 17, colour, bold=True, first=True, space_after=6)
        para(tf, text, 12.5, BODY, line=1.3)

    tf = textbox(s, x, Inches(6.4), cw, Inches(0.5))
    para(tf, "Press TAB mid-chase to swap them. The counts update live in the HUD.",
         11.5, DIM, first=True, line=1.25)

    notes(s, "AKSHAY — 60 to 75 seconds. This is the slide that earns Technical "
             "Implementation marks; take your time. Point at the purple region: "
             "175 cells, BFS spreading in all directions because it has no idea "
             "where the player is. Then orange: 100 cells, A* leaning toward the "
             "player. Both found a path of the SAME length. "
             "TRAP QUESTION - 'so A* is better?' Do NOT say yes. Answer: it "
             "expands fewer cells but ran SLOWER in wall-clock time, heap at "
             "O(log n) versus deque at O(1); at our maze size the per-cell "
             "overhead outweighs the cells saved. Christen's slide has the data.")


def slide_stack(prs):
    s = blank(prs, INK_SOFT)
    heading(s, "How it fits together",
            "Five modules for the game, two standalone tools that measure it. "
            "No dataset, no network, no hardware.")

    top = [
        ("pathfinding.py", "BFS, A*, flood-fill distance maps. The technical core."),
        ("maze.py", "Recursive-backtracker carving, braiding for escape routes."),
        ("entities.py", "Player, Enemy, Coin. Each enemy holds its own algorithm."),
        ("main.py", "Game loop, state machine, rendering, the search overlay."),
    ]
    bottom = [
        ("benchmark.py", "Runs BFS against A* over 50 generated mazes and charts it."),
        ("autoplay.py", "Plays the game headlessly hundreds of times, hunting crashes."),
        ("test_pathfinding.py", "226 headless checks, including a fuzz test. All passing."),
    ]

    gap = Inches(0.22)
    cw = (W - MARGIN * 2 - gap * 3) / 4
    for i, (name, desc) in enumerate(top):
        x = MARGIN + i * (cw + gap)
        card(s, x, Inches(2.5), cw, Inches(1.65))
        tf = textbox(s, x + Inches(0.26), Inches(2.72), cw - Inches(0.52), Inches(1.3))
        para(tf, name, 12.5, CYAN, font=MONO, first=True, space_after=7)
        para(tf, desc, 12, BODY, line=1.3)

    cw3 = (W - MARGIN * 2 - gap * 2) / 3
    for i, (name, desc) in enumerate(bottom):
        x = MARGIN + i * (cw3 + gap)
        sh = card(s, x, Inches(4.45), cw3, Inches(1.7))
        bar = s.shapes.add_shape(1, x, Inches(4.45), cw3, Inches(0.05))
        bar.fill.solid()
        bar.fill.fore_color.rgb = GREEN
        bar.line.fill.background()
        bar.shadow.inherit = False
        tf = textbox(s, x + Inches(0.26), Inches(4.72), cw3 - Inches(0.52), Inches(1.3))
        para(tf, name, 12.5, GREEN, font=MONO, first=True, space_after=7)
        para(tf, desc, 12, BODY, line=1.3)

    tf = textbox(s, MARGIN, H - Inches(0.75), W - MARGIN * 2, Inches(0.4))
    para(tf, "github.com/Hyperval/maze-runner", 11, DIM, font=MONO, first=True)

    notes(s, "ABDULLAH — 30 seconds, keep it short. Do NOT read all seven boxes. "
             "Land one point: the bottom row is tooling we wrote to check our own "
             "work, not game features. 'We didn't just build it, we built the "
             "things that tell us whether it works.' Then go straight into the "
             "live demo - you drive, Akshay narrates the algorithm.")


def slide_challenges(prs):
    s = blank(prs, INK)
    heading(s, "Three things that went wrong",
            "Each one was found by measurement, not by playing.")

    items = [
        (RED, "The enemy camped the exit",
         "We spawned it farthest from the player — which is the opposite corner, "
         "exactly where the exit is. Fixed by maximising min(distance to player, "
         "distance to exit), using real walking distance so walls count."),
        (ORANGE, "The game was unwinnable",
         "Our bot tester reported 0% win rate from level 3. Root cause: the "
         "enemy's floor speed was 100ms against the player's 90ms — only 1.1x "
         "slower than something that never rests and always takes the shortest route."),
        (GREEN, "After tuning, over 500 runs",
         "Levels 1-3 land at 68-70%, levels 4-10 at 20-38%. No crashes. We tuned "
         "difficulty against numbers, not feel."),
    ]
    cw = Inches(5.6)
    for i, (colour, title, text) in enumerate(items):
        y = Inches(2.4) + i * Inches(1.52)
        card(s, MARGIN, y, cw, Inches(1.34))
        bar = s.shapes.add_shape(1, MARGIN, y, Inches(0.055), Inches(1.34))
        bar.fill.solid()
        bar.fill.fore_color.rgb = colour
        bar.line.fill.background()
        bar.shadow.inherit = False
        tf = textbox(s, MARGIN + Inches(0.28), y + Inches(0.17), cw - Inches(0.56), Inches(1.0))
        para(tf, title, 15, colour, bold=True, first=True, space_after=5)
        para(tf, text, 11.5, BODY, line=1.25)

    x = MARGIN + cw + Inches(0.45)
    rw = W - x - MARGIN
    img = "assets/benchmark.png"
    if os.path.exists(img):
        pic = s.shapes.add_picture(img, x, Inches(2.4), width=rw)

    y = Inches(4.75)
    card(s, x, y, rw, Inches(2.0), edge=CYAN, edge_w=1.4)
    tf = textbox(s, x + Inches(0.28), y + Inches(0.2), rw - Inches(0.56), Inches(1.7))
    para(tf, "The result we did not expect", 15, CYAN, bold=True, first=True, space_after=5)
    para(tf, "A* expanded 26% fewer cells — but ran slower in wall-clock time, "
             "0.219ms against 0.169ms. BFS uses a deque at O(1) per operation; A* "
             "uses a heap at O(log n) plus a heuristic per neighbour. At 650 cells "
             "the overhead per cell beats the cells saved.", 11.5, BODY, line=1.25)

    notes(s, "CHRISTEN — 75 to 90 seconds. The team's strongest slide; take your "
             "time. Start with the exit-camping bug, it's concrete and instantly "
             "understandable. Then the balance finding, and stress that a TOOL WE "
             "WROTE found it, not playtesting. Save the blue box for last and "
             "deliver it slowly - A* expanded fewer cells but ran slower, and here "
             "is why. Pause after it and let it land. If asked 'so which is "
             "better': depends on map size and what visiting a cell costs.")


def slide_future(prs):
    s = blank(prs, CYAN)

    tf = textbox(s, MARGIN, Inches(0.75), W - MARGIN * 2, Inches(1.5))
    para(tf, "FUTURE SCOPE", 13, CYAN_DARK, font=MONO, first=True, space_after=9)
    para(tf, "What we would build next", 40, INK, bold=True)

    items = [
        ("A predictive enemy",
         "Right now it chases where you are. An enemy that paths to where you are "
         "heading could cut you off at a junction instead of trailing you."),
        ("Dijkstra with terrain",
         "Mud cells costing 3 steps instead of 1, to show why BFS is really "
         "Dijkstra with every edge weighted the same."),
        ("A better heuristic",
         "Manhattan distance is weak in a twisty maze. One that accounts for walls "
         "would widen A*'s lead — if it can be computed cheaply enough to pay for itself."),
        ("Fog of war",
         "Limit the player's vision radius, so the maze has to be learned rather "
         "than read off the screen in one glance."),
    ]
    gap = Inches(0.22)
    cw = (W - MARGIN * 2 - gap * 3) / 4
    for i, (title, text) in enumerate(items):
        x = MARGIN + i * (cw + gap)
        card(s, x, Inches(2.75), cw, Inches(2.5), fill=CYAN_PALE, edge=CYAN_EDGE)
        tf = textbox(s, x + Inches(0.28), Inches(3.0), cw - Inches(0.56), Inches(2.1))
        para(tf, title, 15, INK, bold=True, first=True, space_after=7)
        para(tf, text, 12, RGBColor(0x2C, 0x3A, 0x44), line=1.3)

    tf = textbox(s, MARGIN, Inches(5.85), W - MARGIN * 2, Inches(0.6))
    para(tf, "github.com/Hyperval/maze-runner", 16, INK, font=MONO,
         bold=True, first=True, space_after=6)
    para(tf, "Thank you — questions welcome.", 16, CYAN_DARK)

    notes(s, "AKHIL — 40 seconds. Pick ONE item, don't read all four. Best is the "
             "predictive enemy, because it names a real limitation: the enemy "
             "always trails, it never intercepts. 'With more time we'd have it "
             "path to where you're heading, so it could cut you off at a junction. "
             "That's a different problem - you have to predict intent, not just "
             "compute a route.' Then close cleanly and STOP: 'That's our project. "
             "Code and documentation are on GitHub. Happy to take questions.'")


def main():
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H

    slide_cover(prs)
    slide_solution(prs)
    slide_stack(prs)
    slide_challenges(prs)
    slide_future(prs)

    os.makedirs("docs", exist_ok=True)
    prs.save(OUT)
    size = os.path.getsize(OUT) / 1024
    print(f"Saved {OUT}  ({size:.0f} KB, {len(prs.slides.__iter__.__self__._sldIdLst)} slides)")
    print("Speaker notes are on every slide — open the Notes pane in PowerPoint.")


if __name__ == "__main__":
    main()
