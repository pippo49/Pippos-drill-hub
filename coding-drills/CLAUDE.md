# Coding drills — pyDrill / bashDrill / cppDrill / gitDrill / sqlDrill

Five self-contained single-file HTML trainers (PWA, GitHub Pages, iOS Safari,
English, intermediate). All share the same engine (v1.6). Owner is token-conscious:
lead with results, keep responses concise, batch-and-validate before delivering.

## Files
- `python-drill.html` — pyDrill, PROG_KEY `pydrill_progress_v1`
- `bash-drill.html`   — bashDrill, PROG_KEY `bashdrill_progress_v1`
- `cpp-drill.html`    — cppDrill, PROG_KEY `cppdrill_progress_v1`
- `git-drill.html`    — gitDrill, PROG_KEY `gitdrill_progress_v1` — **generated**
- `sql-drill.html`    — sqlDrill, PROG_KEY `sqldrill_progress_v1` — **generated**
- `tools/validate.js` — jsdom full-flow probe (see Validation)
- `tools/check_accept.js` — accept-list sanity (see Engine v1.6)
- `tools/verify_sql.py` — runs every sqlDrill answer against real PostgreSQL
- `tools/make_drill.py` — generates git-drill/sql-drill from python-drill
- `tools/build_deck.py` + `tools/git_deck.py` + `tools/sql_deck.py` — curated decks
- `tools/patch_engine_v16.py` — the v1.6 engine additions
- `tools/patch_hardest.py` — adds the hardest-questions round to py/bash/cpp (re-runnable)
- `tools/check_hardest.js` — jsdom regression test for that round
- `tools/update_summaries.py` — splices rewritten `summary` text into inline DECK_DATA
- `tools/strip_backticks.py` — one-off Markdown-backtick cleanup (see Teach panel)
- `tools/tighten_teach_code.py` — narrows comment padding on overflowing code lines
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
4. **Never hand-edit `git-drill.html` or `sql-drill.html`.** They are generated
   by `tools/make_drill.py` from `python-drill.html`, so an engine fix made in
   pyDrill flows to them on the next run — and a hand edit is silently lost.
   Edit the generator, the deck, or python-drill.html.

## Engine (v1.6, identical across apps)
Drill modes: predict / fill / complexity / recall / confusable, plus command /
history / danger / rows added in v1.6. Which of them an app OFFERS is
MODE_LABELS, which is per-app config. Graded matching: exact/close/wrong, OSA typo tolerance,
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

Engine changes must be applied identically to all five files (the engine JS is
byte-identical apart from branding/PROG_KEY/MODE_LABELS/predict prompt; patch via
exact-match string replacement on all five). git-drill and sql-drill pick fixes
up by re-running `tools/make_drill.py`.

## gitDrill and sqlDrill: same engine, different questions

Neither is a programming language, so "run this, what does it print?" does not
fit. Both are **generated from `python-drill.html`** by `tools/make_drill.py`,
which swaps only branding, PROG_KEY, MODE_LABELS, the predict prompt/label and
the deck. Everything else is byte-identical, which is what keeps the engine
shared.

**gitDrill** — git's unit of knowledge is a state transition, not output.
`git status` is verbose and environment-dependent, so it makes a useless answer
key. Modes: **Goal → command** (told the outcome, type the command),
**History after** (a commit graph plus a command, list the resulting commits),
**Danger** (safe / recoverable via reflog / gone for good), Fill the flag,
Which fits, Recall. No predict-output, no complexity.

- Command style is **modern** — answers key on `switch`/`restore` with the
  `checkout` spelling in every accept-list, because that split is exactly what
  git made to stop `checkout` meaning three unrelated things.
- History answers are letter-labelled commits, newest first, with an **ASCII
  apostrophe** marking a rewritten commit (`E' D' C B A`). Typing an ASCII graph
  on a phone is unusable, and a typographic prime (′) is unreachable from a
  phone keyboard — that was caught in a browser after the label and the answers
  disagreed about which character to use.
- The Danger scale's middle level carries the real lesson: almost nothing
  *committed* is ever lost (reflog), and anything never committed has no safety
  net at all. `reset --hard` is rated by what is uncommitted, not by the reset.

**sqlDrill** — PostgreSQL. Modes: **Predict result** (tables as a fixture, type
the rows), **Rows out** (one number — join fan-out, LEFT with no match, NULL
matching nothing), Fill the blank, Which fits, Recall.

**Every sqlDrill predict and rows answer is checked by a real PostgreSQL 16
server**, not worked out by hand — `tools/verify_sql.py`. `SETUP` in
`sql_deck.py` holds the DDL behind each ASCII fixture, and each query runs in a
fresh clone of it, so mutating cards (`DELETE ... RETURNING`, `CREATE TEMP
TABLE`) cannot contaminate later ones.

It enforces two things beyond the answer itself, both of which caught real
faults:

- **A multi-row predict needs a top-level ORDER BY.** The deck's own s1-002
  teaches that no ORDER BY means no order; s8-001 then depended on unordered
  output. (The check strips parenthesised groups first — the ORDER BY inside
  `OVER (...)` orders the window, not the result.)
- **The ordering must be TOTAL.** Each multi-row predict is re-run three times
  with every table physically reshuffled; if the output moves, two rows tie on
  the sort key and the card asks for something undefined. This caught s1-005,
  where Ada and Grace tie on `dept`.

The same principle retired a card: `UPDATE ... FROM` where the source matches
three times updates once from an *arbitrary* match, so "predict the total" was
unanswerable. It became a rows question — how many rows update *is* defined, and
is the actual lesson.

- There is deliberately **no write-the-whole-query mode**. Every such question
  has dozens of correct forms, so a grader loose enough to accept them would
  accept nonsense. Fill-the-blank plus accept-lists drills the same skill with a
  real answer key.
- Most predict cards select a **single column** so there is no separator to get
  wrong; the few with two carry a spaced-pipe variant in the accept-list.
- Where MySQL/SQLite genuinely differ (TRUNCATE rollback, GROUP BY leniency,
  data-modifying CTEs) the card says so — that difference IS the lesson.

## Engine v1.6 (2026-08-10)

Added for the two new drills, applied to all five files:

- **accept-lists** on any typed answer. `HEAD~1` and `HEAD^` name the same
  commit; `git restore --staged f` and `git reset f` unstage identically.
  Without this the deck must pick one spelling and mark the other wrong.
  `gradeAny` tries each and keeps the best grade.
- **fixture blocks** (`pre.fixture`) above the snippet: repo state for git,
  table contents for SQL. "How many rows come back" is unanswerable without it.
- **`command` / `history` / `rows`** text modes, and **`danger`** routed to the
  existing multiple-choice renderer (its options are a fixed three-way scale
  written by the deck builder, so it needed no new rendering).

`MODE_LABELS` is **per-app config, not engine** — it is the one place the five
files legitimately differ beyond branding. py/bash/cpp do not list the new
modes, so nothing changed on their screens.

### Deck guards worth knowing

`tools/build_deck.py` fails the build on: a summary under 45 words; **a backtick
in ANY visible field** (the app escapes text, so Markdown renders literally —
this cost 215 fixes in the teach panels once already, and the guard now covers
prompts and explanations, not just summaries); a `fill` whose answer is already
visible in its own snippet; an accept entry equal to the answer; an MC answer
index out of range; a `danger` card whose options are not the standard scale.

Code lines are capped at **44 characters and it is a build failure**, not a
warning: `pre.code` scrolls rather than breaking the page, but a browser shot of
a CTE card showed the interesting clause scrolled off mid-line on a phone.

`tools/check_accept.js` checks the two things the builder cannot: that no accept
entry is **redundant** (the real grader already accepts it, so it widens
nothing), and that grading is **not too loose** (nonsense must not grade exact;
`--soft` must not collapse into `--hard`).

**A vacuous check was written first and removed**: "does each accepted
alternative grade exact?" always passes, because `gradeAny` compares the typed
answer against the accept list, so an entry matches itself. It passed even with
a deliberately nonsensical alternative inserted. If you add a check here, break
the code on purpose and watch it fail before trusting it.

## Hardest-questions round

A second button on the home screen, beside "Start round", queues **only** the
questions you have got wrong most often. Added by `tools/patch_hardest.py`
(re-runnable) and locked down by `tools/check_hardest.js` — **run it after
touching round or selection logic.**

It exists because `weightFor` cannot concentrate practice here at all: it scores
an always-wrong unit 5 against 1 for a mastered one and 12 for an *unseen* one,
and `buildQueue` only *reorders* the selection. That buys a hard question a
slightly earlier slot in a 381-question round — it never lets you drill the hard
ones on their own.

Design decisions, the same three as the language trainers:
- **Ranking is raw wrong count.** `recordResult` books a `close` grade as a
  correct answer and never increments `wrong`, so this counts outright misses
  only. Ties break on the worse rate.
- **Scope is global**: `hardestUnits()` walks `everyUnit()`, not
  `askableUnits()`, so it **ignores the topic and drill-mode pills**. That is the
  one place in the engine that bypasses them, and it is deliberate — swapping in
  `askableUnits()` is exactly what `check_hardest.js` catches.
- **Shape is a separate round button**, reusing the round machinery.

Size is `max(8, ceil(0.10 × units attempted))`, capped at the number of units
with any mistake. Below 8 the button is disabled and says how many are needed.

`startRound(units, kind)` now takes a round kind: no argument = ordinary round
over the selection, an array = review (queued in the caller's order, since you
re-drill exactly what you missed), array + `"hardest"` = weight-shuffled like an
ordinary round. `session.review` / `session.hardest` drive the eyebrow label and
the summary heading.

## Teach panel ("Teach me this")

Every card's `summary` is a beginner-level explanation, not a terse reminder.
All 645 cards were rewritten to this format on 2026-08-02 (pyDrill 329,
bashDrill 192, cppDrill 124).

Format, ~80–150 words per card:
1. the mental model in plain language
2. why it behaves that way
3. a small worked example, indented four spaces
4. the rule or trap to carry away

### How it renders

`renderTeach(summary)` (engine, identical in all three files) splits the plain
text into blocks: runs of lines indented four spaces become
`<pre class="tc">` (monospace, `white-space: pre`, own `overflow-x: auto`),
everything else becomes `<div class="tp">` (`white-space: pre-wrap`).

Prose therefore wraps and code keeps its alignment, scrolling inside its own box
instead of reflowing. Before this split the whole panel was one `pre-wrap` node
and every example longer than ~55 characters reflowed into the prose, losing its
indentation.

Hard constraints, all learned the hard way:
- **Plain text only.** The summary is escaped with `esc()`. No HTML, and no
  Markdown either — backticks and asterisks render literally.
  `tools/strip_backticks.py` cleaned up an earlier pass that used `` `code` ``;
  its `SKIP_IDS` protects b1-003, where a backtick IS the syntax being taught.
  (`**` survives in pyDrill only as real `**kwargs` syntax.)
- **The `.teach` CSS rule must not be nested under `.fb`.** The teach panel is a
  SIBLING of the feedback div — `.fb` is already closed before the button is
  appended — so `.fb .teach` silently never matches. This was only caught by
  checking computed style in a browser, not by reading the diff.
- **Code-run detection is `/^ {4}/` on a non-blank line, not `/^ {4}\S/`.** The
  stricter form treats a more deeply indented continuation line as prose and
  shatters one example into several `<pre>` blocks.
- `.tc` fits ~45 monospace characters at 11.5px on a 390px viewport. Keep example
  lines within that where the code allows; `tools/tighten_teach_code.py` trims
  comment-alignment padding on lines that overflow (85% of code lines now fit,
  the rest scroll). The page itself must never scroll sideways — verify by
  rendering every card, not a sample.

Workflow for a batch: dump a topic's cards, write `{card_id: text}` to a Python
file, then

    python3 tools/update_summaries.py <drill>.html <summaries>.py
    node tools/validate.js <drill>.html

`update_summaries.py` asserts on unknown ids, blank text, and anything under
`MIN_WORDS` (45), so a half-finished batch fails loudly. It is re-runnable.

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
3. `node tools/check_hardest.js <file>.html` if round/selection logic changed.
4. `node tools/check_accept.js <file>.html` after any deck or grading edit.
5. For gitDrill/sqlDrill: `python3 tools/build_deck.py && python3 tools/make_drill.py`
   FIRST — editing the HTML directly is a hard-rule violation and is lost.
   After any sqlDrill deck edit also run `python3 tools/verify_sql.py`, which
   needs a server:
   `initdb -D /tmp/pgdata -A trust -U pg && pg_ctl -D /tmp/pgdata -o '-p 5433 -k /tmp' start`
   It exits 1 with instructions when no server is reachable rather than skipping
   silently — a check that quietly passes when it cannot run is worse than none.
6. jsdom gotchas (already handled in validate.js): construct JSDOM with
   `url: 'https://localhost/'` or localStorage throws; detect the summary via
   the `.card.summary` element, never `body.textContent` (it includes the
   inline script source, which contains UI strings).

## Deck state (2026-08-10 for git/sql, 2026-07-15 for the rest)
- gitDrill: 16/16 topics, 57 cards / 114 questions
  (32 command · 34 confusable · 17 recall · 14 danger · 13 fill · 4 history).
  g1 Three trees 3 · g2 Staging 5 · g3 Branches 4 · g4 Merging 4 · g5 Rebasing 5 ·
  g6 Undoing 5 · g7 Reflog 3 · g8 Stashing 3 · g9 Remotes 3 · g10 Fetch/pull/push 4 ·
  g11 History 4 · g12 Cherry-pick 2 · g13 Interactive rebase 2 · g14 Bisect 3 ·
  g15 Worktrees/submodules 3 · g16 Tags/ignore/config 4
- sqlDrill: 14/14 topics, 71 cards / 142 questions
  (54 confusable · 28 predict · 26 rows · 19 recall · 15 fill).
  Five fixtures: employees/departments (every join type gives a different
  count), scores (ties, for the ranking functions), orders/items (fan-out and
  anti-joins), node (a tree, for recursion), sales (a series, for windows).

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
0. Deepen gitDrill. sqlDrill was deepened on 2026-08-10 (39→71 cards,
   5→28 predict, 9→26 rows), all Postgres-verified. gitDrill has no equivalent
   oracle — its answers are checked by reading, so extra care is warranted, and
   `history` is only 4 questions.
1. Progress export/import + reset (all five) — guards against iOS Safari
   localStorage eviction. Highest value.
2. Deck deepening: pyDrill t1/t2/t7/t8 predicts; bashDrill b13; cppDrill c9.
3. Possible new pyDrill topics: typing, dataclasses, async, regex.
