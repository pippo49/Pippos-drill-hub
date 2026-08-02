#!/usr/bin/env python3
"""Splice rewritten "Teach me this" summaries into a drill's inline DECK_DATA.

The summaries are hand-authored prose (not generated), so this is a patcher, not
a generator: it takes {card_id: text} and rewrites only those cards' `summary`
fields, leaving every question, answer and per-question `why` untouched.

Usage:
    python3 tools/update_summaries.py <drill.html> <summaries.py>

where <summaries.py> defines SUMMARIES = {"t1-001": "...", ...}.

It refuses to run if an id is unknown or if a summary looks like it was left in
the old terse style, so a half-finished batch fails loudly instead of silently
shipping. Re-runnable: applying the same batch twice is a no-op.
"""
import importlib.util, json, os, sys

MIN_WORDS = 45          # a beginner explanation, not a one-line reminder


def load_deck(path):
    src = open(path, encoding="utf-8").read()
    key = "const DECK_DATA = "
    i = src.index(key) + len(key)
    rest = src[i:]
    deck, end = json.JSONDecoder().raw_decode(rest, rest.index("{"))
    return src, i, deck, i + end


def load_summaries(path):
    spec = importlib.util.spec_from_file_location("summaries", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.SUMMARIES


def main(html_path, summaries_path):
    src, start, deck, end = load_deck(html_path)
    new = load_summaries(summaries_path)
    by_id = {c["id"]: c for c in deck["cards"]}

    unknown = sorted(set(new) - set(by_id))
    assert not unknown, f"unknown card ids: {unknown}"

    short = sorted(cid for cid, t in new.items() if len(t.split()) < MIN_WORDS)
    assert not short, (f"these read like the old terse style (<{MIN_WORDS} words): {short}")

    blank = sorted(cid for cid, t in new.items() if not t.strip())
    assert not blank, f"empty summaries: {blank}"

    changed = 0
    for cid, text in new.items():
        if by_id[cid]["summary"] != text:
            by_id[cid]["summary"] = text
            changed += 1

    compact = json.dumps(deck, ensure_ascii=False, separators=(",", ":"))
    open(html_path, "w", encoding="utf-8").write(src[:start] + compact + src[end:])

    done = sum(1 for c in deck["cards"] if len(c["summary"].split()) >= MIN_WORDS)
    total = len(deck["cards"])
    print(f"{os.path.basename(html_path)}: updated {changed} of {len(new)} in this batch")
    print(f"  rewritten so far: {done}/{total} cards ({done*100//total}%)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
