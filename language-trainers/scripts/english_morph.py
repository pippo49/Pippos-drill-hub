#!/usr/bin/env python3
"""Expand English headwords into the forms the trainer drills.

Unlike Polish/Latin/Italian, English has almost no inflectional morphology to
get wrong: no grammatical gender, no case system, and adjectives don't agree
with anything. What IS worth drilling is the handful of places English spelling
or vocabulary genuinely surprises a learner:

- third-person -s/-es/-ies on the present tense (and the handful of verbs that
  don't follow it at all: be, have),
- irregular past/participle pairs (go/went/gone), which is where the real verb
  difficulty lives, not in person-by-person conjugation,
- irregular or re-spelled plurals (child/children, city/cities, leaf/leaves),
- which adjectives take -er/-est and which take more/most, plus the few that
  are irregular outright (good/better/best).

Regular forms are DERIVED here so the curated word list in build_english_vocab.py
only has to say what's irregular. Every override table is cross-checked against
the word list that actually uses it (build_english_vocab.py calls `check_unused`)
so a typo'd or orphaned override fails the build instead of silently doing
nothing -- the same principle as latin_morph.py's principal-parts cross-check.
"""
import re

# === Present tense: regular spelling rule for the 3rd person singular =======
# consonant+y -> ies; s/x/z/ch/sh/o -> +es; else +s. ("go" and "do" fall out of
# the -o rule for free, which is why they're not irregular here -- only their
# PAST/PARTICIPLE is irregular, handled separately below.)
def third_person(base):
    if re.search(r'[^aeiou]y$', base):
        return base[:-1] + "ies"
    if re.search(r'(s|x|z|ch|sh|o)$', base):
        return base + "es"
    return base + "s"


# Verbs whose PRESENT TENSE doesn't follow the regular pattern at all -- not
# just the 3rd person. "be" is the only English verb with more than two present
# forms; "have" only breaks the 3rd person (has, not haves).
IRREGULAR_PRESENT = {
    "be": {"i": "am", "you": "are", "he_she_it": "is", "we": "are", "they": "are"},
    "have": {"he_she_it": "has"},
}

PERSONS = ["i", "you", "he_she_it", "we", "they"]


def conjugate_present(base):
    """{person: form} for the present tense. `base` carries no "to "."""
    forms = {p: base for p in PERSONS}
    forms["he_she_it"] = third_person(base)
    forms.update(IRREGULAR_PRESENT.get(base, {}))
    return forms


# === Principal parts: only authored for verbs whose past/participle is
# irregular. Regular verbs (base+ed twice) are not worth a drill -- the rule
# has no exceptions to catch a learner out, so no principal_parts field is
# generated for them at all and the mode simply doesn't offer them.
# "be" is deliberately absent: its past splits by person (was/were), which
# doesn't fit the single-answer principal-parts shape, and its present
# (am/is/are) is already drilled by `conjugate`.
IRREGULAR_PAST_PARTICIPLE = {
    "go": ("went", "gone"),
    "do": ("did", "done"),
    "have": ("had", "had"),
    "eat": ("ate", "eaten"),
    "drink": ("drank", "drunk"),
    "see": ("saw", "seen"),
    "give": ("gave", "given"),
    "take": ("took", "taken"),
    "make": ("made", "made"),
    "come": ("came", "come"),
    "get": ("got", "gotten"),
    "know": ("knew", "known"),
    "think": ("thought", "thought"),
    "say": ("said", "said"),
    "speak": ("spoke", "spoken"),
    "write": ("wrote", "written"),
    "read": ("read", "read"),
    "buy": ("bought", "bought"),
    "sell": ("sold", "sold"),
    "bring": ("brought", "brought"),
    "find": ("found", "found"),
    "sleep": ("slept", "slept"),
    "wake": ("woke", "woken"),
    "run": ("ran", "run"),
    "swim": ("swam", "swum"),
    "fly": ("flew", "flown"),
    "drive": ("drove", "driven"),
    "ride": ("rode", "ridden"),
    "fall": ("fell", "fallen"),
    "feel": ("felt", "felt"),
    "keep": ("kept", "kept"),
    "leave": ("left", "left"),
    "lose": ("lost", "lost"),
    "meet": ("met", "met"),
    "pay": ("paid", "paid"),
    "put": ("put", "put"),
    "send": ("sent", "sent"),
    "sit": ("sat", "sat"),
    "stand": ("stood", "stood"),
    "teach": ("taught", "taught"),
    "tell": ("told", "told"),
    "understand": ("understood", "understood"),
    "wear": ("wore", "worn"),
    "win": ("won", "won"),
    "begin": ("began", "begun"),
    "break": ("broke", "broken"),
    "build": ("built", "built"),
    "catch": ("caught", "caught"),
    "choose": ("chose", "chosen"),
    "cut": ("cut", "cut"),
    "draw": ("drew", "drawn"),
    "feed": ("fed", "fed"),
    "fight": ("fought", "fought"),
    "forget": ("forgot", "forgotten"),
    "grow": ("grew", "grown"),
    "hear": ("heard", "heard"),
    "hold": ("held", "held"),
    "hurt": ("hurt", "hurt"),
    "let": ("let", "let"),
    "light": ("lit", "lit"),
    "lend": ("lent", "lent"),
    "ring": ("rang", "rung"),
    "rise": ("rose", "risen"),
    "shine": ("shone", "shone"),
    "shoot": ("shot", "shot"),
    "shut": ("shut", "shut"),
    "sing": ("sang", "sung"),
    "spend": ("spent", "spent"),
    "steal": ("stole", "stolen"),
    "throw": ("threw", "thrown"),
}


def principal_parts(base):
    """[base, past, participle], or None for a regular verb (not drilled)."""
    irr = IRREGULAR_PAST_PARTICIPLE.get(base)
    if not irr:
        return None
    return [base, irr[0], irr[1]]


# === Plurals: only authored on nouns where the form is worth drilling -- a
# true irregular (child/children), a spelling-changing regular (city/cities,
# leaf/leaves), or a learnable-but-easy-to-miss -o exception (potato/potatoes
# against photo/photos). Fully predictable plurals (cat/cats) get no `plural`
# field, and the drill mode simply never asks about them.
IRREGULAR_PLURAL = {
    "child": "children", "person": "people", "man": "men", "woman": "women",
    "foot": "feet", "tooth": "teeth", "mouse": "mice", "goose": "geese",
    "sheep": "sheep", "fish": "fish",
}


def regular_plural(base):
    if re.search(r'[^aeiou]y$', base):
        return base[:-1] + "ies"
    if re.search(r'(s|x|z|ch|sh)$', base):
        return base + "es"
    if re.search(r'(f)$', base):
        return base[:-1] + "ves"
    if re.search(r'fe$', base):
        return base[:-2] + "ves"
    return base + "s"


def plural_of(base, irregular=False):
    """Only called for nouns worth drilling; `irregular` picks the override
    table, otherwise the regular-but-spelling-changing rule applies."""
    if irregular:
        if base not in IRREGULAR_PLURAL:
            raise AssertionError(f"plural_of: {base!r} marked irregular but not in IRREGULAR_PLURAL")
        return IRREGULAR_PLURAL[base]
    return regular_plural(base)


# === Adjective comparison: comparative/superlative. `degree` picks the shape:
#   "er"    -- suffix, with the regular spelling changes (doubling, y->i, bare -r/-st)
#   "more"  -- periphrastic (more/most), the default for most 2+ syllable adjectives
#   explicit (comparative, superlative) tuple -- the handful of true irregulars
IRREGULAR_COMPARISON = {
    "good": ("better", "best"),
    "bad": ("worse", "worst"),
    "far": ("further", "furthest"),
    "little": ("less", "least"),
    "much": ("more", "most"),
    "many": ("more", "most"),
}

_DOUBLING = {"big", "hot", "fat", "thin", "sad", "wet", "fit", "slim", "red"}


def comparison_forms(base, degree="more"):
    if base in IRREGULAR_COMPARISON:
        comp, sup = IRREGULAR_COMPARISON[base]
        return [comp, sup]
    if degree == "more":
        return [f"more {base}", f"most {base}"]
    if degree == "er":
        if base in _DOUBLING:
            return [base + base[-1] + "er", base + base[-1] + "est"]
        if re.search(r'[^aeiou]y$', base):
            stem = base[:-1] + "i"
            return [stem + "er", stem + "est"]
        if base.endswith("e"):
            return [base + "r", base + "st"]
        return [base + "er", base + "est"]
    raise AssertionError(f"comparison_forms: unknown degree {degree!r} for {base!r}")


def check_unused(used_bases, table, table_name):
    """Every entry in an override table must be referenced by some word in the
    curated list, or it's dead weight nobody will ever see drilled (and might
    be a typo hiding a word that's still getting the wrong, regular form)."""
    orphans = set(table) - set(used_bases)
    if orphans:
        raise AssertionError(f"{table_name}: entries never used by the word list: {sorted(orphans)}")
