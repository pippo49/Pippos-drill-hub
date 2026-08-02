#!/usr/bin/env python3
"""French morphology generator: articles, plurals, adjective agreement, present tense.

Same contract as latin_morph.py / italian_morph.py — rules with explicit curated
exceptions, and every expansion cross-checked against whatever the source
authored, so a wrong plural or feminine fails the build instead of shipping.

Two things French spelling does not record, and which are therefore curated
rather than guessed:
  * aspirate h (le héros, but l'hôtel) — decides the article and elision;
  * whether a final -ail/-al noun takes -s or -aux (le bal -> les bals, but
    le journal -> les journaux).
"""

PERSONS = ["je", "tu", "il_elle", "nous", "vous", "ils_elles"]
VOWELS = "aeiouâàäéèêëîïôöùûüy"

# --------------------------------------------------------------- ARTICLES

# Words beginning with an ASPIRATE h: no elision, no liaison (le héros, la
# honte). Everything else with initial h is mute (l'hôtel, l'heure).
ASPIRATE_H = {
    "héros", "haricot", "honte", "hasard", "haine", "hall", "halte", "hamburger",
    "hanche", "handicap", "harpe", "hauteur", "hibou", "hiérarchie", "hockey",
    "hollandais", "homard", "hongrois", "housse", "huit", "hurlement", "haut",
}


def starts_with_vowel_sound(word):
    """True when the word elides (l', j', d') — vowel, or mute h."""
    w = word.lower()
    if not w:
        return False
    if w[0] in VOWELS:
        return True
    if w[0] == "h":
        return w not in ASPIRATE_H
    return False


def article_sg(word, gender):
    """Definite article: le / la / l'."""
    if starts_with_vowel_sound(word):
        return "l'"
    return "la" if gender == "f" else "le"


def article_pl(word, gender):
    """Definite plural article is always les — kept as a function for symmetry."""
    return "les"


# ---------------------------------------------------------------- PLURALS

# -al nouns/adjectives that take a plain -s rather than -aux.
AL_TAKES_S = {"bal", "carnaval", "festival", "chacal", "récital", "régal", "banal", "fatal", "final", "natal", "naval"}
# -ail nouns that take -aux rather than -s.
AIL_TAKES_AUX = {"travail", "vitrail", "corail", "émail", "bail"}
# -eu / -au words that take -s rather than -x.
EU_TAKES_S = {"pneu", "bleu", "landau", "sarrau"}

IRREGULAR_PLURAL = {
    "œil": "yeux", "oeil": "yeux", "ciel": "cieux",
    "monsieur": "messieurs", "madame": "mesdames", "mademoiselle": "mesdemoiselles",
    "bonhomme": "bonshommes", "jeune homme": "jeunes gens",
}


def pluralize(word, gender="m"):
    """Plural of a noun or adjective."""
    w = word.lower()
    if w in IRREGULAR_PLURAL:
        return IRREGULAR_PLURAL[w]
    if not w:
        raise ValueError("empty word")
    # -s, -x, -z are already plural-shaped and never change
    if w[-1] in "sxz":
        return word
    if w.endswith("al") and w not in AL_TAKES_S:
        return word[:-2] + "aux"
    if w.endswith("ail"):
        return word[:-3] + "aux" if w in AIL_TAKES_AUX else word + "s"
    if w.endswith(("eau", "au", "eu")) and w not in EU_TAKES_S:
        return word + "x"
    return word + "s"


def noun_forms(word, gender, plural=None):
    """{article, plural} — what the Noun forms drill asks."""
    generated = pluralize(word, gender)
    if plural is not None and plural != generated:
        raise ValueError(
            f"{word}: generated plural {generated!r} != authored {plural!r}; "
            "add it to the curated tables rather than silently overriding")
    return {"article": article_sg(word, gender), "plural": plural or generated}


# ------------------------------------------------------------- ADJECTIVES

IRREGULAR_FEMININE = {
    "beau": "belle", "nouveau": "nouvelle", "vieux": "vieille", "fou": "folle",
    "mou": "molle", "blanc": "blanche", "franc": "franche", "sec": "sèche",
    "frais": "fraîche", "long": "longue", "doux": "douce", "faux": "fausse",
    "roux": "rousse", "favori": "favorite", "public": "publique", "grec": "grecque",
    "gentil": "gentille", "nul": "nulle", "épais": "épaisse", "gros": "grosse",
    "bas": "basse", "las": "lasse", "malin": "maligne", "bénin": "bénigne",
}
# Adjectives that never agree (colours from nouns, and a few borrowings).
INVARIABLE_ADJ = {"marron", "orange", "super", "chic", "snob", "bio", "kaki"}
# Doubling before -e: -el, -eil, -en, -on, -et (bon -> bonne, cruel -> cruelle).
DOUBLES_FINAL = ("el", "eil", "en", "on", "et")
# -et adjectives that take -ète instead of doubling.
ET_TAKES_GRAVE = {"complet", "concret", "discret", "inquiet", "secret", "replet"}


def feminine(masc):
    """Feminine singular of an adjective."""
    m = masc.lower()
    if m in INVARIABLE_ADJ:
        return masc
    if m in IRREGULAR_FEMININE:
        return IRREGULAR_FEMININE[m]
    if m.endswith("e"):
        return masc                      # already common gender (jeune, rouge)
    if m in ET_TAKES_GRAVE:
        return masc[:-2] + "ète"
    if m.endswith("er"):
        return masc[:-2] + "ère"         # cher -> chère
    if m.endswith("eur"):
        return masc[:-3] + "euse"        # travailleur -> travailleuse
    if m.endswith("teur"):
        return masc[:-4] + "trice"
    if m.endswith("f"):
        return masc[:-1] + "ve"          # actif -> active
    if m.endswith("x"):
        return masc[:-1] + "se"          # heureux -> heureuse
    if m.endswith(DOUBLES_FINAL):
        return masc + masc[-1] + "e"     # bon -> bonne
    return masc + "e"


def decline_adjective(masc_sg, feminine_form=None, invariable=False):
    """{m_sg, f_sg, m_pl, f_pl}."""
    if invariable or masc_sg.lower() in INVARIABLE_ADJ:
        return {"m_sg": masc_sg, "f_sg": masc_sg, "m_pl": masc_sg, "f_pl": masc_sg}
    fem = feminine(masc_sg)
    if feminine_form is not None and feminine_form != fem:
        raise ValueError(
            f"{masc_sg}: generated feminine {fem!r} != authored {feminine_form!r}; "
            "add it to IRREGULAR_FEMININE rather than silently overriding")
    return {"m_sg": masc_sg, "f_sg": fem,
            "m_pl": pluralize(masc_sg, "m"), "f_pl": pluralize(fem, "f")}


# ------------------------------------------------------------ CONJUGATION

REGULAR_ENDINGS = {
    "er":   ["e", "es", "e", "ons", "ez", "ent"],
    "ir":   ["is", "is", "it", "issons", "issez", "issent"],   # finir type
    "re":   ["s", "s", "", "ons", "ez", "ent"],
}
# partir/dormir/sortir type: the singular drops the stem's final consonant
# (part- -> je pars), the plural keeps it (nous partons). Two stems, so this
# cannot be expressed as one ending list.
IR2_SG_ENDINGS = ["s", "s", "t"]
IR2_PL_ENDINGS = ["ons", "ez", "ent"]

IRREGULAR_VERBS = {
    "être":     ["suis", "es", "est", "sommes", "êtes", "sont"],
    "avoir":    ["ai", "as", "a", "avons", "avez", "ont"],
    "aller":    ["vais", "vas", "va", "allons", "allez", "vont"],
    "faire":    ["fais", "fais", "fait", "faisons", "faites", "font"],
    "dire":     ["dis", "dis", "dit", "disons", "dites", "disent"],
    "pouvoir":  ["peux", "peux", "peut", "pouvons", "pouvez", "peuvent"],
    "vouloir":  ["veux", "veux", "veut", "voulons", "voulez", "veulent"],
    "devoir":   ["dois", "dois", "doit", "devons", "devez", "doivent"],
    "savoir":   ["sais", "sais", "sait", "savons", "savez", "savent"],
    "voir":     ["vois", "vois", "voit", "voyons", "voyez", "voient"],
    "venir":    ["viens", "viens", "vient", "venons", "venez", "viennent"],
    "tenir":    ["tiens", "tiens", "tient", "tenons", "tenez", "tiennent"],
    "prendre":  ["prends", "prends", "prend", "prenons", "prenez", "prennent"],
    "mettre":   ["mets", "mets", "met", "mettons", "mettez", "mettent"],
    "boire":    ["bois", "bois", "boit", "buvons", "buvez", "boivent"],
    "croire":   ["crois", "crois", "croit", "croyons", "croyez", "croient"],
    "connaître":["connais", "connais", "connaît", "connaissons", "connaissez", "connaissent"],
    "écrire":   ["écris", "écris", "écrit", "écrivons", "écrivez", "écrivent"],
    "lire":     ["lis", "lis", "lit", "lisons", "lisez", "lisent"],
    "vivre":    ["vis", "vis", "vit", "vivons", "vivez", "vivent"],
    "suivre":   ["suis", "suis", "suit", "suivons", "suivez", "suivent"],
    "recevoir": ["reçois", "reçois", "reçoit", "recevons", "recevez", "reçoivent"],
    "ouvrir":   ["ouvre", "ouvres", "ouvre", "ouvrons", "ouvrez", "ouvrent"],
    "offrir":   ["offre", "offres", "offre", "offrons", "offrez", "offrent"],
    "courir":   ["cours", "cours", "court", "courons", "courez", "courent"],
    "mourir":   ["meurs", "meurs", "meurt", "mourons", "mourez", "meurent"],
    "rire":     ["ris", "ris", "rit", "rions", "riez", "rient"],
    "plaire":   ["plais", "plais", "plaît", "plaisons", "plaisez", "plaisent"],
    "s'asseoir":["assieds", "assieds", "assied", "asseyons", "asseyez", "asseyent"],
    "falloir":  ["—", "—", "faut", "—", "—", "—"],
    "pleuvoir": ["—", "—", "pleut", "—", "—", "—"],
}
# Impersonal verbs: only the 3rd singular exists, so the drill must skip them.
IMPERSONAL = {"falloir", "pleuvoir"}


def _stem_change(stem, ending, infinitive):
    """Spelling shifts that keep pronunciation consistent."""
    inf = infinitive.lower()
    # -ger keeps the soft g before -ons (manger -> mangeons)
    if inf.endswith("ger") and ending == "ons":
        return stem + "e" + ending
    # -cer takes a cedilla before -ons (commencer -> commençons)
    if inf.endswith("cer") and ending == "ons":
        return stem[:-1] + "ç" + ending
    # -yer: y -> i everywhere except nous/vous (payer -> paie, payons)
    if inf.endswith(("ayer", "oyer", "uyer")) and ending not in ("ons", "ez"):
        return stem[:-1] + "i" + ending
    return stem + ending


def conjugate(infinitive, group=None, stem_changes=None):
    """Present indicative: {person: form}.

    group: "er" | "ir" (finir type) | "ir2" (partir type) | "re"; inferred when
    omitted. stem_changes: optional {person: form} overriding specific slots,
    for e-e / é-è verbs (acheter -> j'achète) whose change is lexical.
    """
    if infinitive in IRREGULAR_VERBS:
        return dict(zip(PERSONS, IRREGULAR_VERBS[infinitive]))
    if group is None:
        if infinitive.endswith("er"):
            group = "er"
        elif infinitive.endswith("re"):
            group = "re"
        elif infinitive.endswith("ir"):
            group = "ir"
        else:
            raise ValueError(f"{infinitive}: cannot infer group; pass one explicitly")
    stem = infinitive[:-2]
    if group == "ir2":
        # Two stems: singular loses the stem-final consonant, plural keeps it.
        assert len(stem) > 1, f"{infinitive}: stem too short for the partir type"
        forms = [stem[:-1] + e for e in IR2_SG_ENDINGS] + [stem + e for e in IR2_PL_ENDINGS]
        out = dict(zip(PERSONS, forms))
    else:
        assert group in REGULAR_ENDINGS, f"{infinitive}: unknown group {group!r}"
        out = {p: _stem_change(stem, e, infinitive)
               for p, e in zip(PERSONS, REGULAR_ENDINGS[group])}
    for person, form in (stem_changes or {}).items():
        assert person in PERSONS, f"{infinitive}: unknown person {person!r}"
        out[person] = form
    return out


if __name__ == "__main__":
    assert article_sg("livre", "m") == "le"
    assert article_sg("maison", "f") == "la"
    assert article_sg("ami", "m") == "l'"
    assert article_sg("heure", "f") == "l'"          # mute h
    assert article_sg("héros", "m") == "le"          # aspirate h
    assert article_pl("livre", "m") == "les"

    assert pluralize("livre") == "livres"
    assert pluralize("fils") == "fils"               # already ends in -s
    assert pluralize("prix") == "prix"
    assert pluralize("bateau") == "bateaux"
    assert pluralize("cheveu") == "cheveux"
    assert pluralize("pneu") == "pneus"              # curated exception
    assert pluralize("journal") == "journaux"
    assert pluralize("bal") == "bals"                # curated exception
    assert pluralize("travail") == "travaux"
    assert pluralize("détail") == "détails"
    assert pluralize("œil") == "yeux"

    assert feminine("grand") == "grande"
    assert feminine("cher") == "chère"
    assert feminine("heureux") == "heureuse"
    assert feminine("actif") == "active"
    assert feminine("bon") == "bonne"
    assert feminine("jeune") == "jeune"
    assert feminine("beau") == "belle"
    assert feminine("vieux") == "vieille"
    assert feminine("blanc") == "blanche"
    assert feminine("long") == "longue"
    assert feminine("complet") == "complète"
    assert feminine("marron") == "marron"
    assert decline_adjective("beau") == {"m_sg": "beau", "f_sg": "belle",
                                         "m_pl": "beaux", "f_pl": "belles"}
    assert decline_adjective("national")["m_pl"] == "nationaux"

    assert conjugate("parler")["ils_elles"] == "parlent"
    assert conjugate("finir")["nous"] == "finissons"
    for inf, want in [("partir", ["pars","pars","part","partons","partez","partent"]),
                      ("dormir", ["dors","dors","dort","dormons","dormez","dorment"]),
                      ("sortir", ["sors","sors","sort","sortons","sortez","sortent"]),
                      ("servir", ["sers","sers","sert","servons","servez","servent"])]:
        got = list(conjugate(inf, group="ir2").values())
        assert got == want, f"{inf}: {got} != {want}"
    assert conjugate("vendre")["il_elle"] == "vend"
    assert conjugate("manger")["nous"] == "mangeons"
    assert conjugate("commencer")["nous"] == "commençons"
    assert conjugate("payer")["je"] == "paie"
    assert conjugate("payer")["nous"] == "payons"
    assert conjugate("être")["vous"] == "êtes"
    assert conjugate("avoir")["ils_elles"] == "ont"
    assert conjugate("aller")["je"] == "vais"
    assert conjugate("acheter", stem_changes={"je": "achète", "tu": "achètes",
                                              "il_elle": "achète",
                                              "ils_elles": "achètent"})["je"] == "achète"
    print("french_morph self-check: articles, plurals, agreement, conjugation OK")
