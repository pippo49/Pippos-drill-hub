#!/usr/bin/env python3
"""Latin morphology generator: expands compact dictionary entries into the full
paradigms the trainer drills.

Nouns are keyed off the genitive singular (which is exactly how a school course
identifies the declension and the stem); verbs off their principal parts.
Everything is rule-based with explicit irregular tables — no guessing, and every
expansion is assert-guarded so a malformed input fails loudly rather than
silently producing a wrong form.

Macrons are authored in the source words and carried through the endings;
grading in the app is macron-insensitive, so they are display-only.
"""

PERSONS = ["s1", "s2", "s3", "p1", "p2", "p3"]
TENSES = ["present", "imperfect", "future", "perfect", "pluperfect", "future_perfect"]

# ----------------------------------------------------------------- NOUNS

# case-key -> ending, per declension. `None` means "same as the nominative
# singular headword" (the neuter rule: nom == acc, and 4th/5th quirks).
NOUN_ENDINGS = {
    1: {  # puella, puellae (f)
        "gen_sg": "ae", "dat_sg": "ae", "acc_sg": "am", "abl_sg": "ā",
        "nom_pl": "ae", "gen_pl": "ārum", "dat_pl": "īs", "acc_pl": "ās", "abl_pl": "īs",
    },
    2: {  # dominus, dominī (m) / bellum, bellī (n)
        "gen_sg": "ī", "dat_sg": "ō", "acc_sg": "um", "abl_sg": "ō",
        "nom_pl": "ī", "gen_pl": "ōrum", "dat_pl": "īs", "acc_pl": "ōs", "abl_pl": "īs",
    },
    3: {  # rēx, rēgis (m)
        "gen_sg": "is", "dat_sg": "ī", "acc_sg": "em", "abl_sg": "e",
        "nom_pl": "ēs", "gen_pl": "um", "dat_pl": "ibus", "acc_pl": "ēs", "abl_pl": "ibus",
    },
    4: {  # manus, manūs (f)
        "gen_sg": "ūs", "dat_sg": "uī", "acc_sg": "um", "abl_sg": "ū",
        "nom_pl": "ūs", "gen_pl": "uum", "dat_pl": "ibus", "acc_pl": "ūs", "abl_pl": "ibus",
    },
    5: {  # diēs, diēī (m)
        "gen_sg": "ēī", "dat_sg": "ēī", "acc_sg": "em", "abl_sg": "ē",
        "nom_pl": "ēs", "gen_pl": "ērum", "dat_pl": "ēbus", "acc_pl": "ēs", "abl_pl": "ēbus",
    },
}

# Overrides layered on top of the base table.
NEUTER_OVERRIDE = {
    2: {"acc_sg": None, "nom_pl": "a", "acc_pl": "a"},
    3: {"acc_sg": None, "nom_pl": "a", "acc_pl": "a"},
    4: {"acc_sg": None, "dat_sg": "ū", "nom_pl": "ua", "acc_pl": "ua"},
}
ISTEM_OVERRIDE = {"gen_pl": "ium"}
NEUTER_ISTEM_OVERRIDE = {"abl_sg": "ī", "nom_pl": "ia", "acc_pl": "ia", "gen_pl": "ium"}

# Nouns whose paradigm can't be derived (fully irregular or defective).
IRREGULAR_NOUNS = {
    "vīs": {"gen_sg": "vīs", "dat_sg": "vī", "acc_sg": "vim", "abl_sg": "vī",
            "nom_pl": "vīrēs", "gen_pl": "vīrium", "dat_pl": "vīribus",
            "acc_pl": "vīrēs", "abl_pl": "vīribus"},
    "domus": {"gen_sg": "domūs", "dat_sg": "domuī", "acc_sg": "domum", "abl_sg": "domō",
              "nom_pl": "domūs", "gen_pl": "domuum", "dat_pl": "domibus",
              "acc_pl": "domōs", "abl_pl": "domibus"},
    "deus": {"gen_sg": "deī", "dat_sg": "deō", "acc_sg": "deum", "abl_sg": "deō",
             "nom_pl": "dī", "gen_pl": "deōrum", "dat_pl": "dīs", "acc_pl": "deōs", "abl_pl": "dīs"},
    "Iuppiter": {"gen_sg": "Iovis", "dat_sg": "Iovī", "acc_sg": "Iovem", "abl_sg": "Iove"},
    "bōs": {"gen_sg": "bovis", "dat_sg": "bovī", "acc_sg": "bovem", "abl_sg": "bove",
            "nom_pl": "bovēs", "gen_pl": "boum", "dat_pl": "bōbus", "acc_pl": "bovēs", "abl_pl": "bōbus"},
    "iter": {"gen_sg": "itineris", "dat_sg": "itinerī", "acc_sg": "iter", "abl_sg": "itinere",
             "nom_pl": "itinera", "gen_pl": "itinerum", "dat_pl": "itineribus",
             "acc_pl": "itinera", "abl_pl": "itineribus"},
}

# (Plural-only nouns are declared per-entry via plural_only=True and supply
#  their genitive PLURAL instead of a genitive singular.)


def noun_stem(nom, gen, decl):
    """Stem from the genitive singular — the form a course teaches for exactly this."""
    endings = {1: "ae", 2: "ī", 3: "is", 4: "ūs", 5: ("ēī", "eī")}[decl]
    if decl == 5:
        for e in endings:
            if gen.endswith(e):
                return gen[: -len(e)]
        raise ValueError(f"5th-decl genitive {gen!r} ends in neither ēī nor eī")
    assert gen.endswith(endings), f"{nom}: {decl}-decl genitive {gen!r} should end in {endings!r}"
    return gen[: -len(endings)]


def plural_noun_stem(nom, gen_pl, decl):
    """Stem for a plural-only noun, taken from its genitive PLURAL (castra, castrōrum)."""
    candidates = {1: ("ārum",), 2: ("ōrum",), 3: ("ium", "um"),
                  4: ("uum",), 5: ("ērum",)}[decl]
    for e in candidates:
        if gen_pl.endswith(e):
            return gen_pl[: -len(e)]
    raise ValueError(f"{nom}: {decl}-decl genitive plural {gen_pl!r} ends in none of {candidates}")


def decline_noun(nom, gen, gender, decl, istem=False, plural_only=False):
    """Full case paradigm. Returns {case_key: form} (nominative sg is the headword).

    For plural_only nouns, `gen` is the genitive PLURAL and only plural forms
    are produced — they have no singular to decline.
    """
    if nom in IRREGULAR_NOUNS:
        return dict(IRREGULAR_NOUNS[nom])

    if plural_only:
        endings = dict(NOUN_ENDINGS[decl])
        if gender == "n":
            endings.update(NEUTER_OVERRIDE.get(decl, {}))
            if istem and decl == 3:
                endings.update(NEUTER_ISTEM_OVERRIDE)
        elif istem:
            endings.update(ISTEM_OVERRIDE)
        stem = plural_noun_stem(nom, gen, decl)
        out = {k: stem + e for k, e in endings.items() if k.endswith("_pl") and e is not None}
        assert out["nom_pl"] == nom, \
            f"{nom}: generated nom pl {out['nom_pl']!r} != headword {nom!r}"
        assert out["gen_pl"] == gen, \
            f"{nom}: generated gen pl {out['gen_pl']!r} != authored {gen!r}"
        return out

    endings = dict(NOUN_ENDINGS[decl])
    if gender == "n":
        endings.update(NEUTER_OVERRIDE.get(decl, {}))
        if istem and decl == 3:
            endings.update(NEUTER_ISTEM_OVERRIDE)
    elif istem:
        assert decl == 3, f"{nom}: i-stem only applies to 3rd declension"
        endings.update(ISTEM_OVERRIDE)

    stem = noun_stem(nom, gen, decl)
    if decl == 5:
        # gen/dat sg are -ēī after a vowel stem (diēī) but -eī after a
        # consonant (reī, fideī).
        e_ending = "ēī" if stem and stem[-1] in "aeiouāēīōū" else "eī"
        endings["gen_sg"] = e_ending
        endings["dat_sg"] = e_ending
    out = {}
    for case, end in endings.items():
        out[case] = nom if end is None else stem + end
    # The genitive singular we generate must match the one authored in the source.
    assert out["gen_sg"] == gen, f"{nom}: generated gen sg {out['gen_sg']!r} != authored {gen!r}"
    return out


# ----------------------------------------------------------------- VERBS

# Endings applied to the consonant base (= infinitive minus its last 3 chars).
PRESENT_STEM_ENDINGS = {
    1:      {"present":   ["ō", "ās", "at", "āmus", "ātis", "ant"],
             "imperfect": ["ābam", "ābās", "ābat", "ābāmus", "ābātis", "ābant"],
             "future":    ["ābō", "ābis", "ābit", "ābimus", "ābitis", "ābunt"]},
    2:      {"present":   ["eō", "ēs", "et", "ēmus", "ētis", "ent"],
             "imperfect": ["ēbam", "ēbās", "ēbat", "ēbāmus", "ēbātis", "ēbant"],
             "future":    ["ēbō", "ēbis", "ēbit", "ēbimus", "ēbitis", "ēbunt"]},
    3:      {"present":   ["ō", "is", "it", "imus", "itis", "unt"],
             "imperfect": ["ēbam", "ēbās", "ēbat", "ēbāmus", "ēbātis", "ēbant"],
             "future":    ["am", "ēs", "et", "ēmus", "ētis", "ent"]},
    "3io":  {"present":   ["iō", "is", "it", "imus", "itis", "iunt"],
             "imperfect": ["iēbam", "iēbās", "iēbat", "iēbāmus", "iēbātis", "iēbant"],
             "future":    ["iam", "iēs", "iet", "iēmus", "iētis", "ient"]},
    4:      {"present":   ["iō", "īs", "it", "īmus", "ītis", "iunt"],
             "imperfect": ["iēbam", "iēbās", "iēbat", "iēbāmus", "iēbātis", "iēbant"],
             "future":    ["iam", "iēs", "iet", "iēmus", "iētis", "ient"]},
}

# The perfect system is identical across all conjugations, built on the perfect stem.
PERFECT_STEM_ENDINGS = {
    "perfect":        ["ī", "istī", "it", "imus", "istis", "ērunt"],
    "pluperfect":     ["eram", "erās", "erat", "erāmus", "erātis", "erant"],
    "future_perfect": ["erō", "eris", "erit", "erimus", "eritis", "erint"],
}

IRREGULAR_VERBS = {
    "sum": {
        "present":   ["sum", "es", "est", "sumus", "estis", "sunt"],
        "imperfect": ["eram", "erās", "erat", "erāmus", "erātis", "erant"],
        "future":    ["erō", "eris", "erit", "erimus", "eritis", "erunt"],
    },
    "possum": {
        "present":   ["possum", "potes", "potest", "possumus", "potestis", "possunt"],
        "imperfect": ["poteram", "poterās", "poterat", "poterāmus", "poterātis", "poterant"],
        "future":    ["poterō", "poteris", "poterit", "poterimus", "poteritis", "poterunt"],
    },
    "eō": {
        "present":   ["eō", "īs", "it", "īmus", "ītis", "eunt"],
        "imperfect": ["ībam", "ībās", "ībat", "ībāmus", "ībātis", "ībant"],
        "future":    ["ībō", "ībis", "ībit", "ībimus", "ībitis", "ībunt"],
    },
    "ferō": {
        "present":   ["ferō", "fers", "fert", "ferimus", "fertis", "ferunt"],
        "imperfect": ["ferēbam", "ferēbās", "ferēbat", "ferēbāmus", "ferēbātis", "ferēbant"],
        "future":    ["feram", "ferēs", "feret", "ferēmus", "ferētis", "ferent"],
    },
    "volō": {
        "present":   ["volō", "vīs", "vult", "volumus", "vultis", "volunt"],
        "imperfect": ["volēbam", "volēbās", "volēbat", "volēbāmus", "volēbātis", "volēbant"],
        "future":    ["volam", "volēs", "volet", "volēmus", "volētis", "volent"],
    },
    "nōlō": {
        "present":   ["nōlō", "nōn vīs", "nōn vult", "nōlumus", "nōn vultis", "nōlunt"],
        "imperfect": ["nōlēbam", "nōlēbās", "nōlēbat", "nōlēbāmus", "nōlēbātis", "nōlēbant"],
        "future":    ["nōlam", "nōlēs", "nōlet", "nōlēmus", "nōlētis", "nōlent"],
    },
    "mālō": {
        "present":   ["mālō", "māvīs", "māvult", "mālumus", "māvultis", "mālunt"],
        "imperfect": ["mālēbam", "mālēbās", "mālēbat", "mālēbāmus", "mālēbātis", "mālēbant"],
        "future":    ["mālam", "mālēs", "mālet", "mālēmus", "mālētis", "mālent"],
    },
    "dō": {  # 1st conj but with a short a throughout
        "present":   ["dō", "dās", "dat", "damus", "datis", "dant"],
        "imperfect": ["dabam", "dabās", "dabat", "dabāmus", "dabātis", "dabant"],
        "future":    ["dabō", "dabis", "dabit", "dabimus", "dabitis", "dabunt"],
    },
}

# The perfect system is otherwise fully regular; these verbs contract in the
# 2nd person, where the regular rule would give iistī / iistis.
PERFECT_OVERRIDES = {
    "eō": {"perfect": ["iī", "īstī", "iit", "iimus", "īstis", "iērunt"]},
}

# Prefixed compounds of the irregular verbs: {compound 1sg: (prefix, base 1sg)}.
# Listed explicitly rather than matched by suffix, because a rule like
# "endswith('eō')" would wrongly capture every 2nd-conjugation verb (moneō,
# videō, habeō...). Expanded into the tables above at import time.
VERB_COMPOUNDS = {
    "abeō": ("ab", "eō"), "adeō": ("ad", "eō"), "exeō": ("ex", "eō"),
    "ineō": ("in", "eō"), "redeō": ("red", "eō"), "pereō": ("per", "eō"),
    "trānseō": ("trāns", "eō"),
    "absum": ("ab", "sum"), "adsum": ("ad", "sum"), "dēsum": ("dē", "sum"),
    "praesum": ("prae", "sum"), "īnsum": ("īn", "sum"),
    "afferō": ("af", "ferō"), "auferō": ("au", "ferō"), "cōnferō": ("cōn", "ferō"),
    "offerō": ("of", "ferō"), "referō": ("re", "ferō"), "īnferō": ("īn", "ferō"),
}

for _cmp, (_pre, _base) in VERB_COMPOUNDS.items():
    IRREGULAR_VERBS[_cmp] = {
        tense: [_pre + f for f in forms]
        for tense, forms in IRREGULAR_VERBS[_base].items()
    }
    if _base in PERFECT_OVERRIDES:
        PERFECT_OVERRIDES[_cmp] = {
            tense: [_pre + f for f in forms]
            for tense, forms in PERFECT_OVERRIDES[_base].items()
        }


def conjugate_verb(pp, conj):
    """pp = principal parts list; conj in {1,2,3,'3io',4}. Returns {tense: {person: form}}."""
    assert len(pp) >= 3, f"{pp}: need at least 3 principal parts"
    pres1, inf, perf1 = pp[0], pp[1], pp[2]
    out = {}

    if pres1 in IRREGULAR_VERBS:
        for tense, forms in IRREGULAR_VERBS[pres1].items():
            out[tense] = dict(zip(PERSONS, forms))
    else:
        assert len(inf) > 3, f"{inf}: infinitive too short"
        base = inf[:-3]
        assert inf[-3:] in ("āre", "ēre", "ere", "īre"), f"{inf}: unrecognised infinitive ending"
        for tense, ends in PRESENT_STEM_ENDINGS[conj].items():
            out[tense] = {p: base + e for p, e in zip(PERSONS, ends)}
        assert out["present"]["s1"] == pres1, \
            f"{pres1}: generated present 1sg {out['present']['s1']!r} != authored {pres1!r}"

    # Perfect system — regular for every verb, including the irregulars above.
    assert perf1.endswith("ī"), f"{perf1}: perfect 1sg should end in ī"
    pstem = perf1[:-1]
    for tense, ends in PERFECT_STEM_ENDINGS.items():
        out[tense] = {p: pstem + e for p, e in zip(PERSONS, ends)}
    for tense, forms in PERFECT_OVERRIDES.get(pres1, {}).items():
        out[tense] = dict(zip(PERSONS, forms))
    assert out["perfect"]["s1"] == perf1, f"{perf1}: perfect 1sg mismatch"
    return out


# ------------------------------------------------------------ ADJECTIVES

# One-termination adjectives that decline as consonant stems rather than
# i-stems, so the regular '3-1' rule would produce a wrong neuter plural.
CONSONANT_STEM_ADJECTIVES = {"vetus", "pauper", "dīves"}


def decline_adjective(nom, adj_type, base=None):
    """Nominative forms across genders and numbers.

    adj_type: 'us' (bonus, -a, -um), 'er' (miser/pulcher — pass the base),
              '3-2' (fortis, forte), '3-1' (ingēns — pass the base),
              '3-3' (ācer, ācris, ācre — pass the base).
    """
    if adj_type == "us":
        assert nom.endswith("us"), f"{nom}: 'us' adjective must end in -us"
        b = nom[:-2]
        return {"f_sg_nom": b + "a", "n_sg_nom": b + "um",
                "m_pl_nom": b + "ī", "f_pl_nom": b + "ae", "n_pl_nom": b + "a"}
    if adj_type == "er":
        assert base, f"{nom}: 'er' adjective needs an explicit base (miser- vs pulchr-)"
        return {"f_sg_nom": base + "a", "n_sg_nom": base + "um",
                "m_pl_nom": base + "ī", "f_pl_nom": base + "ae", "n_pl_nom": base + "a"}
    if adj_type == "3-2":
        assert nom.endswith("is"), f"{nom}: '3-2' adjective must end in -is"
        b = nom[:-2]
        return {"f_sg_nom": nom, "n_sg_nom": b + "e",
                "m_pl_nom": b + "ēs", "f_pl_nom": b + "ēs", "n_pl_nom": b + "ia"}
    if adj_type == "3-1":
        assert base, f"{nom}: '3-1' adjective needs an explicit base"
        # Most one-termination adjectives are i-stems (ingēns -> ingentia).
        # vetus and pauper are consonant stems (vetera, paupera) and must use
        # type '3-1-cons' instead; catching it here stops a silent wrong form.
        assert nom not in CONSONANT_STEM_ADJECTIVES, (
            f"{nom} is a consonant-stem adjective: neuter pl is {base}a, not {base}ia. "
            "Use adj_type '3-1-cons'.")
        return {"f_sg_nom": nom, "n_sg_nom": nom,
                "m_pl_nom": base + "ēs", "f_pl_nom": base + "ēs", "n_pl_nom": base + "ia"}
    if adj_type == "pl":
        # A plural-only adjective entry (multī, -ae, -a = "many"). The headword
        # is the masculine nominative plural, so — exactly as m_sg_nom is left
        # out for a normal adjective — it is not stored; the drill asks the
        # other genders.
        assert base, f"{nom}: 'pl' adjective needs an explicit base"
        return {"f_pl_nom": base + "ae", "n_pl_nom": base + "a"}
    if adj_type == "3-1-cons":
        # One termination, consonant stem: neuter plural in -a (vetus -> vetera).
        assert base, f"{nom}: '3-1-cons' adjective needs an explicit base"
        return {"f_sg_nom": nom, "n_sg_nom": nom,
                "m_pl_nom": base + "ēs", "f_pl_nom": base + "ēs", "n_pl_nom": base + "a"}
    if adj_type == "3-3":
        assert base, f"{nom}: '3-3' adjective needs an explicit base"
        return {"f_sg_nom": base + "is", "n_sg_nom": base + "e",
                "m_pl_nom": base + "ēs", "f_pl_nom": base + "ēs", "n_pl_nom": base + "ia"}
    raise ValueError(f"unknown adjective type {adj_type!r}")


if __name__ == "__main__":
    # Self-check against paradigms every first-year course drills.
    assert decline_noun("puella", "puellae", "f", 1)["abl_sg"] == "puellā"
    assert decline_noun("bellum", "bellī", "n", 2)["nom_pl"] == "bella"
    assert decline_noun("bellum", "bellī", "n", 2)["acc_sg"] == "bellum"
    assert decline_noun("ager", "agrī", "m", 2)["acc_sg"] == "agrum"
    assert decline_noun("rēx", "rēgis", "m", 3)["gen_pl"] == "rēgum"
    assert decline_noun("urbs", "urbis", "f", 3, istem=True)["gen_pl"] == "urbium"
    assert decline_noun("corpus", "corporis", "n", 3)["nom_pl"] == "corpora"
    assert decline_noun("mare", "maris", "n", 3, istem=True)["abl_sg"] == "marī"
    assert decline_noun("manus", "manūs", "f", 4)["gen_pl"] == "manuum"
    assert decline_noun("rēs", "reī", "f", 5)["gen_pl"] == "rērum"
    assert decline_noun("diēs", "diēī", "m", 5)["gen_sg"] == "diēī"
    # plural-only: keyed off the genitive plural, and no singular forms at all
    castra = decline_noun("castra", "castrōrum", "n", 2, plural_only=True)
    assert castra["abl_pl"] == "castrīs" and not any(k.endswith("_sg") for k in castra)
    assert decline_noun("moenia", "moenium", "n", 3, istem=True, plural_only=True)["dat_pl"] == "moenibus"
    assert decline_noun("tenebrae", "tenebrārum", "f", 1, plural_only=True)["acc_pl"] == "tenebrās"

    assert conjugate_verb(["amō", "amāre", "amāvī", "amātum"], 1)["present"]["p3"] == "amant"
    assert conjugate_verb(["amō", "amāre", "amāvī", "amātum"], 1)["perfect"]["p3"] == "amāvērunt"
    assert conjugate_verb(["moneō", "monēre", "monuī", "monitum"], 2)["future"]["s1"] == "monēbō"
    assert conjugate_verb(["regō", "regere", "rēxī", "rēctum"], 3)["future"]["s1"] == "regam"
    assert conjugate_verb(["capiō", "capere", "cēpī", "captum"], "3io")["present"]["p3"] == "capiunt"
    assert conjugate_verb(["audiō", "audīre", "audīvī", "audītum"], 4)["imperfect"]["s1"] == "audiēbam"
    assert conjugate_verb(["sum", "esse", "fuī"], 1)["present"]["s3"] == "est"
    assert conjugate_verb(["sum", "esse", "fuī"], 1)["pluperfect"]["s1"] == "fueram"
    # compounds inherit the irregular pattern, prefix and all
    assert conjugate_verb(["abeō", "abīre", "abiī", "abitum"], 1)["present"]["p3"] == "abeunt"
    assert conjugate_verb(["abeō", "abīre", "abiī", "abitum"], 1)["perfect"]["s2"] == "abīstī"
    assert conjugate_verb(["adsum", "adesse", "adfuī"], 1)["present"]["s3"] == "adest"
    assert conjugate_verb(["absum", "abesse", "āfuī"], 1)["present"]["p1"] == "absumus"
    assert conjugate_verb(["referō", "referre", "rettulī", "relātum"], 1)["present"]["s3"] == "refert"
    # a 2nd-conjugation verb must NOT be mistaken for an eō-compound
    assert conjugate_verb(["videō", "vidēre", "vīdī", "vīsum"], 2)["present"]["p3"] == "vident"

    assert decline_adjective("bonus", "us")["n_pl_nom"] == "bona"
    assert decline_adjective("pulcher", "er", base="pulchr")["f_sg_nom"] == "pulchra"
    assert decline_adjective("fortis", "3-2")["n_pl_nom"] == "fortia"
    assert decline_adjective("ingēns", "3-1", base="ingent")["n_pl_nom"] == "ingentia"
    # consonant stems take -a, and the i-stem rule must still refuse them
    assert decline_adjective("vetus", "3-1-cons", base="veter")["n_pl_nom"] == "vetera"
    assert decline_adjective("pauper", "3-1-cons", base="pauper")["n_pl_nom"] == "paupera"
    _pl = decline_adjective("multī", "pl", base="mult")
    assert _pl == {"f_pl_nom": "multae", "n_pl_nom": "multa"}, _pl
    try:
        decline_adjective("vetus", "3-1", base="veter"); raise SystemExit("should have refused vetus")
    except AssertionError:
        pass
    print("latin_morph self-check: all paradigms OK")
