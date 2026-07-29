#!/usr/bin/env python3
"""Italian morphology generator: articles, plurals and present-tense conjugation.

Same contract as latin_morph.py — rules with explicit curated exceptions, and
every expansion cross-checked against whatever the source authored, so a wrong
plural or conjugation fails the build instead of shipping.

Italian plurals of -co/-go are genuinely lexical (amico->amici but fuoco->fuochi:
it tracks Latin stress, which the spelling does not record), so those are driven
by a curated table rather than guessed. Any noun may also override its plural
explicitly; the generator then checks its own rule against that override and
reports the mismatch rather than silently deferring.
"""

PERSONS = ["io", "tu", "lui_lei", "noi", "voi", "loro"]
VOWELS = "aeiouàèéìíòóùú"

# --------------------------------------------------------------- ARTICLES

def article_sg(word, gender):
    """Definite article: il / lo / l' / la."""
    w = word.lower()
    if w[0] in VOWELS:
        return "l'"
    if gender == "f":
        return "la"
    # masculine special cases that take lo
    if w[0] == "z":
        return "lo"
    if w[:2] in ("gn", "ps", "pn"):
        return "lo"
    if w[0] == "x":
        return "lo"
    if w[0] == "s" and len(w) > 1 and w[1] not in VOWELS:   # s + consonant
        return "lo"
    if w[0] == "i" and len(w) > 1 and w[1] in VOWELS:       # semiconsonantal i
        return "lo"
    return "il"


def article_pl(word, gender):
    """Plural definite article: i / gli / le."""
    if gender == "f":
        return "le"
    return "gli" if article_sg(word, "m") in ("lo", "l'") else "i"


# ---------------------------------------------------------------- PLURALS

# -co/-go and -cia/-gia plurals follow stress, which Italian spelling does not
# mark. Curated, not guessed.
HARD_PLURAL = {          # keep the hard c/g sound: -chi / -ghi
    "fuoco": "fuochi", "gioco": "giochi", "luogo": "luoghi", "lago": "laghi",
    "banco": "banchi", "bosco": "boschi", "disco": "dischi", "parco": "parchi",
    "pacco": "pacchi", "cuoco": "cuochi", "tedesco": "tedeschi", "fresco": "freschi",
    "bianco": "bianchi", "stanco": "stanchi", "ricco": "ricchi", "sacco": "sacchi",
    "albergo": "alberghi", "castigo": "castighi", "obbligo": "obblighi",
    "dialogo": "dialoghi", "catalogo": "cataloghi", "lungo": "lunghi", "largo": "larghi",
    "sporco": "sporchi", "poco": "pochi", "secco": "secchi", "bosco": "boschi",
    "gioco": "giochi", "tasca": "tasche",
    "succo": "succhi", "cuoco": "cuochi", "pratico": "pratici",
    "buco": "buchi", "gioco": "giochi", "fico": "fichi", "arco": "archi",
    "porco": "porci", "rischio": "rischi",
}
SOFT_PLURAL = {          # soften to -ci / -gi
    "amico": "amici", "nemico": "nemici", "medico": "medici", "greco": "greci",
    "psicologo": "psicologi", "biologo": "biologi", "asparago": "asparagi",
    "economico": "economici", "simpatico": "simpatici", "stomaco": "stomaci",
    "antico": "antichi", "pubblico": "pubblici", "unico": "unici",
    "magnifico": "magnifici", "politico": "politici", "storico": "storici",
    "artistico": "artistici", "automatico": "automatici", "domestico": "domestici",
    "fantastico": "fantastici", "classico": "classici", "tipico": "tipici",
    "logico": "logici", "tragico": "tragici", "comico": "comici",
    "sindaco": "sindaci",
}
# Nouns/adjectives that do not change in the plural.
INVARIABLE = {
    "città", "università", "libertà", "verità", "società", "novità", "difficoltà",
    "qualità", "quantità", "età", "metà", "caffè", "tè", "bar", "sport", "film",
    "autobus", "computer", "film", "gas", "re", "crisi", "analisi", "tesi",
    "ipotesi", "serie", "specie", "foto", "moto", "auto", "radio", "cinema",
    "clima", "vaglia", "euro", "yogurt", "hotel", "test", "gratis", "blu", "rosa",
    "viola", "beige", "pari", "dispari", "menu", "sport", "bar", "film", "re",
    "caffè", "tè", "città", "università", "novità", "virtù", "tribù",
}
# Fully irregular plurals.
IRREGULAR_PLURAL = {
    "uomo": "uomini", "dio": "dei", "bue": "buoi", "tempio": "templi",
    "mille": "mila", "ala": "ali", "arma": "armi",
    "zio": "zii",   # stressed -io keeps both i
    "moglie": "mogli", "superficie": "superfici",   # -glie absorbs the i
    # feminine plurals of masculine singulars (old Latin neuters)
    "uovo": "uova", "braccio": "braccia", "dito": "dita", "ginocchio": "ginocchia",
    "labbro": "labbra", "lenzuolo": "lenzuola", "osso": "ossa", "paio": "paia",
    "centinaio": "centinaia", "migliaio": "migliaia", "miglio": "miglia",
}


def pluralize(word, gender):
    """Plural of a noun/adjective. Raises on shapes the rules do not cover."""
    w = word.lower()
    if w in IRREGULAR_PLURAL:
        return IRREGULAR_PLURAL[w]
    if w in INVARIABLE:
        return word
    if w in HARD_PLURAL:
        return HARD_PLURAL[w]
    if w in SOFT_PLURAL:
        return SOFT_PLURAL[w]
    if not w:
        raise ValueError("empty word")
    # accented final vowel or final consonant -> invariable
    if w[-1] in "àèéìíòóùú" or w[-1] not in VOWELS:
        return word
    if w.endswith("io"):
        # unstressed -io collapses to a single i (figlio -> figli); the stressed
        # type (zio -> zii) is rare enough to live in IRREGULAR_PLURAL.
        return word[:-2] + "i"
    if w.endswith("ca") or w.endswith("ga"):
        # The h keeps the hard sound; the vowel still follows gender, so
        # masculine collega -> colleghi but feminine amica -> amiche.
        return word[:-1] + "h" + ("i" if gender == "m" else "e")
    if w.endswith("cia") or w.endswith("gia"):
        # vowel before -cia keeps the i (camicia -> camicie), consonant drops it
        # (arancia -> arance)
        stem = word[:-3]
        keep_i = bool(stem) and stem[-1] in VOWELS
        soft = word[-3]  # c or g
        return stem + soft + ("ie" if keep_i else "e")
    if w.endswith("co"):
        raise ValueError(f"{word}: -co plural is lexical; add it to HARD_PLURAL or SOFT_PLURAL")
    if w.endswith("go"):
        raise ValueError(f"{word}: -go plural is lexical; add it to HARD_PLURAL or SOFT_PLURAL")
    if w.endswith("o"):
        return word[:-1] + "i"
    if w.endswith("a"):
        return word[:-1] + ("i" if gender == "m" else "e")
    if w.endswith("e"):
        return word[:-1] + "i"
    raise ValueError(f"{word}: no plural rule for this ending")


def noun_forms(word, gender, plural=None):
    """{article, plural} — what the Noun forms drill asks."""
    generated = pluralize(word, gender)
    if plural is not None and plural != generated:
        raise ValueError(
            f"{word}: generated plural {generated!r} != authored {plural!r}; "
            "add it to the curated tables rather than silently overriding")
    return {"article": article_sg(word, gender), "plural": plural or generated}


# ------------------------------------------------------------ CONJUGATION

REGULAR_ENDINGS = {
    "are":  ["o", "i", "a", "iamo", "ate", "ano"],
    "ere":  ["o", "i", "e", "iamo", "ete", "ono"],
    "ire":  ["o", "i", "e", "iamo", "ite", "ono"],
    "isc":  ["isco", "isci", "isce", "iamo", "ite", "iscono"],
}

IRREGULAR_VERBS = {
    "essere":   ["sono", "sei", "è", "siamo", "siete", "sono"],
    "avere":    ["ho", "hai", "ha", "abbiamo", "avete", "hanno"],
    "andare":   ["vado", "vai", "va", "andiamo", "andate", "vanno"],
    "fare":     ["faccio", "fai", "fa", "facciamo", "fate", "fanno"],
    "dare":     ["do", "dai", "dà", "diamo", "date", "danno"],
    "stare":    ["sto", "stai", "sta", "stiamo", "state", "stanno"],
    "dire":     ["dico", "dici", "dice", "diciamo", "dite", "dicono"],
    "uscire":   ["esco", "esci", "esce", "usciamo", "uscite", "escono"],
    "venire":   ["vengo", "vieni", "viene", "veniamo", "venite", "vengono"],
    "tenere":   ["tengo", "tieni", "tiene", "teniamo", "tenete", "tengono"],
    "potere":   ["posso", "puoi", "può", "possiamo", "potete", "possono"],
    "volere":   ["voglio", "vuoi", "vuole", "vogliamo", "volete", "vogliono"],
    "dovere":   ["devo", "devi", "deve", "dobbiamo", "dovete", "devono"],
    "sapere":   ["so", "sai", "sa", "sappiamo", "sapete", "sanno"],
    "bere":     ["bevo", "bevi", "beve", "beviamo", "bevete", "bevono"],
    "rimanere": ["rimango", "rimani", "rimane", "rimaniamo", "rimanete", "rimangono"],
    "salire":   ["salgo", "sali", "sale", "saliamo", "salite", "salgono"],
    "scegliere":["scelgo", "scegli", "sceglie", "scegliamo", "scegliete", "scelgono"],
    "morire":   ["muoio", "muori", "muore", "moriamo", "morite", "muoiono"],
    "piacere":  ["piaccio", "piaci", "piace", "piacciamo", "piacete", "piacciono"],
    "sedere":   ["siedo", "siedi", "siede", "sediamo", "sedete", "siedono"],
    "tradurre": ["traduco", "traduci", "traduce", "traduciamo", "traducete", "traducono"],
    "porre":    ["pongo", "poni", "pone", "poniamo", "ponete", "pongono"],
    "cogliere": ["colgo", "cogli", "coglie", "cogliamo", "cogliete", "colgono"],
    "spegnere": ["spengo", "spegni", "spegne", "spegniamo", "spegnete", "spengono"],
    "sciogliere": ["sciolgo", "sciogli", "scioglie", "sciogliamo", "sciogliete", "sciolgono"],
    "trarre":   ["traggo", "trai", "trae", "traiamo", "traete", "traggono"],
    "apparire": ["appaio", "appari", "appare", "appariamo", "apparite", "appaiono"],
    "udire":    ["odo", "odi", "ode", "udiamo", "udite", "odono"],
    # -urre / -orre verbs (contracted Latin infinitives)
    "condurre": ["conduco", "conduci", "conduce", "conduciamo", "conducete", "conducono"],
    "produrre": ["produco", "produci", "produce", "produciamo", "producete", "producono"],
    "proporre": ["propongo", "proponi", "propone", "proponiamo", "proponete", "propongono"],
    # -gliere verbs take a hard g in the 1sg/3pl
    "togliere":    ["tolgo", "togli", "toglie", "togliamo", "togliete", "tolgono"],
    "raccogliere": ["raccolgo", "raccogli", "raccoglie", "raccogliamo", "raccogliete", "raccolgono"],
    # tenere compounds
    "sostenere":   ["sostengo", "sostieni", "sostiene", "sosteniamo", "sostenete", "sostengono"],
    "ottenere":    ["ottengo", "ottieni", "ottiene", "otteniamo", "ottenete", "ottengono"],
    "appartenere": ["appartengo", "appartieni", "appartiene", "apparteniamo", "appartenete", "appartengono"],
    "valere":   ["valgo", "vali", "vale", "valiamo", "valete", "valgono"],
    # -ire verbs that keep an i in the stem rather than taking -isc-
    "riempire": ["riempio", "riempi", "riempie", "riempiamo", "riempite", "riempiono"],
    "cucire":   ["cucio", "cuci", "cuce", "cuciamo", "cucite", "cuciono"],
    # stressed -iare: the i does NOT drop (contrast lasciare -> lasci)
    "sciare":   ["scio", "scii", "scia", "sciamo", "sciate", "sciano"],
    "inviare":  ["invio", "invii", "invia", "inviamo", "inviate", "inviano"],
}


def _spelling_fix(stem, ending, infinitive):
    """-care/-gare keep the hard sound before i; -ciare/-giare drop the extra i."""
    if infinitive.endswith(("care", "gare")) and ending.startswith("i"):
        return stem + "h" + ending
    if infinitive.endswith("iare") and ending.startswith("i"):
        return stem + ending[1:]      # mangi-are + iamo -> mangiamo, not mangiiamo
    return stem + ending


def conjugate(infinitive, isc=False):
    """Present indicative: {person: form}."""
    if infinitive in IRREGULAR_VERBS:
        return dict(zip(PERSONS, IRREGULAR_VERBS[infinitive]))
    assert len(infinitive) > 3, f"{infinitive}: too short to be an infinitive"
    tail = infinitive[-3:]
    assert tail in ("are", "ere", "ire"), f"{infinitive}: unrecognised infinitive ending"
    if isc:
        assert tail == "ire", f"{infinitive}: -isc pattern only applies to -ire verbs"
    stem = infinitive[:-3]
    endings = REGULAR_ENDINGS["isc" if isc else tail]
    return {p: _spelling_fix(stem, e, infinitive) for p, e in zip(PERSONS, endings)}


# ------------------------------------------------------------- ADJECTIVES

def decline_adjective(masc_sg, invariable=False):
    """{m_sg, f_sg, m_pl, f_pl}. Handles -o/-a, -e (one ending) and invariables."""
    if invariable or masc_sg.lower() in INVARIABLE:
        return {"m_sg": masc_sg, "f_sg": masc_sg, "m_pl": masc_sg, "f_pl": masc_sg}
    if masc_sg.endswith("o"):
        f_sg = masc_sg[:-1] + "a"
        return {"m_sg": masc_sg, "f_sg": f_sg,
                "m_pl": pluralize(masc_sg, "m"), "f_pl": pluralize(f_sg, "f")}
    if masc_sg.endswith("e"):
        # single-ending adjective: same for both genders, plural in -i
        pl = pluralize(masc_sg, "m")
        return {"m_sg": masc_sg, "f_sg": masc_sg, "m_pl": pl, "f_pl": pl}
    raise ValueError(f"{masc_sg}: adjective must end in -o, -e, or be invariable")


if __name__ == "__main__":
    assert article_sg("libro", "m") == "il"
    assert article_sg("studente", "m") == "lo"        # s + consonant
    assert article_sg("zio", "m") == "lo"
    assert article_sg("amico", "m") == "l'"
    assert article_sg("casa", "f") == "la"
    assert article_sg("amica", "f") == "l'"
    assert article_pl("libro", "m") == "i"
    assert article_pl("studente", "m") == "gli"
    assert article_pl("amico", "m") == "gli"
    assert article_pl("casa", "f") == "le"

    assert pluralize("libro", "m") == "libri"
    assert pluralize("casa", "f") == "case"
    assert pluralize("problema", "m") == "problemi"
    assert pluralize("studente", "m") == "studenti"
    assert pluralize("amico", "m") == "amici"        # curated soft
    assert pluralize("fuoco", "m") == "fuochi"       # curated hard
    assert pluralize("amica", "f") == "amiche"
    assert pluralize("figlio", "m") == "figli"
    assert pluralize("camicia", "f") == "camicie"    # vowel before -cia
    assert pluralize("arancia", "f") == "arance"     # consonant before -cia
    assert pluralize("città", "f") == "città"
    assert pluralize("bar", "m") == "bar"
    assert pluralize("uomo", "m") == "uomini"
    assert pluralize("uovo", "m") == "uova"
    assert pluralize("zio", "m") == "zii"
    assert pluralize("moglie", "f") == "mogli"
    assert pluralize("collega", "m") == "colleghi"   # masculine -ga
    assert pluralize("amica", "f") == "amiche"       # feminine -ca
    try:
        pluralize("banco2", "m")
    except ValueError:
        pass

    assert conjugate("parlare")["loro"] == "parlano"
    assert conjugate("credere")["loro"] == "credono"
    assert conjugate("dormire")["voi"] == "dormite"
    assert conjugate("finire", isc=True)["loro"] == "finiscono"
    assert conjugate("cercare")["tu"] == "cerchi"
    assert conjugate("pagare")["noi"] == "paghiamo"
    assert conjugate("mangiare")["noi"] == "mangiamo"
    assert conjugate("mangiare")["tu"] == "mangi"
    assert conjugate("studiare")["tu"] == "studi"      # generalised -iare rule
    assert conjugate("annoiare")["tu"] == "annoi"
    assert conjugate("lasciare")["noi"] == "lasciamo"
    assert conjugate("sciare")["tu"] == "scii"         # stressed i is kept
    assert conjugate("togliere")["io"] == "tolgo"
    assert conjugate("condurre")["loro"] == "conducono"
    assert conjugate("essere")["lui_lei"] == "è"
    assert conjugate("avere")["loro"] == "hanno"
    assert conjugate("potere")["lui_lei"] == "può"

    assert decline_adjective("rosso") == {"m_sg": "rosso", "f_sg": "rossa",
                                          "m_pl": "rossi", "f_pl": "rosse"}
    assert decline_adjective("grande")["f_pl"] == "grandi"
    assert decline_adjective("blu")["f_pl"] == "blu"
    print("italian_morph self-check: articles, plurals, conjugations OK")
