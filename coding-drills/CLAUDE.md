# Coding drills — pyDrill / bashDrill / cppDrill

Three self-contained single-file HTML trainers (PWA, GitHub Pages, iOS Safari,
English, intermediate). All share the same engine (v1.5). Owner is token-conscious:
lead with results, keep responses concise, batch-and-validate before delivering.

## Files
- `python-drill.html` — pyDrill, PROG_KEY `pydrill_progress_v1`
- `bash-drill.html`   — bashDrill, PROG_KEY `bashdrill_progress_v1`
- `cpp-drill.html`    — cppDrill, PROG_KEY `cppdrill_progress_v1`
- `tools/validate.js` — jsdom full-flow probe (see Validation)
- `<name>-sw.js` + `<name>-manifest.json` + `icons/<name>-icon-{192,512}.png` — offline support (PWA), one set per app (see below)

## Offline support (PWA)

Each app registers its own service worker via a snippet appended inside its existing single `<script>` block (jsdom's `runScripts: 'dangerously'` handles multiple `<script>` tags fine, unlike the Python trainers' validator, but keeping registration in the same block matches that pattern for consistency).

- Registration scope is the page's own filename (e.g. `{ scope: './python-drill.html' }`) so each app's worker only controls itself, despite all three living in the same directory.
- Strategy: network-first with cache fallback — every fetch tries the network first and caches the response, falling back to cache (then the precached app page) only when offline.
- `CACHE_NAME` (e.g. `python-drill-v1`) is manually versioned; bump it to force-purge stale cached assets on next activation.
- jsdom has no Service Worker API, so `'serviceWorker' in navigator` is false under `tools/validate.js` — the registration code never runs during validation, no stub needed.
- Service workers need HTTP(S), not `file://` — test with a local server, not by opening the HTML directly.

## HARD RULES
1. NEVER rename or copy any app to `index.html` — a basename collision once
   destroyed a build. The distinct filenames are the Pages URLs.
2. Commit every working build. The repo is the backup.
3. Every deck edit follows Validation below before it is considered done.

## Engine (v1.5, identical across apps)
Five drill modes: predict / fill / complexity / recall / confusable (bash has no
complexity). Graded matching: exact/close/wrong, OSA typo tolerance,
exception-aware output grading, Big-O grading. Weighted spaced repetition
(unseen=12, streak decay), round + review loop ("Re-drill N missed"), "Teach me
this" reveal on every card, All/None quick-selects, device-aware help text,
guarded localStorage (LS_AVAILABLE).

v1.5 additions (2026-07-15, ported from the Polish trainer):
- Progress records: `{seen, correct, wrong, streak, last}` per qid.
- Rolling 200-answer history under reserved key `__history` inside the PROG_KEY
  object — any code iterating progress MUST skip this key.
- Home-screen Progress card: overall stats + per-topic mastery bars
  (mastery = coverage × accuracy). Functions: `statsForUnits`,
  `allUnitsForTopic`, `renderProgressCard`.

Engine changes must be applied identically to all three files (the engine JS is
byte-identical apart from branding/PROG_KEY; patch via exact-match string
replacement on all three).

## Deck conventions
- Cards live in `const DECK_DATA` inside each HTML file. Every card carries a
  teaching summary.
- pyDrill predict prompt: `$ python` — exact stdout or exception name.
- bashDrill predict prompt: `$ bash` — EXACT stdout; filesystem fixtures stated
  as a comment on snippet line 1 (`# dir contains: ...`).
- cppDrill predict prompt: `$ g++ -std=c++17 && ./a.out` — exact stdout or the
  literal string `compile error`. No UB as an expected answer; UB is taught via
  confusables. Cross-reference: c5-003 (vector copy is deep) mirrors pyDrill
  t1-001 (list aliasing).

## Validation (run after ANY edit, per changed file)
1. `node --check` on the extracted `<script>` body.
2. `npm install` once, then `node tools/validate.js <file>.html` — full flow:
   starts a round, answers every unit across all modes, checks summary,
   wrong counts, history cap, and the populated Progress card.
3. jsdom gotchas (already handled in validate.js): construct JSDOM with
   `url: 'https://localhost/'` or localStorage throws; detect the summary via
   the `.card.summary` element, never `body.textContent` (it includes the
   inline script source, which contains UI strings).

## Deck state (2026-07-15)
- pyDrill: 12/12 topics, 329 cards / 381 units
  (215 predict · 62 fill · 58 confusable · 28 recall · 18 complexity).
  t1 Mutability 14 · t2 Truthiness/None 28 · t3 Slicing 27 · t4 Dicts/sets 33 ·
  t5 Comprehensions 30 · t6 Iteration 31 · t7 Args/defaults 31 · t8 Scope 28 ·
  t9 Decorators 29 · t10 Exceptions 31 · t11 OOP 24 · t12 Stdlib 23
- bashDrill: 14/14 topics, 192 cards / 192 units
  (90 predict · 39 fill · 34 confusable · 29 recall).
  b1 Quoting 13 · b2 Globbing 11 · b3 Pipes/redirection 13 · b4 Exit codes 12 ·
  b5 Vars/env 16 · b6 Text processing 19 · b7 Files/permissions 18 ·
  b8 Processes 18 · b9 Tests 14 · b10 Loops 15 · b11 Networking 13 ·
  b12 Arrays 13 · b13 Arg parsing 7 · b14 Gotcha gauntlet 10
- cppDrill: 11/11 topics, 124 cards / 134 units
  (77 predict · 16 fill · 25 confusable · 10 recall · 6 complexity).
  c1 Values/refs/ptrs 9 · c2 const/init 13 · c3 Arithmetic 11 · c4 Strings/IO 9 ·
  c5 Vectors/STL 16 · c6 Functions 12 · c7 Classes/RAII 11 · c8 Inheritance 11 ·
  c9 Copies/moves 9 · c10 Templates/auto 10 · c11 Smart pointers 13

## Backlog (owner decides priority)
1. Progress export/import + reset (all three) — guards against iOS Safari
   localStorage eviction. Highest value.
2. Deck deepening: pyDrill t1/t2/t7/t8 predicts; bashDrill b13; cppDrill c9.
3. Possible new pyDrill topics: typing, dataclasses, async, regex.
