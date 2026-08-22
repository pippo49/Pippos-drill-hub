# Pippos-drill-hub

Self-contained single-file HTML drill apps, served from GitHub Pages and used
from the iOS home screen. Two projects, each with its own `CLAUDE.md`:

| Directory | What | Read first |
|---|---|---|
| `language-trainers/` | 8 vocabulary trainers (Polish, Spanish, European + Brazilian Portuguese, Italian, French, Latin, medical terminology) | `language-trainers/CLAUDE.md` |
| `coding-drills/` | 5 coding trainers (pyDrill, bashDrill, cppDrill, gitDrill, sqlDrill) | `coding-drills/CLAUDE.md` |

**Read the CLAUDE.md for the directory you are changing before you change
anything in it.** Each carries the build commands, the validation steps and the
per-app conventions, and each points to the `HANDOFF_*.md` files that explain
why the tricky parts are the way they are. This file is only the map.

## Rules that apply everywhere

1. **Never rename or copy an app to `index.html`.** A basename collision
   destroyed a build once. Each app's filename *is* its Pages URL, and people
   have those on their home screens.

2. **Several apps are GENERATED. Never hand-edit them** — edit the generator,
   then re-run it. A hand edit is silently overwritten on the next run.

   | Generated | From | By |
   |---|---|---|
   | `coding-drills/git-drill.html`, `sql-drill.html` | `python-drill.html` | `tools/make_drill.py` |
   | `language-trainers/medical_trainer.html` | `latin_trainer.html` | `scripts/make_medical_trainer.py` |
   | `language-trainers/portuguese_trainer.html`, `brazilian_trainer.html` | `spanish_trainer.html` | `scripts/make_portuguese_trainer.py` |

   Most `vocab*.json` decks are generated too — check the project CLAUDE.md
   before editing one by hand. Polish and Spanish are the hand-maintained ones.

3. **Validate before handing anything back.** Every project has a validator and
   most have behavioural checks beyond it; the commands are in its CLAUDE.md. A
   passing validator is not the same as a working app — anything scaffolded from
   another app needs a rendered screenshot too, because prose strings and shared
   tables are exactly what a mechanical rename walks past.

4. **`index.html` is generated** by `scripts/build_index.py`. Re-run it after
   changing any deck so the landing-page counts stay honest.

5. **Deployment is a push to `main`.** Committing an updated `*.html` there is
   the release — there is no build step and no staging.
