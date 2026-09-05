# Language & skill trainers

Self-contained single-file HTML vocabulary/skill trainers (PWA-style, used on iPhone via GitHub Pages). Each app = one `*.html` with the dataset inlined as `const VOCAB_DATA = {...}` + a matching editable `vocab*.json` (source of truth for data edits).

Apps in this repo:
- `polish_trainer.html` + `vocab.json` — Polish→German (reference language German). Details: `HANDOFF.md`
- `spanish_trainer.html` + `vocab_es.json` — Spanish→English. Details: `HANDOFF_ES.md`
- `latin_trainer.html` + `vocab_la.json` — Latin→English, school years 1–2. Details: `HANDOFF_LA.md`
- `italian_trainer.html` + `vocab_it.json` — Italian→English, A1–A2. Details: `HANDOFF_IT.md`
- `french_trainer.html` + `vocab_fr.json` — French→English, A1–A2, **small-talk focused**. Details: `HANDOFF_FR.md`
- `portuguese_trainer.html` + `vocab_pt.json` — **European Portuguese** with Brazilian forms marked and both accepted. Details: `HANDOFF_PT.md`
- `brazilian_trainer.html` + `vocab_br.json` — **Brazilian Portuguese**, four persons, same source deck re-slotted. Details: `HANDOFF_BR.md`
- `medical_trainer.html` + `vocab_med.json` — **Latin & Greek medical terminology**, for medicine students. Details: `HANDOFF_MED.md`
- (PyDrill / bashDrill / cppDrill share the same engine family — same workflow applies if added here.)

## Generated decks (Latin, Italian, French)

`vocab_la.json`, `vocab_it.json` and `vocab_fr.json` are **generated, not hand-edited** — the curated
word lists live in `scripts/build_<lang>_vocab.py` and the paradigms come from
`scripts/<lang>_morph.py`. The Polish and Spanish decks remain hand-maintained JSON.
Both generators cross-check every expansion against whatever the source authored,
so a wrong plural, genitive or principal part fails the build instead of shipping;
this caught real errors in both decks (`miscēō`→`misceō`, `mūs` mis-flagged as a
non-i-stem, a masculine `-ga` plural rule that produced `collegi` for `colleghi`).

**French-specific:** the deck is deliberately weighted to **small talk** — lessons are
conversational situations and 181 of 1014 entries are ready-made phrases (Spanish has 12,
Italian 22). Keep that share when expanding. Its `FILLER` is `{to}` only, *not* the
Italian `{to, a, an, the}`, because French answers contain a bare `a` (`il a`, `il y a`);
English glosses therefore omit articles. Aspirate h is curated — it is unrecoverable from
spelling and decides both article and elision (`le héros` vs `l'hôtel`). See `HANDOFF_FR.md`.

**Italian-specific:** `-co`/`-go` plurals are lexical (`amico`→`amici` but
`fuoco`→`fuochi`) and come from curated tables; the generator *raises* for any such
word not in them rather than guessing. Italian's `essere`/`stare` split is **not**
Spanish's `ser`/`estar` — `essere` covers location and temporary states
(`sono a Roma`, `sono stanco`), with `stare` reserved for health, the progressive,
`stare per`, and fixed expressions. See `HANDOFF_IT.md` before touching that bank.

## Portuguese: two apps, one source

`portuguese_trainer.html` and `brazilian_trainer.html` are both **generated from
`spanish_trainer.html`** by one run of `scripts/make_portuguese_trainer.py`, and
their decks by one run of `scripts/build_portuguese_vocab.py` (+
`scripts/portuguese_morph.py`). Same generator, same curated word list, so they
cannot drift — and both get the sw.js, manifest and icon refs generated too.

Each deck marks the OTHER variety on the entry as `alt`, and **accepts it when
typed** — a runtime property of `checkAnswer`, so `scripts/check_portuguese.py`
tests it by running each app's own code over all 52 pairs, in both apps.

Persons differ and this is real, not cosmetic: Portugal drills **five**
(eu / tu / ele·ela·você / nós / eles·elas·vocês), Brazil **four** (você takes the
third-person form, so tu has no column). *Vós* is archaic in both.
`check_portuguese.py` asserts the count per app and fails if a verb carries a
form under a key no pronoun label names.

Everything derived is recomputed from a swapped headword — plural, feminine,
paradigm and the `(PT)`/`(BR)` gloss marker. Skipping any of those had the
decline drill asking for the feminine of `marrom` and answering `castanha`.

Three banks Spanish has no use for: **personal infinitive**, **future
subjunctive** and **false friends against Spanish**. The first two are the
valuable ones — the personal infinitive is regular for every verb (ser→sermos)
while the future subjunctive uses the preterite stem (ser→formos), and for a
regular verb they are the same word, which is exactly why they get confused.

A **spelling oracle** (`pyspellchecker`, European Portuguese, allowlisted) runs
over every generated form and caught four real bugs: the -ês plural dropping its
accent, the -vel family taking -eis not -éis, -guer dropping only its u, and
`hoje` mis-classified as a noun. `-ão` plurals are lexical and curated, exactly
like Italian's -co/-go.

**The bug worth remembering when scaffolding any app from another:**
`enabledModes` is a second list of mode names as BARE object keys, so a
quoted-string rename misses it. Left stale it enabled two modes that no longer
existed and never enabled three new ones — five of twelve drill types dead,
while `validate.py` still passed because every mode that could run did. It is
now derived from `MODE_LABELS`, and `check_portuguese.py` fails on any offered
drill type that generates nothing. The `<title>` and one `promptLabel` were
missed the same way and only showed up in a browser screenshot — as did
`DECL_LABELS` still reading `fem. pl. (las ... )` in both Portuguese apps, and a
shared diacritic map carrying Polish, German and Spanish letters but **none of
Portuguese's own**, so `coracao` for `coração` graded plain wrong. Prose strings
and shared tables are exactly what a field rename walks past.

Home-screen icons have a recipe now: `scripts/make_icons.py <slug> <badge>
<accent> <ink>`, checked against the shipped ones with `--check`.

## Medical terminology: a different drill set on the same engine

`medical_trainer.html` is **generated from `latin_trainer.html`** by
`scripts/make_medical_trainer.py` — edit that script, not the HTML, so engine
fixes in the Latin trainer keep flowing through. Its data comes from
`scripts/med_elements.py` + `scripts/med_terms.py` via
`scripts/build_medical_vocab.py`.

The drill types are replaced wholesale, because medical terminology is a
morphology skill rather than a translation one: element↔meaning both ways,
**build the term** from a definition, **break it down** into elements,
**Greek ↔ Latin doublets**, classical **plurals**, **confusable pairs** as a
two-way forced choice, prescription Latin, MC and clinical cloze. Latin and Greek
share one deck on purpose — see `HANDOFF_MED.md`.

Two engine behaviours are overridden for this app only, both applied by the
generator script:
- **`gradeAnswer` splits alternatives on comma only.** The shared version splits
  on comma *or slash*, which is right when `a / b` means "either answer" but
  wrong here, where `cardi/o` is a single form — it tore every root in half and
  graded correct answers as typos. The validator could not see this (it only
  checks a question can be generated); a browser grading probe did.
- The deck-summary pluraliser needs real plurals; its `p + "s"` fallback printed
  "suffixs"/"prefixs".

`build_medical_vocab.py`'s `segment_ok` is the counterpart of the Latin paradigm
cross-check: every term's authored parts must actually be able to spell the term
under the combining-vowel and elision rules, so a wrong root, a wrong order or an
`-ectomy`/`-ostomy` swap fails the build.

## Latin: generated data, and how it differs from the other decks

`vocab_la.json` is **generated, not hand-edited** — edit the curated word lists in
`scripts/build_latin_vocab.py` and re-run it, then rebuild + validate:
```
python3 scripts/latin_morph.py          # paradigm self-check
python3 scripts/build_latin_vocab.py    # regenerates vocab_la.json
python3 scripts/rebuild.py latin_trainer.html vocab_la.json
python3 scripts/validate.py latin_trainer.html
```
`scripts/latin_morph.py` expands the compact dictionary forms into full paradigms —
nouns off the genitive singular, verbs off their principal parts — with explicit
irregular tables. Every expansion is assert-guarded and cross-checked against the
authored form, so a wrong genitive or a mistyped principal part fails the build
rather than shipping a bad paradigm (this caught a real `miscēō`→`misceō` typo).

Engine differences vs the Spanish/Polish trainers:
- **`conjugation` is two-level**: `{tense: {person: form}}`, six indicative active
  tenses. The conjugate drill picks a tense *and* a person; `buildConjSection`
  renders every tense. The other decks stay one-level — do not "unify" them.
- **`principal_parts`** is a drill mode of its own. `normalize()` strips commas, so
  comma- and space-separated answers grade identically.
- **`noun_decl` carries all five cases in both numbers**; `CASE_ORDER` drives the
  reveal table. Nominative singular is the headword and is not stored.
- **Macrons** are display-only: they are in `DIACRITIC_MAP` *and* in the
  `stripDiacritics` character class, so typing plain vowels scores full credit.
- **`FILLER` is `{to, a, an, the}`, not the Spanish reflexive list.** `nōs`, `vōs`,
  `mē`, `tē`, `sē` and `ōs` are real Latin headwords; stripping them emptied the
  answer and graded it wrong. Stripping is also guarded so it can never reduce an
  answer to nothing.

Known generator constraints (all fail loudly rather than silently):
- **Deponent verbs are not supported** (`sequor`, `loquor`, `cōnor`, …) — they have
  no active forms, and the generator would produce wrong output. None are in the
  deck; adding them needs passive-form machinery first.
- One-termination 3rd-declension adjectives are assumed to be i-stems
  (`ingēns`→`ingentia`). `vetus`, `pauper` and `dīves` are consonant stems whose
  neuter plural is `-a`; `CONSONANT_STEM_ADJECTIVES` rejects them with an
  explanation rather than generating `veteria`.
- Compounds of the irregular verbs are listed explicitly in `VERB_COMPOUNDS`, never
  matched by suffix — a rule like `endswith("eō")` would capture every
  2nd-conjugation verb (`moneō`, `videō`, `habeō`).
- Plural-only nouns (`castra`, `arma`, `thermae`) pass their genitive **plural** and
  set `plural_only=True`.

## What a mechanical rename walks past (found by sweeping for it)

The Portuguese section below describes this bug class; a sweep across all eight
apps found four more live instances of it, all now fixed at the generator or
patch script, never in a generated file:

- **Every app exported its progress as `polish-trainer-progress-<date>.json`.**
  The slug was hardcoded and copied through all eight scaffolds, so backing up
  two trainers produced two files with the same name. It is now derived from
  `STORAGE_KEY`, which each app already sets for itself.
- **`selectionCanAsk` in both Portuguese apps gated on `enabledModes.es_en` /
  `.en_es`** — names those apps do not have. Same bare-key blind spot as the
  `enabledModes` initialiser, one function further on. The clause was therefore
  always false: with only the two translation drills selected, both apps
  reported **0 words in selection** and an empty state while `generateQuestion`
  kept producing questions, which is why `validate.py` never saw it. It also
  kept dead `antonym`/`synonym` clauses for drills those apps do not offer.
  `check_portuguese.py` now compares every `enabledModes.<key>` reference in
  `selectionCanAsk` against `MODE_LABELS` and fails on any that is not a real
  drill type, and asserts a translation-only selection still counts its words.
- **`make_medical_trainer.py` replaced `buildPool` with a copy that predated the
  hardest-words round**, so regenerating the app silently reverted its round to
  drilling the whole deck. `patch_hardest.py` cannot repair it — it sees
  `hardestRows` already present and skips — so the generator carries the branch
  itself. `check_hardest.py` is what caught it.
- **`stripGermanFiller` / `cleanGerman`** are shared engine helpers with nothing
  German about them outside the Polish app; they are now `stripFiller` /
  `cleanGloss`, and the comments around them name each app's own languages
  rather than Polish and German.

- **`answerLabel` is two things at once** — a language ("Polish") or the kind of
  thing wanted ("Antonym", "Form", "Word") — and one shared line wrote
  `"Your answer in " + answerLabel.toLowerCase()` for both. It read "Your answer
  in synonym…" for four of Polish's six labels and for **every one** of the
  medical trainer's, which names no language at all. A question that wants a
  language now says so with `answerIn: true` (the two translation modes), and
  everything else reads "Your antonym…". `validate.py` decides which labels are
  languages from the app's own output rather than a list — a translation mode
  uses the language name as its `promptLabel` too — and fails either way round.

`scripts/dom_stub.js` now **records** children, attributes and click listeners
instead of discarding them, so a check can render a control and press it. While
they were no-ops nothing could test what a button *does* — which is how the
hardest-words button stayed one-way with every check passing.

## The on-page error box

Each trainer shows a red diagnostic box for uncaught errors. It **ignores opaque
cross-origin errors** — `message: "Script error."` with no filename or line. That is
what a browser reports when a script from another origin throws, and since these pages
load no external scripts at all, such an error is always someone else's injected code
(an in-app browser, an extension, a content blocker), not ours. It was reported from a
phone as a "Script error." banner on a working app; a 600-question run across every mode
threw nothing, and dispatching a synthetic opaque ErrorEvent reproduced the banner
exactly. Errors from our own inline script carry the page URL and a real line number and
are still reported — don't widen the filter past the no-filename-and-no-line case.

## Offline support (PWA)

Each app has a matching `<name>-sw.js` service worker + `<name>-manifest.json` manifest + `icons/<name>-icon-{192,512}.png`, registered from a snippet inside the app's existing single `<script>` block (registration must stay inside that block, not a second `<script>` tag — `scripts/validate.py` extracts JS from the first `<script>` to the last `</script>`, and a second tag breaks the extraction).

- Registration uses an explicit narrow `scope` equal to the page's own filename (e.g. `{ scope: './spanish_trainer.html' }`) so each app's service worker only ever controls itself, even though both trainers' files live in the same directory.
- Strategy is network-first with cache fallback: every fetch tries the network first (and caches a fresh copy on success), falling back to the cache — and finally to the precached app page — only when the network fails (offline).
- `CACHE_NAME` is a manually-versioned string (e.g. `spanish-trainer-v1`); bump it whenever you want to force-purge old cached assets on next activation. Since the strategy is network-first, this is mostly a safety net — online users always get the latest file regardless.
- Service workers require serving over HTTP(S), not `file://` — test with a local server (e.g. `python3 -m http.server`), not by opening the HTML file directly.

## The header is computed, never written down

The stats line and the deck summary under it (`#deck-meta`) are both rendered
from `VOCAB_DATA` at load. Polish had them hardcoded as static HTML from when
the deck held 1126 entries, so the shipped app advertised **half the deck**
(`1126 entries · 598 nouns …` against a real 2234/1370) while the stats line
right above it, being computed, said 2234. `vocab.json`'s `meta` block held the
same stale snapshot and fed nothing; it now carries only the descriptive fields
the other decks use. **Don't put a count in markup or in `meta`** — nothing
recomputes them, and `validate.py` cannot see a wrong number in a string.

## Selection filters & repeat avoidance

Three independent filters gate the question pool, each with its own `All`/`None` toggle row and its own localStorage key (`<app>_trainer_lessons` / `<app>_trainer_pos`; drill-type enablement isn't persisted): **Drill types** (`enabledModes`), **Lessons** (`enabledLessons`, `ALL_LESSONS`), and **Word forms / part of speech** (`enabledPos`, `ALL_POS`, derived from `entries.pos`, most-frequent-first). `buildPool()` ANDs all three; adding a fourth filter dimension means threading it through the same four spots: `buildPool`'s filter predicate, `selectionCanAsk`'s two call sites (`renderSelectionCount`, `selectionExhausted`), and the `renderCard` empty-state message chain.

**Gotcha**: `enabledPos` only filters things drawn from `entries` — Spanish's `ser_estar`/`por_para` special-bank modes have no `.pos` field to check (caught after shipping: selecting only "Numbers" still surfaced random Ser vs estar questions). Fixed via `specialModeAllowed(type)`, which hand-maps `ser_estar`→`enabledPos.verb` and `por_para`→`enabledPos.preposition` and is checked both in `generateQuestion` (gates whether the mode can fire at all) and in the Word-forms toggle handler (so a *currently displayed* special question gets replaced immediately if its pos is unchecked mid-question, not just on the next pick). Any future special/curated-bank drill mode needs the same explicit pos mapping — it won't fall out of the `entries`-based filtering for free.

Repeat avoidance is two-layered, in `buildPool` (and, for Spanish only, mirrored in the `ser_estar`/`por_para` special-bank branch since those draw from `VOCAB_DATA.special` instead of `entries`):
1. **Hard floor** — `NO_REPEAT_WINDOW` (8): a word can't resurface within the last 8 questions *of its own pool*, as long as the pool is big enough to still leave a choice (`Math.min(recentIds.length, pool.length - 1, NO_REPEAT_WINDOW)`). This is the part that actually matters for small pools (a single lesson, or one part-of-speech filter) — a soft multiplier alone doesn't reliably prevent short gaps once you check it against a synthetic gap simulation, because the *average* revisit gap for a fixed pool size trends toward the pool size regardless of weighting shape; only a hard exclusion moves the *minimum* gap.
2. **Soft recency decay** on top, for pools bigger than the hard window: `w *= recency / (recency + 12)` over a `recentIds` lookback capped at 40 (was `+6` / cap 20 before this was widened).

**Polish only, so far**: a third, stricter layer sits in front of both —
`buildPool` hard-excludes anything in `roundAsked` (this round's own coverage
set, reset each round), so a word cannot repeat at all until every askable
word in the current selection has had a turn. Once it has, `selectionExhausted`
ends the round straight into the summary rather than pausing to ask
"keep going?" — that interstitial (`showSelectionBreak`, `breakShown`) is gone.
The other seven apps still rely on layers 1–2 alone (repeats are rare, not
impossible, within an open-ended round). See `HANDOFF.md` before porting this;
it wasn't asked for elsewhere yet.

## Answer acceptance: what counts as correct

Reported from real use: the apps were marking correct answers wrong. Fixed by
`scripts/patch_grading.py` (re-runnable, idempotent) and locked down by
`scripts/check_grading.py`, which fails if any of these regress.
**Run `python3 scripts/check_grading.py` after touching grading.**

The rules below are enforced through `patch_grading.py`'s job table — if an app
is not in that table it does not have them. Polish was missing for a long time
because it is glossed in German and rule 1 does not apply to it; rules 3–6 do,
and it now has them.

1. **English contractions, both directions.** Glosses are written as people speak
   them ("it's", "what's your name?"); a learner taught formal written English
   types "it is" / "what is your name". `expandContractions` rewrites both sides
   before comparing. Each pattern requires a recognised English pronoun or
   auxiliary before the apostrophe (or the `n't` ending), so they cannot touch
   French elision — `j'ai`, `qu'est-ce`, `l'hôtel`, `t'appelles` pass through
   unchanged, with guard cases proving it.

2. **French question forms (French only).** A question has three shapes: rising
   intonation (`tu veux venir ?`), `est-ce que`, and inversion (`veux-tu venir ?`).
   The deck stores one; `frenchQuestionVariants` derives the others for the
   EN→FR accept list, including the reflexive case
   (`comment tu t'appelles ?` <-> `comment t'appelles-tu ?`) and interrogative
   in situ (`qu'est-ce que ça veut dire ?` <-> `ça veut dire quoi ?`).
   Only stored answers containing `?` are transformed, so the noun
   `rendez-vous` is never mistaken for an inverted verb. Which token is the verb
   cannot be known without parsing, so several candidate shapes are offered; the
   extra ones only widen acceptance.

3. **Adjective agreement (fr/es/it/pl, NOT Latin).** An EN→X prompt carries no
   gender or number, so every agreeing form answers it: "big" is
   grand/grande/grands/grandes, "groß" is duży/duża/duże. Latin is excluded on
   purpose — its `declension` spans cases, so accepting every form would accept
   a genitive plural for "good". Polish is included because its `declension`
   holds nominative forms only, so the same argument as Spanish applies.

4. **Curated synonyms** linked on an entry join its accept list, on top of the
   existing cross-entry rule (any entry sharing an English alternative).
   **Except a Polish aspect partner.** Polish mirrors every `aspect_pair` link
   into `synonyms`, so this rule would silently accept a perfective for an
   imperfective prompt — a distinction the deck drills on purpose, and which
   the Synonyms drill asks for explicitly, tagged `(pf.)`/`(impf.)`. It only
   reaches the 6 of 24 pairs the deck glosses *differently* (`mówić`
   "sprechen, reden" vs `powiedzieć` "sagen"); for the other 18 both verbs carry
   the same German word and the cross-entry rule still accepts either, which is
   right — the prompt genuinely translates to both.

5. **A comma inside a phrase is not an alternative separator.** `gradeAnswer`
   splits the target on `,` and `/` — right for "town, city", wrong for
   "I'm fine, thanks", which could therefore never match in full. The intact
   target is now always offered alongside the split parts.

6. **Filler-stripping must never empty an answer.** `stripGermanFiller` drops
   reflexive particles/articles from both sides so "sich entschuldigen" and
   "entschuldigen" match. When the whole answer *is* one of those particles the
   target became `""` and matched anything that also stripped to nothing —
   German "sich" graded **exact** for the Polish headword `się` (pd0773,
   glossed "man"). `return kept || s` falls back to the unstripped string.
   Latin and French already had the guard; Polish now does. Spanish, Portuguese
   and Brazilian still carry the unguarded one-liner — latent, because no entry
   or cloze target in those decks is made only of their `FILLER` words, and
   patching Spanish alone would desync the two generated Portuguese apps.

Still not accepted: a synonym that is **not in the deck at all**. Cross-entry
acceptance can only find words the deck knows; add the word as an entry whose
gloss shares an alternative and it is accepted everywhere.

**Punctuation is stripped, apostrophes are not.** `normalize` removes
`. , ! ? ; : ¡ ¿ … « » – — “ ”` so an answer never depends on typing punctuation.
The Spanish opening marks matter: they were originally missing while the closing
ones were stripped, so `hola` graded only "typo" against `¡hola!` (half credit)
across the six greeting phrases, 39 cloze sentences and 6 special-bank items that
carry them. Apostrophes are deliberately left in — Italian `l'` and `un'` are word
forms, and `l'` is itself an answer in the Noun forms drill.

**Mode selection must try every enabled mode, not a fixed number of random draws.**
`pickQuestion` shuffles the enabled modes and walks them, because many modes cannot
serve a given selection at all — a `phrase` entry has no conjugation, declension,
cloze or antonyms, so only 3 of the 11 Spanish modes can produce a question for it.
The old "8 random draws" version therefore reported "No words match the selected
drill types, lessons, and word forms" on ~9% of questions whenever a narrow
Word-forms filter was active. The empty state now appears only when *no* enabled
mode can serve the selection, which is a real dead end worth reporting.

## The hardest-words round

A button in the header starts a round drawn **only** from the words with the most
wrong answers. Added by `scripts/patch_hardest.py` (re-runnable, idempotent) and
locked down by `scripts/check_hardest.py` — **run it after touching selection or
round logic.**

It exists because the SRS weighting cannot concentrate practice: an always-wrong
item scores 5 against 1 for a mastered one and 12 for an *unseen* one, so in a
1000-word deck a hard word still surfaces about one question in seven, and only
once coverage is complete. Same conclusion as repeat avoidance — only a hard
exclusion moves the distribution.

Design decisions, all made by the owner when asked:
- **Ranking is raw wrong count**, not error rate, with no minimum-attempts floor.
  `recordAnswer` already books a near-miss as half a wrong, so typos accumulate
  toward difficulty without outranking outright errors. Ties break on the worse
  rate.
- **Scope is global**: the round deliberately **ignores the lesson and word-form
  filters**, so it is the hardest words overall rather than the hardest inside
  the current view. This is the one place `buildPool` bypasses those filters.
- **Shape is a separate round button**, not a drill type and not a fourth filter
  dimension — it reuses the existing round machinery and needs no threading
  through `selectionCanAsk`/empty-state.
- **The button is a toggle** (`aria-pressed`, `.btn-hardest.active`): press it in
  a round and it leaves for an ordinary one, because `startNewRound` already
  clears `hardestMode`/`hardestIds` and both header lines. It shipped one-way —
  its click handler was `startHardestRound` whatever the state, so pressing it
  again restarted the same round and the only way out was to finish or reload —
  and it rendered permanently dark, the same styling every other selector on the
  page uses for "selected", so it read as on before it was. Its in-round label
  counts `hardestIds`, not `hardestRows()`, which keeps moving as you answer.

Size is `max(8, ceil(0.10 × words attempted))`, capped at the number of words
with any mistake against them. Below 8 missed words the button is disabled and
says how many are needed — with no history there is nothing to drill, so the
feature is inert rather than misleading.

Enabled **drill types still apply** (so "hardest words, as cloze" works), but
`specialModeAllowed` returns false in a hardest round: the Spanish/Italian/French
sentence banks draw from `VOCAB_DATA.special` and carry no entry id to match
against the hardest set.

Three surfaces have to know about the round or they lie: `selectionExhausted`
(coverage means the hardest set, not the selection), the `renderCard` empty-state
chain, and `renderSelectionCount` (it would otherwise claim "880 words in
selection" while drilling 12).

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

Generated apps (`medical_trainer.html`, `portuguese_trainer.html`,
`brazilian_trainer.html`) are rebuilt by their own scripts, never hand-edited:
```
python3 scripts/build_portuguese_vocab.py && python3 scripts/make_portuguese_trainer.py
python3 scripts/validate.py portuguese_trainer.html
python3 scripts/validate.py brazilian_trainer.html
python3 scripts/check_portuguese.py          # both apps
```

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
