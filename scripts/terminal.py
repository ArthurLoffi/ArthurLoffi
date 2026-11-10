#!/usr/bin/env python3
"""Generates assets/terminal.svg — an animated terminal for the profile README.

Pure SVG + CSS (no JavaScript), so it animates when GitHub renders it as an image.
Edit SCRIPT below and run:  python3 scripts/terminal.py
"""
from pathlib import Path
from xml.sax.saxutils import escape

# ── Theme (Tokyo Night) ────────────────────────────────────────────────
BG, BAR, BORDER = "#1a1b26", "#16161e", "#2f334d"
FG, DIM = "#c0caf5", "#565f89"
GREEN, BLUE, PURPLE = "#9ece6a", "#7aa2f7", "#bb9af7"
CYAN, ORANGE, YELLOW, RED = "#7dcfff", "#ff9e64", "#e0af68", "#f7768e"

# ── Layout ────────────────────────────────────────────────────────────
FONT_SIZE = 14
CW = 8.4            # forced width of each character (textLength keeps it exact)
LH = 22             # line height
PAD_X, TOP = 24, 64 # text origin
WIDTH = 820

TYPE_SPEED = 0.055  # seconds per typed character
HOLD = 6.0          # seconds the finished screen stays before restarting

USER = [("arthur", GREEN), ("@", DIM), ("joinville", BLUE), (":", DIM), ("~", PURPLE), ("$ ", FG)]


def s(text, color=FG):
    return (text, color)


def kv(key, value, comma=True, raw=False):
    val = [s(value if raw else f'"{value}"', ORANGE if raw else GREEN)]
    return [s("  "), s(f'"{key}"', CYAN), s(": ", FG), *val, s("," if comma else "", FG)]


def arr(key, items, comma=True):
    parts = [s("  "), s(f'"{key}"', CYAN), s(": [", FG)]
    for i, it in enumerate(items):
        parts.append(s(f'"{it}"', GREEN))
        if i < len(items) - 1:
            parts.append(s(", ", FG))
    parts.append(s("]" + ("," if comma else ""), FG))
    return parts


# Each step: ("cmd", "typed command") or ("out", [segments]) or ("gap", px)
SCRIPT = [
    ("cmd", "whoami"),
    ("out", [s("Arthur", YELLOW), s(" · Software Engineering Student · Joinville, SC, Brazil", FG)]),
    ("gap", 8),
    ("cmd", "cat about.json"),
    ("out", [s("{", FG)]),
    ("out", kv("role", "Software Engineering Student")),
    ("out", kv("semester", "2", raw=True)),
    ("out", arr("focus", ["automation", "internal tools", "backend"])),
    ("out", arr("stack", ["TypeScript", "React", "Go"])),
    ("out", arr("infra", ["Docker", "PostgreSQL", "MongoDB"])),
    ("out", kv("curious_about", "how software works under the hood", comma=False)),
    ("out", [s("}", FG)]),
    ("gap", 8),
    ("cmd", "ls ~/projects"),
    ("out", [s("url-shortener-go  ", BLUE), s("rest-api-go  ", BLUE), s("task-queue  ", BLUE),
             s("system-monitor  ", BLUE), s("asset-control", BLUE)]),
    ("gap", 8),
    ("cmd", "echo $STATUS"),
    ("out", [s("● ", GREEN), s("Open to connect — let's build something together!", FG)]),
    ("gap", 8),
    ("cmd", None),  # final idle prompt with blinking cursor
]


# ── Build the timeline ────────────────────────────────────────────────
def build_with_pauses():
    t = 0.6
    y = TOP
    items = []
    prompt_len = sum(len(x[0]) for x in USER)
    prev = None
    for kind, val in SCRIPT:
        if kind == "gap":
            y += val
            continue
        if kind == "cmd":
            if prev == "out":
                t += 0.9
            cmd = val or ""
            appear = t
            start = t + (0.45 if cmd else 0)
            end = start + len(cmd) * TYPE_SPEED
            items.append(dict(kind="cmd", y=y, segs=USER + ([s(cmd, FG)] if cmd else []),
                              appear=appear, start=start, end=end, col=prompt_len, n=len(cmd),
                              final=val is None))
            t = end + 0.3
        else:
            items.append(dict(kind="out", y=y, segs=val, appear=t))
            t += 0.06
        prev = kind
        y += LH
    return items, y, t


def text_el(segs, y):
    out = [f'<text y="{y}" xml:space="preserve">']
    col = 0
    for txt, color in segs:
        if txt.strip():
            x = PAD_X + col * CW
            out.append(f'<tspan x="{x:.1f}" fill="{color}" textLength="{len(txt) * CW:.1f}" '
                       f'lengthAdjust="spacing">{escape(txt)}</tspan>')
        col += len(txt)
    out.append("</text>")
    return "".join(out)


def main():
    items, bottom, t_end = build_with_pauses()
    total = t_end + HOLD
    pct = lambda sec: f"{min(sec / total * 100, 100):.3f}%"
    fade_out_start = pct(total - 0.6)
    fade_out_end = pct(total - 0.2)

    height = bottom + 18
    css, body = [], []

    for i, it in enumerate(items):
        a = it["appear"]
        css.append(
            f"@keyframes v{i}{{0%,{pct(max(a - 0.001, 0))}{{opacity:0}}{pct(a)},{fade_out_start}{{opacity:1}}"
            f"{fade_out_end},100%{{opacity:0}}}}.v{i}{{animation:v{i} {total:.2f}s linear infinite}}"
        )
        line = [f'<g class="v{i}">', text_el(it["segs"], it["y"])]
        if it["kind"] == "cmd":
            x0 = PAD_X + it["col"] * CW
            w = it["n"] * CW
            cy = it["y"] - FONT_SIZE + 2
            if it["final"]:
                line.append(f'<rect class="blink" x="{x0:.1f}" y="{cy}" width="{CW:.1f}" height="{FONT_SIZE + 3}" fill="{FG}"/>')
            else:
                # overlay (bg + cursor) slides right one character at a time, revealing the command
                st, en = it["start"], it["end"]
                hide = en + 0.3
                css.append(
                    f"@keyframes t{i}{{0%,{pct(st)}{{transform:translateX(0);animation-timing-function:steps({it['n']},end)}}"
                    f"{pct(en)}{{transform:translateX({w:.1f}px);opacity:1}}"
                    f"{pct(hide)},100%{{transform:translateX({w:.1f}px);opacity:0}}}}"
                    f".t{i}{{animation:t{i} {total:.2f}s linear infinite}}"
                )
                line.append(f'<g class="t{i}">'
                            f'<rect x="{x0:.1f}" y="{cy - 3}" width="{w + CW:.1f}" height="{LH}" fill="{BG}"/>'
                            f'<rect class="blink" x="{x0:.1f}" y="{cy}" width="{CW:.1f}" height="{FONT_SIZE + 3}" fill="{FG}"/>'
                            f'</g>')
        line.append("</g>")
        body.append("".join(line))

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" aria-label="Animated terminal: Arthur, Software Engineering Student from Joinville, SC, Brazil">
<style>
text{{font-family:'JetBrains Mono','Fira Code','SF Mono',Menlo,Consolas,'DejaVu Sans Mono','Liberation Mono',monospace;font-size:{FONT_SIZE}px}}
.title{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;font-size:13px}}
@keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
.blink{{animation:blink 1s step-end infinite}}
{chr(10).join(css)}
</style>
<defs>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="{PURPLE}" stop-opacity=".55"/>
<stop offset=".5" stop-color="{BORDER}"/>
<stop offset="1" stop-color="{CYAN}" stop-opacity=".55"/>
</linearGradient>
<clipPath id="win"><rect x="1" y="1" width="{WIDTH - 2}" height="{height - 2}" rx="12"/></clipPath>
</defs>
<rect x="1" y="1" width="{WIDTH - 2}" height="{height - 2}" rx="12" fill="{BG}"/>
<g clip-path="url(#win)">
<rect x="0" y="0" width="{WIDTH}" height="38" fill="{BAR}"/>
<line x1="0" y1="38" x2="{WIDTH}" y2="38" stroke="{BORDER}"/>
</g>
<circle cx="22" cy="19" r="6" fill="{RED}"/>
<circle cx="42" cy="19" r="6" fill="{YELLOW}"/>
<circle cx="62" cy="19" r="6" fill="{GREEN}"/>
<text class="title" x="{WIDTH / 2}" y="23" text-anchor="middle" fill="{DIM}">arthur@joinville: ~ — zsh</text>
{chr(10).join(body)}
<rect x="1" y="1" width="{WIDTH - 2}" height="{height - 2}" rx="12" fill="none" stroke="url(#edge)" stroke-width="1.5"/>
</svg>
'''
    out = Path(__file__).resolve().parent.parent / "assets" / "terminal.svg"
    out.parent.mkdir(exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out} ({len(svg)} bytes, {total:.1f}s loop, {height}px tall)")


if __name__ == "__main__":
    main()
