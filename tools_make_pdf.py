"""Build a single printable study guide PDF from the docs/ markdown files.

Run with:  python tools_make_pdf.py

Produces docs/MazeRunner_StudyGuide.pdf -- everything the team needs to learn
the project, in one document with a contents page, ready to print or read on a
phone the morning of the viva.

It works in two stages:
  1. Markdown  -> HTML   (the `markdown` library, plus a print stylesheet)
  2. HTML      -> PDF    (headless Chrome, which every machine here has)

Chrome is used rather than a Python PDF library because it already renders the
tables, code blocks and page breaks correctly, and needs no extra installs.
"""

import os
import re
import shutil
import subprocess
import sys

import markdown

# Order matters: this is the order someone should read them in.
SOURCES = [
    ("docs/CODE_WALKTHROUGH.md", "Code Walkthrough"),
    ("docs/VIVA_PREP.md", "Viva Preparation"),
    ("README.md", "Project README"),
    ("docs/MEMBER_A.md", "Member A — Core Logic"),
    ("docs/MEMBER_B.md", "Member B — Maze & Balance"),
    ("docs/MEMBER_C.md", "Member C — Interface & Testing"),
    ("docs/MEMBER_D.md", "Member D — Analysis & Docs"),
]

OUT_HTML = "docs/_studyguide.html"
OUT_PDF = "docs/MazeRunner_StudyGuide.pdf"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

CSS = """
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; }
body {
  font-family: "Segoe UI", -apple-system, Helvetica, Arial, sans-serif;
  font-size: 10.5pt; line-height: 1.55; color: #1b1b22;
  margin: 0; padding: 0;
}
h1 { font-size: 23pt; color: #15151d; margin: 0 0 4pt;
     border-bottom: 2.5pt solid #56ccf2; padding-bottom: 6pt; }
h2 { font-size: 16pt; color: #15151d; margin: 20pt 0 6pt;
     border-bottom: 0.7pt solid #d4d7e0; padding-bottom: 3pt;
     page-break-after: avoid; }
h3 { font-size: 12.5pt; color: #2a2a35; margin: 14pt 0 4pt;
     page-break-after: avoid; }
p, li { orphans: 3; widows: 3; }
code { font-family: "Consolas", "Courier New", monospace; font-size: 9.2pt;
       background: #f1f2f6; padding: 1pt 3pt; border-radius: 3px;
       color: #8a3b6b; }
pre { background: #f7f8fa; border: 0.7pt solid #dfe2ea; border-left: 3pt solid #7c65d6;
      border-radius: 4px; padding: 8pt 10pt; overflow-x: auto;
      page-break-inside: avoid; font-size: 9pt; line-height: 1.42; }
pre code { background: none; padding: 0; color: #22222c; }
table { border-collapse: collapse; width: 100%; margin: 9pt 0; font-size: 9.3pt;
        page-break-inside: avoid; }
th { background: #eef0f5; text-align: left; font-weight: 600;
     border: 0.7pt solid #ccd0db; padding: 4.5pt 6pt; }
td { border: 0.7pt solid #dfe2ea; padding: 4.5pt 6pt; vertical-align: top; }
blockquote { margin: 8pt 0; padding: 6pt 12pt; border-left: 3pt solid #56ccf2;
             background: #f3fbfe; color: #26323c; }
hr { border: none; border-top: 0.7pt solid #d4d7e0; margin: 14pt 0; }
a { color: #1f6f94; text-decoration: none; }
strong { color: #15151d; }

.cover { text-align: center; padding-top: 55mm; page-break-after: always; }
.cover h1 { font-size: 34pt; border: none; margin-bottom: 10pt; }
.cover .sub { font-size: 14pt; color: #555f6e; margin-bottom: 30pt; }
.cover .meta { font-size: 10.5pt; color: #6a7179; line-height: 1.9; }
.cover .rule { width: 58mm; height: 3pt; background: #56ccf2; margin: 16pt auto 22pt; }

.toc { page-break-after: always; }
.toc h1 { border-bottom: 2.5pt solid #56ccf2; }
.toc ol { font-size: 12pt; line-height: 2.1; padding-left: 18pt; }
.toc a { color: #1b1b22; }

.chapter { page-break-before: always; }
.chapter > h1 { margin-top: 0; }
"""


def find_chrome():
    for path in CHROME_CANDIDATES:
        if os.path.exists(path):
            return path
    for name in ("chrome", "google-chrome", "msedge"):
        found = shutil.which(name)
        if found:
            return found
    return None


def demote_headings(html):
    """Push every heading down one level so each file's H1 nests under its
    chapter title. Done on the rendered HTML so fenced code is untouched."""
    for level in (5, 4, 3, 2, 1):
        html = html.replace(f"<h{level}>", f"<h{level + 1}>")
        html = html.replace(f"</h{level}>", f"</h{level + 1}>")
    return html


def build_html():
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists"])

    chapters = []
    toc_entries = []
    missing = []

    for i, (path, title) in enumerate(SOURCES, start=1):
        if not os.path.exists(path):
            missing.append(path)
            continue

        with open(path, encoding="utf-8") as fh:
            text = fh.read()

        # Drop the file's own top-level title; the chapter heading replaces it.
        text = re.sub(r"\A#\s+.*?\n", "", text, count=1)

        md.reset()
        body = demote_headings(md.convert(text))

        anchor = f"ch{i}"
        toc_entries.append(f'<li><a href="#{anchor}">{title}</a></li>')
        chapters.append(
            f'<div class="chapter" id="{anchor}"><h1>{i}. {title}</h1>{body}</div>'
        )

    if missing:
        print("  (skipped, not found: " + ", ".join(missing) + ")")

    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Maze Runner — Study Guide</title>
<style>{CSS}</style></head><body>

<div class="cover">
  <h1>Maze Runner</h1>
  <div class="rule"></div>
  <div class="sub">AI-Controlled Enemy — BFS vs A*<br>Complete Study Guide</div>
  <div class="meta">
    Problem Statement 15<br>
    REVA University · B25CS0311 Portfolio Building<br>
    Hackathon अभिनव (Abhinava) · 07/10/2026<br><br>
    github.com/Hyperval/maze-runner
  </div>
</div>

<div class="toc">
  <h1>Contents</h1>
  <ol>{''.join(toc_entries)}</ol>
  <p style="margin-top:22pt;color:#555f6e">
    Read chapters 1 and 2 before the viva — everyone, not just the person who
    wrote that part. Chapter 1 explains every file in plain language; chapter 2
    is the expected questions with answers.
  </p>
</div>

{''.join(chapters)}
</body></html>"""

    os.makedirs("docs", exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8") as fh:
        fh.write(html)
    return len(chapters)


def to_pdf(chrome):
    out_abs = os.path.abspath(OUT_PDF)
    src_abs = os.path.abspath(OUT_HTML).replace("\\", "/")

    subprocess.run(
        [
            chrome, "--headless", "--disable-gpu", "--no-sandbox",
            "--no-pdf-header-footer",
            f"--print-to-pdf={out_abs}",
            f"file:///{src_abs}",
        ],
        check=True,
        capture_output=True,
        timeout=180,
    )
    return out_abs


def main():
    count = build_html()
    print(f"Built HTML from {count} documents.")

    chrome = find_chrome()
    if not chrome:
        print("\nNo Chrome or Edge found, so the PDF step was skipped.")
        print(f"The HTML is at {OUT_HTML} -- open it and use Print > Save as PDF.")
        return 1

    path = to_pdf(chrome)
    size_kb = os.path.getsize(path) / 1024
    print(f"PDF written to {OUT_PDF}  ({size_kb:.0f} KB)")
    os.remove(OUT_HTML)
    return 0


if __name__ == "__main__":
    sys.exit(main())
