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
