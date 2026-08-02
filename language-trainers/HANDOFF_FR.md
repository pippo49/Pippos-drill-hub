# French trainer — handoff

Self-contained French→English trainer (single HTML file, same engine family as the Spanish and Italian trainers, PWA-ready, used on iPhone). English is the reference/answer language. Level A1–A2, **focused on small talk**. Keep responses concise — lead with results; I spot-check errors myself.

## What "small talk focus" means here

This is the one thing that makes this deck different from the others, so preserve it when expanding:

- **Lessons are conversational situations**, not topic buckets: 1 greetings & introductions · 2 politeness · 3 how are you / feelings · 4 weather · 5 family & personal life · 6 work & studies · 7 free time & weekend · 8 food & eating out · 9 travel · 10 home · 11 opinions & agreeing · 12 plans & invitations · 13 numbers, time & dates · 14 core verbs · 15 adjectives & adverbs · 16 conversation fillers & connectors.
- **Phrases are a first-class category, not an afterthought.** 181 of the 1014 entries are ready-made phrases — the units you actually say (`ça va ?`, `quoi de neuf ?`, `tant pis`, `du coup`, `bref`). For comparison the Spanish deck has 12 and the Italian 22. Keep adding phrases at roughly this share.
- **Cloze sentences are lines of dialogue**, not textbook examples.
- **Both special drills are the ones small talk actually turns on** (below).

## The data is generated — never hand-edit `vocab_fr.json`

```
python3 scripts/french_morph.py         # rule self-check
python3 scripts/build_french_vocab.py   # regenerates vocab_fr.json
python3 scripts/rebuild.py french_trainer.html vocab_fr.json
python3 scripts/validate.py french_trainer.html
```

## Source format

- **Phrases**: `(French, English, lesson)` — the biggest list, and deliberately first in the file.
- **Nouns**: `(word, gender, English, lesson[, explicit plural])`. The plural is generated; give it explicitly only to *assert* a curated form.
- **Verbs**: `(infinitive, English, lesson[, group][, stem_changes])`. `group` is `"er"`/`"ir"`(finir)/`"ir2"`(partir)/`"re"`, inferred when omitted. `stem_changes` is a `{person: form}` override for the lexical e-è / é-è verbs (`acheter → j'achète`) and for reflexives, whose forms carry their pronoun (`se lever → je me lève`).
- **Adjectives**: `(masc sg, English, lesson[, explicit feminine][, invariable])`.
- **Everything else**: `(French, English, pos, lesson)`.
- **`CLOZE` / `ANTONYMS` / `SYNONYMS`**: as in the other decks.

**English glosses are written without articles** ("house", not "the house") — see the FILLER note below.

## Generator notes (`french_morph.py`)

- **Aspirate h is curated** (`ASPIRATE_H`): it is not recoverable from spelling and decides both the article and elision — `le héros` but `l'hôtel`.
- **Plurals**: `-s/-x/-z` invariable; `-al → -aux` except `AL_TAKES_S` (bal, festival…); `-ail → -s` except `AIL_TAKES_AUX` (travail → travaux); `-eau/-au/-eu → -x` except `EU_TAKES_S` (pneu, bleu); irregulars (`œil → yeux`, `ciel → cieux`).
- **Feminines**: rules for `-er → -ère`, `-x → -se`, `-f → -ve`, `-eur → -euse`, and doubling before `-e` (`bon → bonne`), plus `IRREGULAR_FEMININE` (beau/belle, vieux/vieille, blanc/blanche, long/longue…) and `ET_TAKES_GRAVE` (complet → complète).
- **Conjugation** is present indicative only. The `partir` type needs **two stems** — the singular drops the stem-final consonant (`part- → je pars`) while the plural keeps it (`nous partons`) — so it cannot be expressed as one ending list and lives outside `REGULAR_ENDINGS`. Spelling shifts handled: `-ger → -geons`, `-cer → -çons`, `-yer → -ie-`.
- **Impersonal verbs** (`falloir`, `pleuvoir`) are listed in `IMPERSONAL` and get **no** `conjugation`, so the Conjugate drill skips them rather than asking for a nonexistent `je` form.

## Engine differences

- Field names `fr`/`en`; modes `fr_en`/`en_fr`; localStorage `french_trainer_*`.
- **`FILLER` is `{to}` only** — *not* the Italian `{to, a, an, the}`. French answers legitimately contain a bare `a` (`il a`, `il y a`), and stripping it would corrupt them. English glosses therefore omit articles. Apostrophes are never stripped: `l'`, `d'`, `j'` are word forms.
- Accents, `ç`, and the `œ`/`æ` ligatures are in `DIACRITIC_MAP` *and* the `stripDiacritics` character class, so `coeur` scores full credit for `cœur`.
- **The Conjugate drill accepts the pronoun-prefixed answer too** — both `ai` and `j'ai` — since a French form is rarely written without its subject. `j'` elision is applied when the form starts with a vowel.

## The two special drills

Both are **verb** drills, so both follow the Word-forms "Verbs" toggle via `specialModeAllowed`. Each item stores an explicit `wrong` counterpart plus a `note` that rides on the correct option and is revealed after answering.

1. **`tu_vous`** (30 items, ids `tv###`) — the register decision. Covers: strangers and titles vs first-name terms; workplace hierarchy; family and partners; service staff; **`vous` as the plural of `tu`** (friends, but more than one); possessives and object pronouns following the register (`ton`/`votre`, `te`/`vous`); imperatives; and the moment of switching (`on se tutoie ?`).
2. **`avoir_etre`** (40 items, ids `ae###`) — the passé composé auxiliary. `être` for the DR & MRS VANDERTRAMP motion/change-of-state verbs and **all reflexives**; `avoir` for transitives and most others. Includes the pairs that flip on whether there is a direct object: `elle est passée` vs `il a monté les valises`, `nous avons descendu la poubelle`, `elle a sorti son téléphone`.

## State of the deck (v1)

- **1014 entries**: 344 nouns, **181 phrases**, 168 verbs, 146 adjectives, 77 adverbs, 30 pronouns, 24 conjunctions, 24 numbers, 20 prepositions. 16 lessons.
- **Cloze: 84 words × 2 (168)**. Antonyms 55 pairs, synonyms 15 pairs.
- 11 drill modes: `fr_en, en_fr, conjugate, decline, noun_case, antonym, synonym, multiple_choice, cloze, tu_vous, avoir_etre`.

## What's next

1. **Passé composé as a second tense layer** — pairs naturally with the `avoir_etre` drill, and the Latin trainer already has the two-level `{tense: {person: form}}` shape to copy. Past participles would need their own field (they are irregular enough — `fait`, `dit`, `pris`, `écrit` — to be worth drilling alone).
2. A third special drill: **`c'est` vs `il est`**, which is arguably the next most common small-talk stumble. A new bank plus three registrations is all it takes.
3. Negation as a drill (`ne… pas / plus / jamais / rien`) — currently only present as vocabulary.
4. More phrases: the deck could carry twice as many without drifting off-level.

## My preferences

Direct, concise, lead with the result; batch sizes as I specify; only apply corrections you're confident in, flag the rest; no blanket auto-sweeps on lexical morphology; always rebuild + validate before presenting files.


## Answer acceptance (fixes from user feedback)

Reported: the drill marked correct answers wrong. Fixed in
`scripts/patch_grading.py`; `scripts/check_grading.py` is the regression test —
run it after any grading change.

- **Formal written English is accepted.** "it is" for "it's", "what is your
  name" for "what's your name?", "it does not matter" for "it doesn't matter",
  in both directions.
- **All three French question forms are accepted**, whichever the deck stores:
  intonation, `est-ce que`, and inversion — including reflexives
  (`comment tu t'appelles ?` <-> `comment t'appelles-tu ?`) and interrogative in
  situ (`qu'est-ce que ça veut dire ?` <-> `ça veut dire quoi ?`).
- **tu / vous / toi** are all accepted for "you", and where the deck holds both
  registers of a phrase as separate entries (`comment vas-tu ?` /
  `comment allez-vous ?`) either answers the other's prompt.
- **Feminine and plural adjective forms** are accepted for an EN→FR prompt that
  carries no gender or number.
- **Curated synonyms** are accepted for the same gloss.

The reveal line lists every accepted form, so the other correct answers are
still shown after answering.

Not fixable in the engine: a French word that is **not in the deck** cannot be
accepted. If a specific rejected answer should be valid, add it as an entry
sharing an English alternative with the existing one.
