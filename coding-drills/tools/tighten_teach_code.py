#!/usr/bin/env python3
"""Trim comment-alignment padding in "Teach me this" code examples.

The teach panel renders indented example lines in a monospace <pre class="tc">
that is ~45 characters wide on a 390px phone. Wide runs of spaces used to align
a trailing comment push lines past that for no benefit — the alignment is lost
anyway once the block has to scroll.

So: on lines that ACTUALLY overflow, shrink the run of spaces before a trailing
# or // comment, down to as few as two, but only as far as needed to fit. Lines
that already fit keep their alignment untouched.

Only whitespace between code and a comment marker is changed; no code, no prose,
no comment text. Re-runnable.

Usage: python3 tools/tighten_teach_code.py <drill.html> [...]
"""
import json, re, sys

WIDTH = 45          # monospace chars that fit in .tc at a 390px viewport
MIN_GAP = 2         # never squeeze a comment closer than this
CMT = re.compile(r"^(\s*\S.*?\S)([ ]{3,})(#|//)(.*)$")


def tighten(line):
    """line is the dedented code text; returns it possibly narrowed."""
    if len(line) <= WIDTH:
        return line
    m = CMT.match(line)
    if not m:
        return line
    code, gap, marker, rest = m.groups()
    excess = len(line) - WIDTH
    new_gap = max(MIN_GAP, len(gap) - excess)
    return f"{code}{' ' * new_gap}{marker}{rest}"


def main(paths):
    for path in paths:
        src = open(path, encoding="utf-8").read()
        key = "const DECK_DATA = "
        start = src.index(key) + len(key)
        rest = src[start:]
        deck, off = json.JSONDecoder().raw_decode(rest, rest.index("{"))
        end = start + off

        cards = lines_changed = 0
        for c in deck["cards"]:
            out, hit = [], False
            for line in c["summary"].split("\n"):
                if line.strip() and line.startswith("    "):
                    new = "    " + tighten(line[4:])
                    if new != line:
                        hit = True
                        lines_changed += 1
                    out.append(new)
                else:
                    out.append(line)
            if hit:
                c["summary"] = "\n".join(out)
                cards += 1

        over = sum(1 for c in deck["cards"] for l in c["summary"].split("\n")
                   if l.strip() and l.startswith("    ") and len(l) - 4 > WIDTH)
        compact = json.dumps(deck, ensure_ascii=False, separators=(",", ":"))
        open(path, "w", encoding="utf-8").write(src[:start] + compact + src[end:])
        print(f"{path}: narrowed {lines_changed} lines in {cards} cards; "
              f"{over} code lines still exceed {WIDTH} chars")


if __name__ == "__main__":
    main(sys.argv[1:])
