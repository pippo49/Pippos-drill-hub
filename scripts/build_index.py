#!/usr/bin/env python3
"""Generate the repo-root landing page (index.html) that links to every drill.

The hub has a manifest (home-screen icon + standalone display) but deliberately
NO service worker. Its canonical URL is the directory root, so a worker would
need directory scope — and a directory-scoped worker takes control of the app
pages too, then declines to serve them, breaking the apps' own offline support.
Verified in a browser: the Spanish trainer ended up controlled by the hub worker.
The apps' offline support matters more than the hub's, so the hub stays online-only.

Counts are read from the actual decks so the page cannot drift — re-run this
after adding entries or a new app:
    python3 scripts/build_index.py

NOTE: this creates a NEW page. It never renames or copies an app to
index.html — see the HARD RULE in coding-drills/CLAUDE.md; the apps keep their
own distinct filenames, which are their GitHub Pages URLs.
"""
import json, os, re, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LANGUAGE_APPS = [
    # (html file, vocab json, title, subtitle, accent, ink, badge)
    # `badge` must match the app's own icon glyph so the two are recognisably
    # the same app on the home screen.
    ("polish_trainer.html",  "vocab.json",    "Polish",  "polski → deutsch",   "#22304a", "#ffffff", "PL"),
    ("spanish_trainer.html", "vocab_es.json", "Spanish", "español → english",  "#7a2331", "#ffffff", "ES"),
    ("italian_trainer.html", "vocab_it.json", "Italian", "italiano → english", "#0e5c3a", "#f4f1e4", "IT"),
    ("latin_trainer.html",   "vocab_la.json", "Latin",   "latina → english",   "#5c1f2e", "#f0d9a8", "LA"),
]

CODING_APPS = [
    ("python-drill.html", "pyDrill",   "Python",     "#1b1d27", "#ffd43b", "PY"),
    ("bash-drill.html",   "bashDrill", "Bash / CLI", "#0e1420", "#37e08a", "$_"),
    ("cpp-drill.html",    "cppDrill",  "C++17",      "#1b1d27", "#5c9fe0", "C++"),
]


def language_stats(html_file, vocab_file):
    data = json.load(open(os.path.join(ROOT, "language-trainers", vocab_file), encoding="utf-8"))
    entries = data["entries"]
    source = open(os.path.join(ROOT, "language-trainers", html_file), encoding="utf-8")
    # MODE_LABELS is the authoritative list of drill types for each app.
    m = re.search(r"const MODE_LABELS = \[(.*?)\];", source.read(), re.S)
    modes = re.findall(r'\[\s*"([a-z_]+)"', m.group(1))
    lessons = {e.get("lesson") for e in entries if e.get("lesson")}
    return {"entries": len(entries), "modes": len(modes), "lessons": len(lessons)}


def coding_stats(html_file):
    src = open(os.path.join(ROOT, "coding-drills", html_file), encoding="utf-8").read()
    key = "const DECK_DATA = "
    rest = src[src.index(key) + len(key):]
    deck, _ = json.JSONDecoder().raw_decode(rest, rest.index("{"))
    return {"topics": len(deck["topics"]), "cards": len(deck["cards"])}


def card(href, title, subtitle, stats, accent, ink, badge):
    chips = "".join(f"<span>{html.escape(s)}</span>" for s in stats)
    return f"""      <a class="card" href="{href}">
        <span class="badge" style="background:{accent};color:{ink}">{html.escape(badge)}</span>
        <span class="body">
          <span class="title">{html.escape(title)}</span>
          <span class="sub">{html.escape(subtitle)}</span>
          <span class="stats">{chips}</span>
        </span>
        <span class="go" aria-hidden="true">→</span>
      </a>"""


def build():
    lang_cards, total_entries = [], 0
    for f, v, title, sub, accent, ink, badge in LANGUAGE_APPS:
        s = language_stats(f, v)
        total_entries += s["entries"]
        lang_cards.append(card(
            f"language-trainers/{f}", title, sub,
            [f"{s['entries']:,} words", f"{s['modes']} drills", f"{s['lessons']} lessons"],
            accent, ink, badge))

    code_cards, total_cards = [], 0
    for f, title, sub, accent, ink, badge in CODING_APPS:
        s = coding_stats(f)
        total_cards += s["cards"]
        code_cards.append(card(
            f"coding-drills/{f}", title, sub,
            [f"{s['cards']} cards", f"{s['topics']} topics"],
            accent, ink, badge))

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Drill Hub">
<meta name="theme-color" content="#f8f3e8">
<link rel="manifest" href="./hub-manifest.json">
<link rel="apple-touch-icon" href="./icons/hub-icon-192.png">
<meta name="description" content="Vocabulary and coding drills — self-contained trainers that work offline.">
<title>Pippo's Drill Hub</title>
<style>
  :root {{
    --paper:#f8f3e8; --ink:#1a1a1a; --muted:#5a4a3a; --line:#d9cfba; --accent:#b43c28;
  }}
  * {{ box-sizing:border-box; }}
  html {{ color-scheme:light only; background:var(--paper); -webkit-text-size-adjust:100%; }}
  html,body {{ margin:0; padding:0; }}
  body {{
    background:var(--paper); color:var(--ink);
    font-family:"EB Garamond", Georgia, "Times New Roman", serif;
    min-height:100vh; padding:32px 20px calc(40px + env(safe-area-inset-bottom));
    line-height:1.5;
  }}
  .wrap {{ max-width:720px; margin:0 auto; }}
  header {{ border-bottom:1px solid var(--ink); padding-bottom:16px; margin-bottom:8px; }}
  h1 {{ margin:0; font-size:2.4rem; font-weight:500; font-style:italic; letter-spacing:-0.01em; }}
  h1 .dot {{ color:var(--accent); font-style:normal; }}
  .tagline {{ margin-top:10px; font-size:0.95rem; color:var(--muted); font-style:italic; }}
  h2 {{
    font-size:0.78rem; text-transform:uppercase; letter-spacing:0.14em;
    color:var(--muted); font-weight:600; font-family:system-ui,-apple-system,sans-serif;
    margin:32px 0 12px;
  }}
  .grid {{ display:grid; gap:10px; }}
  .card {{
    display:flex; align-items:center; gap:14px;
    padding:14px 16px; border:1px solid var(--line); border-radius:10px;
    background:#fffdf7; text-decoration:none; color:inherit;
    transition:border-color .15s ease, transform .15s ease;
  }}
  .card:hover, .card:focus-visible {{ border-color:var(--ink); transform:translateY(-1px); outline:none; }}
  .card:active {{ transform:translateY(0); }}
  .badge {{
    flex:0 0 46px; height:46px; border-radius:9px;
    display:flex; align-items:center; justify-content:center;
    font-family:system-ui,-apple-system,sans-serif; font-weight:700;
    font-size:0.95rem; letter-spacing:0.02em;
  }}
  .body {{ flex:1 1 auto; min-width:0; display:flex; flex-direction:column; gap:2px; }}
  .title {{ font-size:1.25rem; font-weight:500; }}
  .sub {{ font-size:0.9rem; color:var(--muted); font-style:italic; }}
  .stats {{ display:flex; flex-wrap:wrap; gap:6px; margin-top:5px; }}
  .stats span {{
    font-family:system-ui,-apple-system,sans-serif; font-size:0.7rem;
    color:var(--muted); border:1px solid var(--line); border-radius:99px;
    padding:2px 8px; white-space:nowrap;
  }}
  .go {{ flex:0 0 auto; color:var(--muted); font-size:1.2rem; }}
  footer {{
    margin-top:36px; padding-top:16px; border-top:1px solid var(--line);
    font-size:0.85rem; color:var(--muted); font-style:italic;
  }}
  footer p {{ margin:0 0 8px; }}
  @media (max-width:400px) {{
    body {{ padding:24px 14px; }}
    h1 {{ font-size:2rem; }}
    .badge {{ flex-basis:40px; height:40px; font-size:0.85rem; }}
  }}
</style>
</head>
<body>
<div class="wrap">

  <header>
    <h1>Drill Hub<span class="dot">·</span></h1>
    <div class="tagline">{total_entries:,} vocabulary entries and {total_cards} coding cards — all offline-capable.</div>
  </header>

  <h2>Language trainers</h2>
  <div class="grid">
{chr(10).join(lang_cards)}
  </div>

  <h2>Coding drills</h2>
  <div class="grid">
{chr(10).join(code_cards)}
  </div>

  <footer>
    <p>Each app is a single self-contained page. Open one while online and it keeps
       working offline; add it to your home screen for its own icon.</p>
    <p>Progress is stored per app in this browser — use each app's Export button to back it up.</p>
  </footer>

</div>
</body>
</html>
"""
    out = os.path.join(ROOT, "index.html")
    open(out, "w", encoding="utf-8").write(page)
    print(f"wrote {out}")
    print(f"  {len(LANGUAGE_APPS)} language trainers · {total_entries:,} entries")
    print(f"  {len(CODING_APPS)} coding drills · {total_cards} cards")


if __name__ == "__main__":
    build()
