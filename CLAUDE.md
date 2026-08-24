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

6. **A change is not delivered until it is on `main` and the Pages build is
   green.** A feature branch is work in progress, not a release: pushing one
   changes nothing on my phone. So finish the job — commit, fast-forward
   `main`, push it, and confirm the "pages build and deployment" run succeeded
   for that commit — and don't stop at the branch and report "pushed", which
   reads as "live" and is not. Do this without asking; ask only if the merge
   is not a clean fast-forward, or a check is failing.

   If a session is configured to develop on a named branch, that governs where
   the *work* happens, not whether it ships. Say so at the first commit — "this
   is on a branch, it goes live when it reaches `main`" — and get the go-ahead
   once, not per change.
