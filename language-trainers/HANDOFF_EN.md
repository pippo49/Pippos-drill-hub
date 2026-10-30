# English trainer — handoff

Self-contained English→German vocabulary trainer (single HTML file, same engine
family as the other trainers, PWA-ready, used on iPhone). Level: **A1–A2
starter deck**, 9 lessons, 225 entries — the first slice, meant to grow the
way every other trainer here did: lesson by lesson, not shipped complete.

## Direction: the mirror of Polish, not of Spanish

Every other trainer here glosses in English (`es/en`, `it/en`, `fr/en`,
`la/en`). This one is the other way round: **English is the headword being
drilled** (`en`), **German is the bare gloss** (`de`) — same shape as the
Polish trainer (`pl` headword / `de` gloss), just with English's far lighter
grammar. It exists for a German speaker learning English, not an English
speaker learning German.

That direction decision matters for grading, and it was worth getting
explicit before writing a line of engine code: the two previous candidate
framings ("German is the headword, needs full case/gender morphology" vs
"English is the headword, lighter grammar") implied different build effort
and different grading rules, so the owner was asked to pick between them
directly rather than guessing from "add an English/German drill".

## Why English needed its OWN engine, not a generator like Portuguese

`make_portuguese_trainer.py` works by renaming fields in a copy of the Spanish
trainer, because Portuguese and Spanish have the *same grammatical shape*:
both inflect for gender, both decline adjectives four ways, both conjugate by
person. A line-for-line transform is safe.

English doesn't share that shape with anything else in this repo — no
grammatical gender, no case system, no adjective agreement at all. Copying
Polish's `declension`/`noun_case` modes over would have produced either
nothing (no data to put in them) or nonsense (agreement-widening rules that
assume a form space English doesn't have). So `english_trainer.html` is its
own hand-written engine, closely modelled on Polish's, with the grammar-heavy
modes swapped for English-appropriate ones and the shared parts (grading core,
SRS, no-repeat round, hardest words, cloze UI, PWA, export/import) copied
near-verbatim, since none of that is language-specific.

## Schema (what `build_english_vocab.py` authors)

```
{ en, de, pos, id, lesson,
  conjugation: {i,you,he_she_it,we,they},       // verbs, present tense only
  principal_parts: [base, past, participle],     // verbs, IRREGULAR ONLY
  plural: "...",                                 // nouns, only when worth drilling
  comparison: [comparative, superlative],        // adjectives, when gradable
  cloze: [{en: "...{word}...", de: "..."}] }
```

Three things are deliberately **not** authored on every entry of their part of
speech, unlike Polish's `noun_decl`/`declension` which are populated for
(almost) every noun/adjective:

- **`principal_parts` only on irregular verbs.** A regular verb's past and
  participle are both `base + "ed"` — there is no exception for a drill to
  catch, so regular verbs simply don't get the field, and the `principal_parts`
  mode never offers them. `scripts/english_morph.py`'s
  `IRREGULAR_PAST_PARTICIPLE` table is the full list of what does.
- **`plural` only when it's worth drilling.** `cat` → `cats` teaches nothing;
  `child` → `children`, `city` → `cities`, `leaf` → `leaves` do. The generator
  computes the regular form and simply omits the field when it matches
  `base + "s"` exactly (see `add_noun` in `build_english_vocab.py`).
- **`comparison` only on gradable adjectives.** Colour terms, nationalities and
  a handful of others don't take a comparative/superlative at all; those
  entries carry no `comparison` field and the mode skips them.
- **`you` and `you_pl` are the same person, always** — English never
  distinguishes singular/plural "you", for any verb including `be` (am / **are**
  / is / **are** / **are**). A sixth, always-identical drill slot would have
  taught nothing, so `conjugate` only has five persons (`i, you, he_she_it, we,
  they`), not six.

`scripts/english_morph.py` derives every regular form (3rd-person -s/-es/-ies
spelling, regular plurals including the f→ves and y→ies spelling changes,
regular -er/-est vs periphrastic more/most) and holds the irregular override
tables (`IRREGULAR_PRESENT`, `IRREGULAR_PAST_PARTICIPLE`, `IRREGULAR_PLURAL`,
`IRREGULAR_COMPARISON`). `build_english_vocab.py`'s `check_unused` cross-checks
every override table against the word list that actually uses it — the same
principle as `latin_morph.py`'s principal-parts cross-check, so a typo'd or
orphaned override fails the build instead of silently doing nothing. (This is
how the deck grew from an initial ~30-verb sample to the 78 in the shipped
build — the cross-check kept rejecting the build until every table entry that
had already been written actually had a word using it, which was the fastest
way to discover which common irregular verbs were still missing from the
lesson list.)

## Grading: needs BOTH halves of the existing rule set

Every other app needs at most one of "English contractions" (gloss = English)
or "German filler guard" (gloss = German) from `scripts/patch_grading.py`'s
job table — never both, because in every other app exactly one side of the
pair is English. This app answers questions in **both** directions (`en_de`
answers in German, `de_en`/`cloze` answer in English), so it needs both rules
at once, applied directly in the engine rather than patched on afterwards:

- **English contractions** (`expandContractions`), because `de_en` and cloze
  answers are free-typed English prose ("it's" / "it is").
- **German filler guard** (`stripFiller`, stripping the reflexive particle
  "sich", with the `return kept || s` fallback from day one so a filler word
  that IS the whole answer can never grade an unrelated answer "exact").

**Not needed, unlike Polish/Spanish/Italian/French**: the adjective-agreement
widening rule (`patch_grading.py` rule 3). That rule exists because a
gloss-side prompt with no gender/number marking must accept every agreeing
form of the target-language adjective. English adjectives don't agree with
anything — there is no form space to widen into. `comparison` is a separate
drill mode, not a grading exception.

`scripts/check_grading.py` has a dedicated `ENGLISH_PAIRS` section exercising
both rules together, run alongside the French/Polish regression checks it
already had.

## The shared `validate.py` had a real English-specific gap

Its cloze brace-check picked the cloze pair's target language as "whichever
key is not `en`" — true in every other deck, where `en` is always the English
*gloss*. Here `en` is the *target*, carrying the `{brace}` markup, while `de`
is the gloss. The old logic would have checked the German side (no braces, 0
≠ 1) and failed every cloze question in this deck. Fixed to pick whichever key
actually contains a `{` instead of assuming which language that is — strictly
more correct for every existing deck too, not just this one.

## Validation

```
python3 scripts/english_morph.py            # no CLI output; imported by the next line
python3 scripts/build_english_vocab.py       # regenerates vocab_en.json, cross-checks tables
python3 scripts/rebuild.py english_trainer.html vocab_en.json
python3 scripts/validate.py english_trainer.html
python3 scripts/check_grading.py
python3 scripts/check_hardest.py
python3 scripts/build_index.py               # keeps the hub's counts honest
```

## Backlog (owner decides priority)

1. More lessons — this is a 225-entry starter slice (9 lessons: greetings,
   family, numbers/time, food, two verb lessons, adjectives, home, weather,
   people/animals), not the full deck every other trainer has grown into.
2. No antonym/synonym bank yet (unlike Polish/Spanish/Italian/French) — no
   curated links authored for this first pass. Cheap to add once there's a
   deck big enough for it to be worth curating.
3. No curated sentence bank (unlike Spanish/Italian/French's `ser_estar`-style
   modes) — nothing in English's A1-A2 grammar maps onto that shape the way
   ser/estar or tu/vous do.
4. Icon accent `#2d4356` / badge `EN` — unused by any other app, picked to be
   visually distinct in the hub.
