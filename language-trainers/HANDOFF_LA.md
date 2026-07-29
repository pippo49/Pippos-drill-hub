# Latin trainer — handoff

Self-contained Latin→English vocabulary trainer (single HTML file, same engine family as the Polish and Spanish trainers, PWA-ready, used on iPhone). English is the reference/answer language. Level: **what you meet in the first two years of school Latin**. Keep responses concise — lead with results; I spot-check errors myself.

## The data is generated — never hand-edit `vocab_la.json`

Edit the curated word lists in `scripts/build_latin_vocab.py`, then:
```
python3 scripts/latin_morph.py          # paradigm self-check
python3 scripts/build_latin_vocab.py    # regenerates vocab_la.json
python3 scripts/rebuild.py latin_trainer.html vocab_la.json
python3 scripts/validate.py latin_trainer.html
```
Hand-edits to `vocab_la.json` are lost on the next build.

## Source format (what you actually author)

- **Nouns**: `(nominative, genitive, gender, declension, i-stem?, English, lesson)` — the genitive gives the stem and identifies the declension, exactly as a course teaches it. Plural-only nouns go in `PLURAL_ONLY_NOUNS` and pass their genitive **plural**.
- **Verbs**: `(principal parts, conjugation, English, lesson)`, conjugation in `{1, 2, 3, "3io", 4}`.
- **Adjectives**: `(nominative, type, base-or-None, English, lesson)`, type in `{"us", "er", "3-2", "3-1", "3-3"}`. `er`/`3-1`/`3-3` need an explicit base (`pulcher`→`pulchr`, `ingēns`→`ingent`).
- **Everything else**: `(Latin, English, pos, lesson)`.
- **Cloze**: `CLOZE[headword] = [(sentence with {target}, English), ...]`, target wrapped in `{...}`, answer = the in-sentence inflected form.
- **`ANTONYMS` / `SYNONYMS`**: pairs of headwords, linked both directions automatically.

Macrons are authored in the source words and carried through the endings. They are **display-only** — grading is macron-insensitive, so typing plain vowels always scores full credit.

## Generator guarantees

`latin_morph.py` expands nouns off the genitive singular and verbs off the perfect stem, with explicit irregular tables (`sum`/`possum`/`eō`/`ferō`/`volō`/`nōlō`/`mālō`/`dō`; `vīs`/`domus`/`deus`/`Iuppiter`/`bōs`/`iter`). Every expansion is assert-guarded **and cross-checked against the authored form** — a wrong genitive or mistyped principal part fails the build. This is the main safety net; trust it and let it fail rather than working around it.

`build_latin_vocab.py` additionally enforces: id uniqueness, `(la, pos)` uniqueness, antonym/synonym link targets exist, single-brace cloze, no blank forms, 6 persons per tense.

## Known constraints (deliberate — each fails loudly)

1. **No deponent verbs** (`sequor`, `loquor`, `cōnor`, `patior`, `ūtor`…). They have no active forms and the generator would emit nonsense. Common in year 2 — adding them needs passive-form machinery first, and is the single biggest gap.
2. One-termination 3rd-decl adjectives are assumed i-stem (`ingēns`→`ingentia`); `vetus`, `pauper`, `dīves` are consonant stems (`vetera`) and are rejected by `CONSONANT_STEM_ADJECTIVES`.
3. Irregular-verb compounds are listed explicitly in `VERB_COMPOUNDS` — never suffix-matched, because `endswith("eō")` would capture `moneō`/`videō`/`habeō`.
4. Adjective paradigms store **nominatives only** (5 gender/number forms). Cloze answers in oblique cases (`in altō monte`) will therefore show up in the flag-only cross-check as "outside stored paradigms" — that is expected, verify by eye rather than auto-fixing.

## State of the deck (v1)

- **1000 entries**: 434 nouns, 241 verbs, 150 adjectives, 79 adverbs, 26 prepositions, 25 numbers, 23 pronouns, 22 conjunctions. 15 topic lessons.
- All five declensions incl. i-stems, neuters and plural-only; all four conjugations plus 3rd-`iō` and the irregulars; six indicative active tenses per verb.
- **Cloze: 89 words × 2 sentences (178)**. Antonyms: 58 pairs. Synonyms: 26 pairs.
- 10 drill modes: `la_en, en_la, conjugate, decline, noun_case, antonym, synonym, multiple_choice, cloze, principal_parts`.

## What's next

1. **Deponent verbs** — needs engine support for passive forms (see constraint 1).
2. Comparative/superlative adjectives (`melior`, `optimus`) as a second `declension` layer.
3. Subjunctive as further tense keys — the `conjugation` shape already supports it; only the labels and generator tables need extending.
4. Oblique-case adjective forms, if adjective agreement is worth drilling directly.
5. A "which case is this?" drill over the cloze sentences — the closest Latin analogue to the Spanish `ser_estar`/`por_para` special banks, and the engine already generalises MC-style modes on `currentQ.choices`.

## My preferences

Direct, concise, lead with the result; batch sizes as I specify; only apply corrections you're confident in, flag the rest; no blanket auto-sweeps on lexical morphology; always rebuild + validate before presenting files.
