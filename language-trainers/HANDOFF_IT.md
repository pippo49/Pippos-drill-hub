# Italian trainer — handoff

Self-contained Italian→English vocabulary trainer (single HTML file, same engine family as the Spanish trainer, PWA-ready, used on iPhone). English is the reference/answer language. Level A1–A2. Keep responses concise — lead with results; I spot-check errors myself.

## The data is generated — never hand-edit `vocab_it.json`

Edit the curated word lists in `scripts/build_italian_vocab.py`, then:
```
python3 scripts/italian_morph.py         # rule self-check
python3 scripts/build_italian_vocab.py   # regenerates vocab_it.json
python3 scripts/rebuild.py italian_trainer.html vocab_it.json
python3 scripts/validate.py italian_trainer.html
```

## Source format

- **Nouns**: `(word, gender, English, lesson[, explicit plural])`. The plural is generated; supply it explicitly only to *assert* a curated form — the generator compares its own rule against yours and fails on a mismatch rather than silently deferring.
- **Verbs**: `(infinitive, English, lesson[, isc])`, where `isc=True` marks the `-isc-` type (`finire → finisco`).
- **Adjectives**: `(masc sg, English, lesson[, invariable])`.
- **Everything else**: `(Italian, English, pos, lesson)`.
- **Cloze**: `CLOZE[headword] = [(sentence with {target}, English), ...]`.
- **`ANTONYMS` / `SYNONYMS`**: headword pairs, linked both ways. Keep them same-part-of-speech — the drill asks for a word of the same kind.

## Generator notes (`italian_morph.py`)

- **Articles** are derived, not stored per word: `il / lo / l' / la` and `i / gli / le`, covering s+consonant, z-, gn-, ps-, x- and semiconsonantal i-.
- **Plurals of `-co`/`-go` are lexical** (`amico → amici` but `fuoco → fuochi`: it follows Latin stress, which the spelling does not record). These come from the curated `HARD_PLURAL` / `SOFT_PLURAL` tables and the generator **raises** for any `-co`/`-go` word not in them, rather than guessing. Adding such a word means adding a table entry.
- `-ca`/`-ga` insert an h but keep the gendered vowel: masculine `collega → colleghi`, feminine `amica → amiche`.
- `-cia`/`-gia` keep the i after a vowel (`camicia → camicie`) and drop it after a consonant (`arancia → arance`).
- Irregular and invariable plurals (`uomo → uomini`, `uovo → uova`, `città`, `bar`) are tabled.
- **Conjugation** is present indicative only. All `-iare` verbs drop the i before an i-ending (`studiare → studi`, `mangiare → mangiamo`); the stressed type (`sciare → scii`, `inviare → invii`) is listed as irregular instead. `-care`/`-gare` insert h (`cercare → cerchi`).
- Irregulars are tabled, including the `-urre`/`-orre` contracted infinitives (`condurre`, `produrre`, `proporre`), `-gliere` verbs (`togliere → tolgo`), and `tenere` compounds.

## The two special drills

Curated sentence banks in `VOCAB_DATA.special`, ids outside the `it####` space. Both are **verb** drills, so `specialModeAllowed` maps both onto the Word-forms "Verbs" toggle. Each item stores an explicit `wrong` counterpart (unlike Spanish's por/para, which derives it in-engine), plus a `note` that rides on the correct option as its gloss and is revealed after answering.

1. **`essere_stare`** (45 items, ids `est###`). **Italian is not Spanish** — do not port the ser/estar split. Italian `essere` covers most of what Spanish divides, *including location and temporary states*: `sono a Roma`, `sono stanco`, `sono felice`. `stare` is reserved for:
   - health/wellbeing — `come stai?`, `sto bene`, `sta male`
   - the progressive — `sto mangiando`, `sta arrivando`
   - `stare per` + infinitive (about to) — `sto per uscire`
   - fixed expressions — `stare attento / zitto / fermo / tranquillo / in piedi`
   - clothes fitting or suiting — `ti sta bene`, `mi stanno strette`
   - staying/remaining somewhere — `sto a casa`, `quanto stai a Roma?`
2. **`avere_essere`** (44 items, ids `aux###`) — auxiliary choice in the passato prossimo. `essere` for intransitive motion/change-of-state verbs (`andare`, `venire`, `partire`, `nascere`, `morire`, `diventare`), all reflexives, and `piacere`/`succedere`/`sembrare`/`riuscire`/`costare`/`mancare`/`bastare`. `avere` for transitives and most other intransitives (`dormire`, `camminare`, `viaggiare`, `telefonare`).

## Engine differences vs Spanish

Field names `it`/`en`; mode keys `it_en`/`en_it`; localStorage `italian_trainer_progress` / `_lessons` / `_pos`. `DECL_LABELS` uses `m_sg` (not Spanish's `m_sg_nom`) as the skipped headword key. Accents à è ì ò ù î added to `DIACRITIC_MAP` *and* to the `stripDiacritics` character class. **`FILLER` is `{to, a, an, the}`, not the Spanish reflexive list** — `ci`, `vi` and `si` are real Italian words; stripping is also guarded so it can never empty an answer.

## State of the deck (v1)

- **1186 entries**: 536 nouns, 289 verbs, 176 adjectives, 74 adverbs, 26 numbers, 22 prepositions, 22 phrases, 21 pronouns, 20 conjunctions. 16 lessons.
- **Cloze: 80 words × 2 sentences (160)**. Antonyms 58 pairs, synonyms 28 pairs.
- 11 drill modes: `it_en, en_it, conjugate, decline, noun_case, antonym, synonym, multiple_choice, cloze, essere_stare, avere_essere`.

## What's next

1. **Passato prossimo as a second tense layer** — the biggest gap. The Latin trainer already has two-level `conjugation` (`{tense: {person: form}}`); porting that shape here would give present + passato prossimo, and pairs naturally with the `avere_essere` drill.
2. Past participles as their own field (needed for 1, and irregular enough — `fatto`, `detto`, `preso`, `scritto` — to be worth drilling alone).
3. A third special drill: `sapere` vs `conoscere`, or the prepositions `a`/`in` with places. The engine generalises MC modes on `currentQ.choices`, so a new bank plus three registrations is all it takes.
4. Reflexive verbs as a marked class (`lavarsi`, `svegliarsi`) — currently absent.

## My preferences

Direct, concise, lead with the result; batch sizes as I specify; only apply corrections you're confident in, flag the rest; no blanket auto-sweeps on lexical morphology; always rebuild + validate before presenting files.
