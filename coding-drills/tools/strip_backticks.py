#!/usr/bin/env python3
"""One-off: remove Markdown-style inline backticks from the "Teach me this" text.

The teach panel renders as PLAIN TEXT (esc() escapes HTML, white-space: pre-wrap),
so `foo` shows the backticks literally. Inline code is already carried by the
indented example blocks, so the backticks are stripped rather than replaced.

SKIP_IDS lists cards where a backtick is the subject matter rather than markup —
bash's legacy `cmd` command substitution — and must survive.

Usage: python3 tools/strip_backticks.py <drill.html> [...]
"""
import json, re, sys

SKIP_IDS = {"b1-003"}           # backticks ARE the syntax being taught
PAIR = re.compile(r"`([^`\n]{1,60})`")


def main(paths):
    for path in paths:
        src = open(path, encoding="utf-8").read()
        key = "const DECK_DATA = "
        start = src.index(key) + len(key)
        rest = src[start:]
        deck, off = json.JSONDecoder().raw_decode(rest, rest.index("{"))
        end = start + off

        changed = 0
        for c in deck["cards"]:
            if c["id"] in SKIP_IDS:
                continue
            new = PAIR.sub(r"\1", c["summary"])
            if new != c["summary"]:
                c["summary"] = new
                changed += 1

        left = sum(c["summary"].count("`") for c in deck["cards"])
        compact = json.dumps(deck, ensure_ascii=False, separators=(",", ":"))
        open(path, "w", encoding="utf-8").write(src[:start] + compact + src[end:])
        print(f"{path}: stripped in {changed} cards; {left} backtick chars remain")


if __name__ == "__main__":
    main(sys.argv[1:])
