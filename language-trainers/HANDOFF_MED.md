# Medical terminology trainer — handoff

`medical_trainer.html` + `vocab_med.json` — Latin **and** Greek word-building for
medicine students. 870 entries, 22 lessons, 11 drill types.

## Why one deck and not two

Latin and Greek are deliberately in the same app. Clinical vocabulary mixes them
in a single term (*hypo-* Gk + *glyc-* Gk + *-aemia* Gk, but *cardiovascular* is
Gk + L), and the **Greek/Latin doublet** — `nephr/o` vs `ren/o`, `ophthalm/o` vs
`ocul/o` — is one of the things students are examined on and reliably get wrong.
The rule of thumb the deck teaches: the Greek form usually builds the
pathology/surgery word (*nephrectomy*), the Latin form the plain anatomical
adjective (*renal artery*). Splitting the languages would hide exactly that.

Every root carries `origin`, and the `doublet` drill asks for the other side.
**45 doublets.** Sixteen of those were added after a report that bone appeared as
Greek `oste/o` only — Latin *os, ossis* gives `oss/e-` (osseous, ossicle). An
audit for glosses where Greek and Latin both name the same structure found the
rest: ten Latin roots were missing entirely (`oss/e`, `sanguin/o`, `capit/o`,
`nerv/o`, `medull/o`, `corpor/o`, `aqu/e`, `calcul/o`, `test/o`, `glandul/o`) and
six pairs were both present but never linked (cell, white, sound, tendon, bile,
abdomen). Worth re-running that audit after adding roots — the drill can only
ask the pairs that are linked.

## Drill types, and why they differ from the conversational trainers

The Spanish/Italian/French apps drill translation and inflection. Medical
terminology is a different skill — decomposing an unfamiliar term and building a
correct one — so the modes are different:

| Mode | Asks |
|---|---|
| Element → meaning | `-ectomy` → surgical removal |
| Meaning → element | inflammation → `-itis` |
| Term → meaning | *hepatomegaly* → enlargement of the liver |
| **Build the term** | "inflammation of the stomach" → *gastritis* |
| **Break it down** | in *gastroenterology*, which element means "intestine"? |
| **Greek ↔ Latin** | `nephr/o` is Greek; give the Latin form |
| Plurals | *diagnosis* → *diagnoses*; *vertebra* → *vertebrae* |
| Easily confused | a two-way forced choice: *ilium* vs *ileum* |
| Prescription Latin | `p.r.n.` → as needed; *pro re nata* → `p.r.n.` |
| Multiple choice | recognition, either direction |
| Clinical context | a cloze sentence from real clinical prose |

Deliberate choices:

- **Break it down asks for ONE element, not the whole decomposition.** Grading a
  free-typed "gastr/o + enter/o + -logy" needs a normaliser so loose that
  retyping the term itself would pass, which defeats the exercise.
- **Easily confused is a two-option forced choice.** The first version padded it
  to four with terms from other pairs and produced incoherent options (a root
  against two suffixes). The pair *is* the question.
- **Prescription Latin withholds the Latin** when asking for the meaning — it
  would give the answer away — and shows it in the reveal panel instead.

## The notation is explained on the page

Reported: *"hydr/o — is one the stem and the other the masculine ending?"* It is
not, and nothing in the app said so, which left a reasonable guess with nowhere
to be corrected. A permanent note under the deck summary now explains that the
slash marks a **combining vowel** — a linker with no meaning and no gender,
dropped before a vowel-initial element, usually `o` from Greek but `i` or `e`
on Latin roots (`dent/i`, `chol/e`), and optional when typing an answer.

The confusion is understandable: Latin `-us` *is* a masculine ending, and the
deck carries `-us` as a suffix. The difference is position — a real ending
closes a finished word, a combining vowel sits between two elements.

## Greek or Latin — shown on every element and on the word

The reveal panel labels the origin of each element and of the word as a whole:

```
Elements
  appendic/o    appendix        — Latin
  -itis         inflammation    — Greek
Word origin
  Hybrid — Greek + Latin
  A Latin stem with a Greek ending — the usual shape.
```

A term's origin is **derived from its parts**, not authored, so it cannot drift
out of step with the breakdown: all-Greek elements give "Greek throughout",
all-Latin "Latin throughout", and a mix is flagged as a hybrid with the pattern
named (Latin stem + Greek ending, or the reverse). The two terms with no parts
(*jaundice*, *diverticulitis*) carry an explicit origin in `CLOZE_ONLY`.

Current split: **237 Greek · 41 hybrid · 1 Latin**. Hybrids are worth flagging
rather than hiding — *appendicitis*, *vasectomy*, *quadriplegia*, *nocturia* and
*sinusitis* all pair a Latin stem with a Greek ending, which is why they look
irregular beside Greek-throughout neighbours like *gastritis*.

Origin is shown only **after** answering, so it never hints at the answer.

## Terms cited inside a note are glossed too

The notes illustrate an element with real words — "-ectomy … Appendectomy,
nephrectomy". Those are now listed with their meanings, so nothing in an
explanation is left for the learner to guess:

```
Notes
  Gk ektome 'a cutting out'. Appendectomy, nephrectomy.
Terms used above
  Appendectomy    surgical removal of the appendix
  nephrectomy     surgical removal of a kidney
```

496 citations across 309 notes. Most resolve against the deck itself — an entry,
its plural, or the same word in the other spelling convention (the notes are
written in British English, the deck headwords are American, so `haematuria`
finds `hematuria`). The rest come from `scripts/med_examples.py`.

**The build fails if a note cites a medical term with no gloss anywhere.** That
is the point of the assertion: it is not possible to add a note mentioning an
unexplained term and have it ship. Fixing it means either adding the gloss to
`EXAMPLE_GLOSSARY`, listing the word in `NOT_TERMS` (ordinary English, or a
Greek/Latin etymon the sentence already explains), or rewording the note.
Verified by deleting a gloss and watching the build refuse.

## Clinical terms inside a cloze sentence are glossed too

A cloze sentence is real clinical prose, so it uses vocabulary beyond the answer.
Those words are listed with the sentence that used them:

```
Migratory right iliac fossa pain is the classic history of _____.

Other terms in this sentence
  Migratory     moving from one site to another over time
  iliac fossa   the lower quarter of the abdomen on either side
```

84 terms across 47 of the 60 sentences. Unlike the note citations these cannot be
found by a suffix — *febrile*, *erythema*, *melaena*, *rigidity* are not built
from elements — so `CLINICAL_GLOSSARY` in `scripts/med_examples.py` curates them,
and the deck's own entries are folded in on top.

Matching is **phrase-first and word-bounded**: `iliac fossa` wins over a bare
`fossa`, `costal margin` over `costal`, and `media` does not match inside
`immediate`. Overlaps are resolved by preferring the longer phrase, and the
answer itself is never listed. Terms attach to the **sentence**, not the entry,
so a card only ever shows the words actually in front of the learner.

### The cloze vocabulary is closed — new sentences cannot smuggle a term in

Clinical prose words cannot be recognised by a suffix the way `-itis` can, so
rather than guess at a pattern, **every word in every cloze sentence must be
classified**: it either has a gloss, or it is listed in `ORDINARY_WORDS` as
everyday English. The build fails on anything else, naming the word *and the
sentence it appeared in*.

That makes adding sentences safe: write one, run the build, and it tells you
exactly which words need a decision. Verified both ways — a sentence containing
`tachyphylaxis` is refused, one using only classified vocabulary builds.

`ORDINARY_WORDS` (199 words) was generated once from the deck's own sentences and
then read through by hand; that review is what promoted `acute`, `red flag`,
`frequency`, `discharge`, `dominant hemisphere`, `ecg` and ten others out of it
and into `CLINICAL_GLOSSARY`. Extend it deliberately — adding a word there to
silence a failure you have not read defeats the point.

**The notes are guarded differently.** Their citations *are* morphologically
detectable, so the suffix check covers them (see above); a closed vocabulary
would mean classifying 1,440 words of ordinary prose for very little gain.

## Generated deck — do not hand-edit `vocab_med.json`

Curated data lives in `scripts/med_elements.py` (prefixes, suffixes, roots,
doublets) and `scripts/med_terms.py` (built terms, plurals, confusables, anatomy,
prescription Latin, cloze). Rebuild with:

```
python3 scripts/build_medical_vocab.py     # regenerates vocab_med.json
python3 scripts/rebuild.py medical_trainer.html vocab_med.json
python3 scripts/validate.py medical_trainer.html
```

`build_medical_vocab.py` is assert-guarded, like the Latin and Italian
generators. The check that earns its keep is **segment_ok**: every term's
authored `parts` must actually be able to spell that term, allowing the real
combining-vowel and elision rules (`gastr/o` + `-itis` → *gastritis*, keeping the
o before a consonant, dropping it before a vowel; `hypo-` + `ox/i` + `-ia` →
*hypoxia*). It rejects a wrong root, a wrong order, an extra or missing part, and
`-ectomy`/`-ostomy` swaps — verified against deliberate errors. It also enforces
unique element forms, both halves of every doublet existing with opposite
origins, and one well-formed `{brace}` per cloze sentence naming a real entry.

Two terms could not be expressed under the rule and were changed rather than
given an exception: *iritis* (needs `irid-` → `ir-`, a two-letter loss) became
*iridectomy*, and *endometriosis* uses the `metri/o` stem.

## The trainer is generated too

`medical_trainer.html` is built from `latin_trainer.html` by
`scripts/make_medical_trainer.py`, which swaps in the modes, `selectionCanAsk`,
the extras panel, the labels and the branding. Engine fixes made in the Latin
trainer flow here on the next run — so **edit the script, not the HTML**.

Two engine changes are medical-only and applied by that script:

- **`gradeAnswer` splits alternatives on comma only, not comma-or-slash.** In the
  Latin deck `a / b` lists alternative answers; here a combining form *is*
  spelled with a slash, so the shared version tore `trich/o` into `trich` and `o`
  and graded a perfectly typed answer as a typo. Caught in a browser, not by the
  validator, which only checks that a question can be generated.
- The deck-summary pluraliser gained real plurals (its `p + "s"` fallback
  produced "suffixs" and "prefixs").

Answers accept an element with or without its notation: `cardi/o`, `cardio` and
`cardi` all grade exact, as do `-ectomy` and `ectomy`. Where several elements
share a gloss (`nephr/o` and `ren/o` are both "kidney") the meaning→element drill
accepts any of them.

## Known gaps

- Deponent-style irregulars aside, the deck has no eponyms (Fallot, Crohn) — they
  are not Latin/Greek word-building and would not drill the same skill.
- Spelling follows the American convention (*anemia*, *esophagus*, *edema*),
  matching most textbooks; the British forms are not currently accepted as
  alternatives. Adding them means an `acceptableAnswers` variant list, not a
  second deck.
- No filter dimension for origin (Greek vs Latin). The three-filter engine is
  proven; a fourth needs threading through `buildPool`, both `selectionCanAsk`
  call sites and the empty-state chain (see `CLAUDE.md`).
