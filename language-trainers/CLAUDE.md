# Language & skill trainers

Self-contained single-file HTML vocabulary/skill trainers (PWA-style, used on iPhone via GitHub Pages). Each app = one `*.html` with the dataset inlined as `const VOCAB_DATA = {...}` + a matching editable `vocab*.json` (source of truth for data edits).

Apps in this repo:
- `polish_trainer.html` + `vocab.json` — Polish→German (reference language German). Details: `HANDOFF.md`
- `spanish_trainer.html` + `vocab_es.json` — Spanish→English. Details: `HANDOFF_ES.md`
- (PyDrill / bashDrill / cppDrill share the same engine family — same workflow applies if added here.)

## Offline support (PWA)

Each app has a matching `<name>-sw.js` service worker + `<name>-manifest.json` manifest + `icons/<name>-icon-{192,512}.png`, registered from a snippet inside the app's existing single `<script>` block (registration must stay inside that block, not a second `<script>` tag — `scripts/validate.py` extracts JS from the first `<script>` to the last `</script>`, and a second tag breaks the extraction).

- Registration uses an explicit narrow `scope` equal to the page's own filename (e.g. `{ scope: './spanish_trainer.html' }`) so each app's service worker only ever controls itself, even though both trainers' files live in the same directory.
- Strategy is network-first with cache fallback: every fetch tries the network first (and caches a fresh copy on success), falling back to the cache — and finally to the precached app page — only when the network fails (offline).
- `CACHE_NAME` is a manually-versioned string (e.g. `spanish-trainer-v1`); bump it whenever you want to force-purge old cached assets on next activation. Since the strategy is network-first, this is mostly a safety net — online users always get the latest file regardless.
- Service workers require serving over HTTP(S), not `file://` — test with a local server (e.g. `python3 -m http.server`), not by opening the HTML file directly.

## Selection filters & repeat avoidance

Three independent filters gate the question pool, each with its own `All`/`None` toggle row and its own localStorage key (`<app>_trainer_lessons` / `<app>_trainer_pos`; drill-type enablement isn't persisted): **Drill types** (`enabledModes`), **Lessons** (`enabledLessons`, `ALL_LESSONS`), and **Word forms / part of speech** (`enabledPos`, `ALL_POS`, derived from `entries.pos`, most-frequent-first). `buildPool()` ANDs all three; adding a fourth filter dimension means threading it through the same four spots: `buildPool`'s filter predicate, `selectionCanAsk`'s two call sites (`renderSelectionCount`, `selectionExhausted`), and the `renderCard` empty-state message chain.

**Gotcha**: `enabledPos` only filters things drawn from `entries` — Spanish's `ser_estar`/`por_para` special-bank modes have no `.pos` field to check (caught after shipping: selecting only "Numbers" still surfaced random Ser vs estar questions). Fixed via `specialModeAllowed(type)`, which hand-maps `ser_estar`→`enabledPos.verb` and `por_para`→`enabledPos.preposition` and is checked both in `generateQuestion` (gates whether the mode can fire at all) and in the Word-forms toggle handler (so a *currently displayed* special question gets replaced immediately if its pos is unchecked mid-question, not just on the next pick). Any future special/curated-bank drill mode needs the same explicit pos mapping — it won't fall out of the `entries`-based filtering for free.

Repeat avoidance is two-layered, in `buildPool` (and, for Spanish only, mirrored in the `ser_estar`/`por_para` special-bank branch since those draw from `VOCAB_DATA.special` instead of `entries`):
1. **Hard floor** — `NO_REPEAT_WINDOW` (8): a word can't resurface within the last 8 questions *of its own pool*, as long as the pool is big enough to still leave a choice (`Math.min(recentIds.length, pool.length - 1, NO_REPEAT_WINDOW)`). This is the part that actually matters for small pools (a single lesson, or one part-of-speech filter) — a soft multiplier alone doesn't reliably prevent short gaps once you check it against a synthetic gap simulation, because the *average* revisit gap for a fixed pool size trends toward the pool size regardless of weighting shape; only a hard exclusion moves the *minimum* gap.
2. **Soft recency decay** on top, for pools bigger than the hard window: `w *= recency / (recency + 12)` over a `recentIds` lookback capped at 40 (was `+6` / cap 20 before this was widened).

`recentIds` is the single shared, global recency log across every mode and both special banks — pushed once per successful `pickQuestion()`, id namespaces never collide (`es####` vocab ids vs `se###`/`pp###` bank ids), so mixing modes doesn't defeat the floor.

`learning_tool_pattern.md` describes the engine architecture (drill modes, graded answering, SRS weighting, review rounds, cloze UX) and my working preferences. Read it before making changes.

## Commands

Rebuild an app after editing its vocab JSON (splices compact JSON into the HTML in place):
```
python3 scripts/rebuild.py polish_trainer.html vocab.json
python3 scripts/rebuild.py spanish_trainer.html vocab_es.json
```

Validate a build (JS syntax + 400×runtime probe of every mode + data hygiene; exits 1 on failure):
```
python3 scripts/validate.py polish_trainer.html
```

**ALWAYS run rebuild + validate after any change to a vocab JSON or to the inline JS. Never hand back or commit an unvalidated build.**

To edit engine JS/CSS: edit the `*.html` directly (everything before `const VOCAB_DATA` is head/CSS; everything after the data blob is the app JS), then validate.

## Data schema (shared shape; language fields differ)

Polish entry: `pl, de, pos, id, lesson` + per-pos morphology — verbs `conjugation{ja..oni_one}` + `aspect`; adjectives `declension{m_sg_nom,f_sg_nom,n_sg_nom,nv_pl_nom}`; nouns `gender, animate?, plural, noun_decl{acc_sg,gen_sg,nom_pl,acc_pl,gen_pl}` (partial `noun_decl` allowed — drill only asks keys present).
Spanish entry: `es, en, pos, id, lesson` — verbs `conjugation{yo..ellos_ellas_ustedes}`; adjectives `declension{m_sg_nom,f_sg,m_pl,f_pl}`; nouns `gender, plural, noun_decl{article,plural}`.
Both: `cloze` = array of `{pl,de}` / `{es,en}` with the target wrapped in `{...}`; answer = the inflected in-sentence form, authored correctly and independently of any stored paradigm fields. `antonyms`/`synonyms` = arrays of entry ids, always linked in both directions.

## Conventions & policies

- Cloze batches: ~30 words/turn unless told otherwise, 2 sentences per word, mixing cases/persons/number; prioritise the lessons currently being learned; prefer a 3rd/4th sentence on a common word over a first sentence on a rare one.
- Grammar/data corrections: apply only what you are confident is right; flag uncertain items instead of guessing. **Never run blanket rule-based auto-fix sweeps over morphology** — the rules have lexical exceptions; produce a candidate-suspects list for manual review instead.
- iOS constraint: guard every `localStorage` access (feature-tested); no other browser-storage APIs.
- The two apps use distinct localStorage keys (`polish_trainer_*` / `spanish_trainer_*`) so they coexist on one device — keep it that way for any new app.
- Deployment is GitHub Pages: committing an updated `*.html` to main is the release.

## Style with me

Direct, concise, scannable; lead with the result. I'm token-conscious. I'll correct real-world errors — revise rather than hedge.
