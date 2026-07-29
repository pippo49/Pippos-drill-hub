# Pippos-drill-hub
Drills for various skills. Self-contained single-file HTML apps (PWA-style, used via GitHub Pages / iOS home-screen).

**Landing page:** https://pippo49.github.io/Pippos-drill-hub/ lists every drill with live counts.
It is generated — after changing a deck, re-run `python3 scripts/build_index.py` so the numbers stay honest.

## Projects

- **`language-trainers/`** — Polish→German, Spanish→English, Latin→English and Italian→English vocabulary trainers. See `language-trainers/CLAUDE.md`.
- **`coding-drills/`** — pyDrill / bashDrill / cppDrill coding practice trainers. See `coding-drills/CLAUDE.md`.

Each project directory has its own `CLAUDE.md` with build/validate commands and conventions — read it before making changes there.

**Note:** these apps moved into subdirectories in July 2026 (previously flat at repo root), so GitHub Pages / home-screen URLs changed — re-add any bookmarked shortcuts to `language-trainers/spanish_trainer.html` etc.
