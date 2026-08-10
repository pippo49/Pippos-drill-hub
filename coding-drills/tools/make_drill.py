#!/usr/bin/env python3
"""Generate git-drill.html / sql-drill.html from python-drill.html.

Same idea as language-trainers/scripts/make_medical_trainer.py: the new apps are
GENERATED from an existing one so engine fixes keep flowing to them. Edit this
script, never the generated HTML.

Only five things are per-app: branding (title, logo, manifest, icon, service
worker), PROG_KEY, MODE_LABELS, the predict prompt/label, and the deck. The
engine JS is byte-identical to python-drill.html everywhere else, which is what
keeps a fix made in pyDrill flowing to both.

    python3 tools/make_drill.py            # builds both
    python3 tools/make_drill.py git        # just one
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CD = os.path.join(HERE, "..")
BASE = "python-drill.html"

# gitDrill has no predict-output or complexity: git's answer to "what does this
# print" is verbose, environment-dependent status text, and nothing here has a
# meaningful cost curve. It gets command / history / danger instead.
GIT_MODES = [
    ("command", "Goal → command"),
    ("history", "History after"),
    ("danger", "Danger"),
    ("fill", "Fill the flag"),
    ("confusable", "Which fits"),
    ("recall", "Recall"),
]

# sqlDrill keeps predict-output -- a query over a fixed table HAS one right
# answer -- and adds rows-out. No complexity: query cost is an optimiser
# question, drilled through the index topic instead of a Big-O guess.
SQL_MODES = [
    ("predict", "Predict result"),
    ("rows", "Rows out"),
    ("fill", "Fill the blank"),
    ("confusable", "Which fits"),
    ("recall", "Recall"),
]

APPS = {
    "git": {
        "slug": "git-drill",
        "title": "gitDrill",
        "logo": 'git<b>Drill</b>',
        "prog_key": "gitdrill_progress_v1",
        "modes": GIT_MODES,
        "deck": "git_deck.json",
        # unused (no predict cards) but kept coherent for anyone who adds one
        "prompt": "$ git",
        "predict_lbl": "What does this print? (exact)",
    },
    "sql": {
        "slug": "sql-drill",
        "title": "sqlDrill",
        "logo": 'sql<b>Drill</b>',
        "prog_key": "sqldrill_progress_v1",
        "modes": SQL_MODES,
        "deck": "sql_deck.json",
        "prompt": "$ psql",
        # The deck contains nulls and booleans, so the label has to state how
        # psql prints them or the answer becomes a guess about formatting.
        "predict_lbl": "Rows in order, one per line \u2014 | between columns, NULL, t/f",
    },
}


def sub(src, name, old, new):
    assert src.count(old) == 1, f"{name}: anchor not found exactly once: {old[:70]!r}"
    return src.replace(old, new)


def build(key):
    cfg = APPS[key]
    src = open(os.path.join(CD, BASE), encoding="utf-8").read()
    slug = cfg["slug"]

    # --- branding -----------------------------------------------------------
    src = sub(src, key, '<meta name="apple-mobile-web-app-title" content="PyDrill">',
              f'<meta name="apple-mobile-web-app-title" content="{cfg["title"]}">')
    src = sub(src, key, '<link rel="manifest" href="./python-drill-manifest.json">',
              f'<link rel="manifest" href="./{slug}-manifest.json">')
    src = sub(src, key, '<link rel="apple-touch-icon" href="./icons/python-drill-icon-192.png">',
              f'<link rel="apple-touch-icon" href="./icons/{slug}-icon-192.png">')
    src = sub(src, key, "<title>PyDrill</title>", f"<title>{cfg['title']}</title>")
    src = sub(src, key, '<div class="logo">py<b>Drill</b></div>',
              f'<div class="logo">{cfg["logo"]}</div>')
    src = sub(src, key, 'var PROG_KEY = "pydrill_progress_v1";',
              f'var PROG_KEY = "{cfg["prog_key"]}";')
    src = sub(src, key,
              "navigator.serviceWorker.register('./python-drill-sw.js', { scope: './python-drill.html' })",
              f"navigator.serviceWorker.register('./{slug}-sw.js', {{ scope: './{slug}.html' }})")

    # --- predict prompt + label --------------------------------------------
    src = sub(src, key,
              """codeHtml='<pre class="code"><span class="prompt">$ python</span>\\n'+esc(u.item.code)+'</pre>';
    lbl="What does this print? (or name the exception)"; multiline=true;""",
              f"""codeHtml='<pre class="code"><span class="prompt">{cfg["prompt"]}</span>\\n'+esc(u.item.code)+'</pre>';
    lbl="{cfg["predict_lbl"]}"; multiline=true;""")

    # --- drill modes --------------------------------------------------------
    old_modes = re.search(r"var MODE_LABELS = \[.*?\];", src, re.S).group(0)
    new_modes = ("var MODE_LABELS = [\n" +
                 "".join(f'  ["{m}","{lbl}"],\n' for m, lbl in cfg["modes"]).rstrip(",\n") +
                 "\n];")
    src = sub(src, key, old_modes, new_modes)

    # --- deck ---------------------------------------------------------------
    deck = json.load(open(os.path.join(HERE, cfg["deck"]), encoding="utf-8"))
    blob = json.dumps(deck, ensure_ascii=False, separators=(",", ":"))
    old_deck = re.search(r"const DECK_DATA = \{.*?\};\n", src, re.S).group(0)
    src = sub(src, key, old_deck, "const DECK_DATA = " + blob + ";\n")

    out = os.path.join(CD, f"{slug}.html")
    open(out, "w", encoding="utf-8").write(src)
    cards = len(deck["cards"])
    return f"{slug}.html  {cards} cards, {len(deck['topics'])} topics, {len(cfg['modes'])} modes"


def main():
    which = sys.argv[1:] or list(APPS)
    for k in which:
        print(build(k))


if __name__ == "__main__":
    main()
