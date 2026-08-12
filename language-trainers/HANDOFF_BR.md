# Brazilian trainer — handoff

`brazilian_trainer.html` + `vocab_br.json` — **Brazilian Portuguese** with the
European forms marked. 921 entries, 24 lessons, 12 drill types, 5 special banks
(99 items), 223 cloze sentences, 52 marked variants.

Full parity with `portuguese_trainer.html`: same engine, same drill types, same
deck size. Read `HANDOFF_PT.md` first — everything there about the personal
infinitive, the future subjunctive, the spelling oracle and the homograph rule
applies here unchanged. This file covers only what is different.

## One curated source, two decks

`scripts/build_portuguese_vocab.py` runs twice, `build("eu")` and `build("br")`,
and `scripts/make_portuguese_trainer.py` generates both apps from the same
Spanish parent. There is no second word list to keep in step, so the two decks
**cannot** drift: a word added for Portugal appears in Brazil the same run.

`BR_VARIANTS` is the only place the two varieties are named, and it is read in
both directions. In the European deck the entry keeps `comboio` and carries
`alt: "trem"`; in the Brazilian deck it keeps `trem` and carries
`alt: "comboio"`. The reveal panel labels them from `VARIANT_PRIMARY` /
`VARIANT_OTHER`, so the Brazilian app shows **Brasil: trem · Portugal: comboio**
and the European one shows the same pair the other way round. Both grade exact
in both apps.

## Four persons, not five

Brazil's paradigm is **eu / você·ele·ela / nós / vocês·eles·elas**. *Você* is the
ordinary second person and takes third-person verb forms, so `tu` and `ele` are
one slot rather than two, and drilling *tu falas* would teach a shape most
Brazilians never write.

That is a real re-slotting, not a relabelling: `conjugate_br`,
`personal_infinitive_br` and `future_subjunctive_br` in `portuguese_morph.py`
rebuild the dict with the four keys, and `check_portuguese.py` asserts the
count per app — five for Portugal, four for Brazil — and fails if any verb has
a form under a key no pronoun label names.

## What gets rewritten for Brazil

Four kinds of change, each with its own map and its own guard:

| Map | Rewrites | Example |
|---|---|---|
| `BR_VARIANTS` | headwords, both ways | comboio ↔ trem |
| `BR_SENTENCES` | cloze and bank sentences | `Dói-me a {cabeça}` → `Minha {cabeça} está doendo` |
| `BR_NOTES` | the note explaining the sentence | "estar a + infinitive" → "estar + gerund" |
| `BR_WRONG` | a bank item's distractor | ff009's trap becomes `apelido` |

`BR_NOTES` and `BR_WRONG` exist because rewriting the sentence alone was not
enough. The progressive card showed `{Estou} aprendendo português` above the
note *"estar a + infinitive is the progressive"* — teaching the construction it
had just replaced. Same for the personal-infinitive card whose sentence became
`Antes de você {comer}` while the note still explained "the -es ending marks tu".
`check_br_sentences` now scans notes as well as sentences, which is how both
were found.

## Everything derived is recomputed from the Brazilian headword

Swapping `pt` alone leaves the European morphology attached, and the decline
drill then asks for the feminine of `marrom` and answers `castanha` — which is
neither variety's word for the thing. So a swap recomputes:

- **nouns** — `trem`/`trens`, not `comboios` (multi-word ones come from
  `BR_COMPOUND_PLURALS`);
- **adjectives** — `marrom` is invariable for gender where `castanho` has
  `castanha`, and `cinza` is invariable outright;
- **verbs** — `baixar` conjugates as `baixo`, not `descarrego`;
- **the gloss marker** — `train (PT)` becomes `train (BR)`, because the marker
  names the variety the headword belongs to. `check_markers` fails on any
  paired entry whose gloss names the other variety.

## The guard is derived, not hand-listed

`EU_ONLY` fails the build on any European-only construction surviving into the
Brazilian deck: enclisis, `estar a` + infinitive, `tu`, the article before a
possessive, and European vocabulary.

The vocabulary pattern is **built from `BR_VARIANTS` itself** rather than
written out, because a hand-written list only catches the words someone
remembered. The original listed four words and missed
`Se falarmos devagar, ele percebe` sitting in the future-subjunctive bank with
Portugal's verb in it. Deriving it turned up 26 items in one run — twelve
sentences with an article before a possessive, four `depressa`, and the
false-friend card asking `Qual é o teu {apelido}?` for "surname", which in
Brazil means *nickname*.

Two allowlists keep it honest rather than absolute, each entry with a reason:
`EU_VOCAB_OK` for words the pattern flags that are current in Brazil anyway
(`passeio`, `bilhete`, `casaco`, `gelado`, `esquisito`), and `EU_TEXT_OK` for
whole texts that name a European word on purpose — the false-friend notes do,
and `qual é o seu nome?` keeps its article in Brazil too.

## What a browser caught that no validator did

Both apps passed `validate.py` and `check_portuguese.py` while showing, on the
first card of a decline drill, `fem. pl. (las ... )`. `DECL_LABELS` and
`NOUN_LABELS` are prose, not field names, so the `.es` → `.pt` rename walked
straight past them and both apps shipped Spanish articles. They are now
rewritten by the generator and `check_portuguese.py` fails on any label
matching `el|la|los|las`.

The same screenshot pass found the shared diacritic map — Polish, German and
Spanish letters — had **none of Portuguese's own**. `coracao` was two edits from
`coração` and graded plain **wrong**, on the two accents the language uses most.
Seven accent-only pairs are now asserted to grade `diacritic`.

## Commands

```
python3 scripts/portuguese_morph.py            # paradigm self-check, both paradigms
python3 scripts/build_portuguese_vocab.py      # writes vocab_pt.json AND vocab_br.json
python3 scripts/make_portuguese_trainer.py     # writes both apps, both SWs, both manifests
python3 scripts/make_icons.py --check          # the icon recipe still matches what shipped
python3 scripts/validate.py brazilian_trainer.html
python3 scripts/check_portuguese.py            # runs over BOTH apps
python3 ../scripts/build_index.py              # hub counts
```

## Known gaps

- **`você` only.** Brazilian `tu` is real in the south and the northeast, with
  third-person verb forms in most of that usage. The deck teaches the national
  standard and does not mark the regional second person at all.
- **No `a gente`**, which is how most Brazilians say "we" in speech. The deck
  drills `nós` because that is what the paradigm needs, so the most common
  spoken subject pronoun is absent.
- **Four entries name a variety without being a swapped pair** —
  `conduzir`/`dirigir` and `tu`/`você`, all four deliberate. Two more,
  `nevoeiro` and `bilheteira`, were marked European by mistake and were only
  found because the marker check demanded that every marker be true.
- The false-friend bank is still aimed at **Spanish** interference, which is the
  right target in Portugal and a less common one in Brazil.
- Only the present indicative is drilled, as in every deck in this family.
