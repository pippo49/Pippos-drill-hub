#!/usr/bin/env python3
"""Portuguese morphology: articles, plurals, present tense, personal infinitive.

Same contract as italian_morph.py and latin_morph.py — rules with explicit
curated exceptions, every expansion cross-checked against whatever the source
authored, so a wrong plural or conjugation fails the build instead of shipping.

Three things are specific to Portuguese and worth knowing before editing:

* **-ão plurals are lexical.** coração->corações, pão->pães, irmão->irmãos: the
  three patterns descend from different Latin endings (-anem, -anum, -onem) and
  the modern spelling records none of that. -ões is much the commonest, so it is
  the default, and the other two are curated tables. Guessing here would be the
  Portuguese equivalent of Italian's amico/fuoco problem.

* **vós is not in the paradigm.** It is archaic in both varieties; Portugal uses
  *vocês* for plural you and Brazil does too. Including a person nobody says
  would be five wasted slots in every conjugation drill. The persons are
  eu / tu / ele_ela_voce / nos / eles_elas_voces.

* **The personal infinitive is fully regular, for every verb.** ser->sermos,
  fazer->fazermos: it is built on the infinitive, always. That is exactly what
  makes it confusable with the future subjunctive, which uses the preterite stem
  and is wildly irregular (ser->formos, fazer->fizermos). The two coincide for
  regular verbs, which is why learners think they are the same thing. Both are
  generated here so the deck can contrast them.
"""

PERSONS = ["eu", "tu", "ele_ela_voce", "nos", "eles_elas_voces"]

# Brazil's paradigm is FOUR slots, not five. você is the ordinary second person
# and takes third-person verb forms, so tu and ele collapse into one. Regions
# that do say tu (the south, the northeast) very often use the ele form with it
# anyway, so drilling "tu falas" would teach a shape most Brazilians do not use.
PERSONS_BR = ["eu", "voce_ele_ela", "nos", "voces_eles_elas"]

VOWELS = "aeiouáéíóúâêôãõà"

# --------------------------------------------------------------- ARTICLES

DEF_ARTICLE = {"m": "o", "f": "a"}
DEF_ARTICLE_PL = {"m": "os", "f": "as"}
INDEF_ARTICLE = {"m": "um", "f": "uma"}


def article_sg(gender):
    assert gender in DEF_ARTICLE, f"unknown gender {gender!r}"
    return DEF_ARTICLE[gender]


def article_pl(gender):
    return DEF_ARTICLE_PL[gender]


# ---------------------------------------------------------------- PLURALS

# -ão is the one ending the spelling does not determine. Default is -ões.
AO_AES = {          # -ão -> -ães
    "pão", "cão", "alemão", "capitão", "escrivão", "charlatão", "catalão",
}
AO_AOS = {          # -ão -> -ãos (the stem vowel was already there)
    "mão", "irmão", "cidadão", "cristão", "órfão", "órgão", "sótão", "grão",
    "bênção", "chão", "pagão", "vão", "artesão", "acórdão",
}

# Nouns that only exist in the plural: the headword IS the plural, so it has no
# separate form. Distinct from INVARIABLE_S below, which are singulars whose
# plural happens to look the same.
PLURAL_ONLY = {
    "férias", "costas", "calças", "óculos", "parabéns", "arredores", "víveres",
}

# Paroxytone/proparoxytone words ending in -s do not change.
INVARIABLE_S = {
    "lápis", "ônibus", "vírus", "atlas", "bônus", "campus", "oásis", "pires",
    "cais", "lápis", "tênis", "ténis", "simples", "alferes", "obus",
    "sandes", "lápis", "ourives", "pêsames", "fezes",
}

IRREGULAR_PLURAL = {
    "qualquer": "quaisquer",
    "mal": "males",
    "cônsul": "cônsules",
    "fóssil": "fósseis",
    "réptil": "répteis",
    "projétil": "projéteis",
    "carácter": "caracteres",
    "caráter": "caracteres",
    # loanwords ending in a consonant Portuguese does not use finally: they
    # take a bare -s rather than any of the native patterns
    "internet": "internet",     # uncountable in practice
    "email": "emails",
    "site": "sites",
}


def _stressed_last(word):
    """Does the written accent (or an -r/-z/-l ending) put stress on the end?"""
    return word[-1] in "rzl" or any(c in word[-2:] for c in "áéíóúâêô")


def pluralize(word, gender=None):
    w = word.lower()
    if w in IRREGULAR_PLURAL:
        return IRREGULAR_PLURAL[w]
    if w in PLURAL_ONLY or w in INVARIABLE_S:
        return word
    if w.endswith("x"):
        return word                                   # o tórax -> os tórax

    if w.endswith("ão"):
        if w in AO_AES:
            return word[:-2] + "ães"
        if w in AO_AOS:
            return word[:-2] + "ãos"
        return word[:-2] + "ões"                      # the productive default

    if w.endswith("m"):
        return word[:-1] + "ns"                       # homem -> homens

    if w.endswith(("el", "il")):
        # A word already carrying a written accent is stressed EARLIER, so its
        # plural needs no new accent: possível->possíveis, fácil->fáceis,
        # amável->amáveis. Only an oxytone -el/-il takes one: papel->papéis,
        # funil->funis. Missing this produced "possívéis" — two stress marks in
        # one word, which Portuguese never writes.
        accented = any(c in word for c in "áéíóúâêôãõ")
        if accented:
            return word[:-2] + "eis"
        if w.endswith("el"):
            return word[:-2] + "éis"
        return word[:-1] + "s"                        # funil -> funis
    if w.endswith("al"):
        return word[:-2] + "ais"
    if w.endswith("ol"):
        return word[:-2] + "óis"
    if w.endswith("ul"):
        return word[:-2] + "uis"

    if w.endswith("s"):
        # An oxytone -s takes -es, and the written accent then DISAPPEARS,
        # because the plural is an ordinary paroxytone that does not need it:
        # mês->meses, português->portugueses, ananás->ananases. The spellchecker
        # oracle caught this rule missing — four forms out of 448.
        # -ís is the exception: país->países keeps the accent, which is marking
        # a hiatus (pa-ís) rather than merely the stress.
        for acc, plain in (("ês", "es"), ("ás", "as"), ("ós", "os"), ("ús", "us")):
            if w.endswith(acc):
                return word[:-2] + plain + "es"
        # the invariable ones are listed in INVARIABLE_S
        return word + "es"

    if w[-1] == "z":
        # A stressed i or u that follows another vowel is a HIATUS, and the
        # plural has to keep the accent that marks it: raiz->raízes,
        # juiz->juízes. Without a preceding vowel there is no hiatus and no
        # accent: luz->luzes, feliz->felizes.
        if len(w) >= 3 and w[-2] in "iu" and w[-3] in "aeiouáéíóú":
            acc = {"i": "í", "u": "ú"}[w[-2]]
            return word[:-2] + acc + "zes"
        return word + "es"
    if w[-1] == "r":
        return word + "es"
    if w[-1] in "n":
        return word + "es"

    if w[-1] in VOWELS or w.endswith("ã"):
        return word + "s"

    raise ValueError(f"{word!r}: no plural rule — add it to IRREGULAR_PLURAL")


def noun_forms(word, gender, plural=None):
    """{article, plural} — what the Noun forms drill asks."""
    generated = pluralize(word, gender)
    if plural is not None and plural != generated:
        raise ValueError(
            f"{word}: generated plural {generated!r} != authored {plural!r}; "
            "add it to the curated tables rather than silently overriding")
    return {"article": article_sg(gender), "plural": plural or generated}


# ------------------------------------------------------------ CONJUGATION

REGULAR_ENDINGS = {
    "ar": ["o", "as", "a", "amos", "am"],
    "er": ["o", "es", "e", "emos", "em"],
    "ir": ["o", "es", "e", "imos", "em"],
}

IRREGULAR_VERBS = {
    "ser":     ["sou", "és", "é", "somos", "são"],
    "estar":   ["estou", "estás", "está", "estamos", "estão"],
    "ter":     ["tenho", "tens", "tem", "temos", "têm"],
    "haver":   ["hei", "hás", "há", "havemos", "hão"],
    "ir":      ["vou", "vais", "vai", "vamos", "vão"],
    "fazer":   ["faço", "fazes", "faz", "fazemos", "fazem"],
    "dizer":   ["digo", "dizes", "diz", "dizemos", "dizem"],
    "poder":   ["posso", "podes", "pode", "podemos", "podem"],
    "querer":  ["quero", "queres", "quer", "queremos", "querem"],
    "saber":   ["sei", "sabes", "sabe", "sabemos", "sabem"],
    "ver":     ["vejo", "vês", "vê", "vemos", "veem"],
    "vir":     ["venho", "vens", "vem", "vimos", "vêm"],
    "pôr":     ["ponho", "pões", "põe", "pomos", "põem"],
    "dar":     ["dou", "dás", "dá", "damos", "dão"],
    "trazer":  ["trago", "trazes", "traz", "trazemos", "trazem"],
    "ler":     ["leio", "lês", "lê", "lemos", "leem"],
    "crer":    ["creio", "crês", "crê", "cremos", "creem"],
    "perder":  ["perco", "perdes", "perde", "perdemos", "perdem"],
    "ouvir":   ["ouço", "ouves", "ouve", "ouvimos", "ouvem"],
    "pedir":   ["peço", "pedes", "pede", "pedimos", "pedem"],
    "medir":   ["meço", "medes", "mede", "medimos", "medem"],
    "sair":    ["saio", "sais", "sai", "saímos", "saem"],
    "cair":    ["caio", "cais", "cai", "caímos", "caem"],
    "valer":   ["valho", "vales", "vale", "valemos", "valem"],
    "caber":   ["caibo", "cabes", "cabe", "cabemos", "cabem"],
    "odiar":   ["odeio", "odeias", "odeia", "odiamos", "odeiam"],
    "despir":  ["dispo", "despes", "despe", "despimos", "despem"],
    # -ir verbs raising e->i or o->u in the 1sg only
    "sentir":  ["sinto", "sentes", "sente", "sentimos", "sentem"],
    "servir":  ["sirvo", "serves", "serve", "servimos", "servem"],
    "seguir":  ["sigo", "segues", "segue", "seguimos", "seguem"],
    "vestir":  ["visto", "vestes", "veste", "vestimos", "vestem"],
    "repetir": ["repito", "repetes", "repete", "repetimos", "repetem"],
    "preferir": ["prefiro", "preferes", "prefere", "preferimos", "preferem"],
    "dormir":  ["durmo", "dormes", "dorme", "dormimos", "dormem"],
    "subir":   ["subo", "sobes", "sobe", "subimos", "sobem"],
    "fugir":   ["fujo", "foges", "foge", "fugimos", "fogem"],
    "construir": ["construo", "constróis", "constrói", "construímos", "constroem"],
    # -uir verbs keep the u as a full vowel and take a hiatus accent in nós
    "diminuir": ["diminuo", "diminuis", "diminui", "diminuímos", "diminuem"],
    # monosyllabic -ir verbs in -rir: the stem keeps its i
    "rir":     ["rio", "ris", "ri", "rimos", "riem"],
    "sorrir":  ["sorrio", "sorris", "sorri", "sorrimos", "sorriem"],
    # stressed i takes an accent where the stem is stressed (hiatus pro-í-bo)
    "proibir": ["proíbo", "proíbes", "proíbe", "proibimos", "proíbem"],
    # compounds keep their base's irregularity
    "conseguir": ["consigo", "consegues", "consegue", "conseguimos", "conseguem"],
    "manter":  ["mantenho", "manténs", "mantém", "mantemos", "mantêm"],
    "obter":   ["obtenho", "obténs", "obtém", "obtemos", "obtêm"],
    "conter":  ["contenho", "conténs", "contém", "contemos", "contêm"],
    "prever":  ["prevejo", "prevês", "prevê", "prevemos", "preveem"],
    "rever":   ["revejo", "revês", "revê", "revemos", "reveem"],
    "compor":  ["componho", "compões", "compõe", "compomos", "compõem"],
    "supor":   ["suponho", "supões", "supõe", "supomos", "supõem"],
    "propor":  ["proponho", "propões", "propõe", "propomos", "propõem"],
    "convir":  ["convenho", "convéns", "convém", "convimos", "convêm"],
    "intervir": ["intervenho", "intervéns", "intervém", "intervimos", "intervêm"],
    "refazer": ["refaço", "refazes", "refaz", "refazemos", "refazem"],
    "desfazer": ["desfaço", "desfazes", "desfaz", "desfazemos", "desfazem"],
    "satisfazer": ["satisfaço", "satisfazes", "satisfaz", "satisfazemos", "satisfazem"],
}


def _spelling_fix(stem, ending, infinitive):
    """Keep the sound of the stem's final consonant before a changed vowel.

    Portuguese spelling encodes sound, so the letter has to change when the
    ending's vowel does: -car/-gar/-çar only shift before e (subjunctive), while
    -cer/-ger/-guir shift before the -o of the first person singular.
    """
    if not ending.startswith("o"):
        return stem + ending
    if infinitive.endswith("cer"):
        return stem[:-1] + "ç" + ending          # conhecer -> conheço
    if infinitive.endswith("ger"):
        return stem[:-1] + "j" + ending          # proteger -> protejo
    if infinitive.endswith("gir"):
        return stem[:-1] + "j" + ending          # dirigir -> dirijo
    if infinitive.endswith(("guir", "guer")):
        return stem[:-1] + ending                # erguer -> ergo, distinguir -> distingo
    return stem + ending


def conjugate(infinitive):
    """Present indicative: {person: form}."""
    # -ear verbs insert an i wherever the stem is stressed: passear -> passeio,
    # passeias, passeia, but passeamos with the stress on the ending. A whole
    # productive class, and the spelling oracle is what found it missing.
    if infinitive.endswith("ear"):
        stem = infinitive[:-2]                  # passe-
        return dict(zip(PERSONS, [stem + "io", stem + "ias", stem + "ia",
                                  infinitive[:-2] + "amos", stem + "iam"]))
    # -zir verbs apocopate the third person singular: conduzir -> conduz, not
    # conduze, exactly as dizer gives diz and fazer gives faz.
    if infinitive.endswith("zir") and infinitive not in IRREGULAR_VERBS:
        stem = infinitive[:-3]                  # condu-
        return dict(zip(PERSONS, [stem + "zo", stem + "zes", stem + "z",
                                  stem + "zimos", stem + "zem"]))
    if infinitive in IRREGULAR_VERBS:
        forms = IRREGULAR_VERBS[infinitive]
        assert len(forms) == len(PERSONS), f"{infinitive}: wrong number of forms"
        return dict(zip(PERSONS, forms))
    assert len(infinitive) > 2, f"{infinitive}: too short to be an infinitive"
    tail = infinitive[-2:]
    assert tail in REGULAR_ENDINGS, f"{infinitive}: unrecognised infinitive ending"
    stem = infinitive[:-2]
    return {p: _spelling_fix(stem, e, infinitive)
            for p, e in zip(PERSONS, REGULAR_ENDINGS[tail])}


# ------------------------------------------------- PERSONAL INFINITIVE

PERSONAL_ENDINGS = ["", "es", "", "mos", "em"]


def personal_infinitive(infinitive):
    """{person: form}. Regular for EVERY verb, including ser and fazer.

    That total regularity is the point: it is what separates the personal
    infinitive from the future subjunctive, which shares its endings but is
    built on the (very irregular) preterite stem.
    """
    assert infinitive.endswith(("ar", "er", "ir", "ôr", "or")), \
        f"{infinitive}: not an infinitive"
    return {p: infinitive + e for p, e in zip(PERSONS, PERSONAL_ENDINGS)}


# The future subjunctive, for the cards that contrast the two. Regular verbs
# build it on the infinitive as well, so only the irregular stems are listed;
# anything absent is identical to the personal infinitive, which IS the lesson.
FUTURE_SUBJUNCTIVE_STEMS = {
    "ser": "for", "ir": "for", "ter": "tiver", "estar": "estiver",
    "fazer": "fizer", "dizer": "disser", "poder": "puder", "querer": "quiser",
    "saber": "souber", "ver": "vir", "vir": "vier", "pôr": "puser",
    "dar": "der", "trazer": "trouxer", "haver": "houver", "caber": "couber",
}


def future_subjunctive(infinitive):
    stem = FUTURE_SUBJUNCTIVE_STEMS.get(infinitive)
    if stem is None:
        return personal_infinitive(infinitive)
    return {p: stem + e for p, e in zip(PERSONS, PERSONAL_ENDINGS)}


# ------------------------------------------------------------- ADJECTIVES

INVARIABLE_ADJ = {
    "azul", "verde", "grande", "forte", "fácil", "difícil", "feliz", "triste",
    "jovem", "simples", "doce", "pobre", "livre", "importante", "inteligente",
    "interessante", "quente", "alegre", "amável", "possível", "impossível",
    "útil", "terrível", "horrível", "agradável", "responsável", "normal",
    "especial", "principal", "final", "igual", "capaz", "feroz", "veloz",
    "ruim", "comum", "melhor", "pior", "maior", "menor",
}


def decline_adjective(masc_sg):
    """{m_sg_nom, f_sg, m_pl, f_pl} — the shape the Spanish/Italian engine wants."""
    w = masc_sg.lower()
    if w in INVARIABLE_ADJ:
        pl = pluralize(masc_sg)
        return {"m_sg_nom": masc_sg, "f_sg": masc_sg, "m_pl": pl, "f_pl": pl}
    # -ão must be tested before -o: "alemão" ends in the letter o as well, and
    # the -o rule would produce "alemãa".
    if w.endswith("ão"):
        fem = masc_sg[:-2] + "ã"                   # alemão -> alemã
    elif w.endswith("ês"):
        fem = masc_sg[:-2] + "esa"                 # português -> portuguesa
    elif w.endswith("or") and not w.endswith(("ior", "erior")):
        fem = masc_sg + "a"                        # trabalhador -> trabalhadora
    elif w.endswith("o"):
        fem = masc_sg[:-1] + "a"
    elif w.endswith("ol"):
        fem = masc_sg + "a"                        # espanhol -> espanhola
    elif w.endswith("eu"):
        fem = masc_sg[:-2] + "eia"                 # europeu -> europeia
    else:
        fem = masc_sg                              # -e, -a, -l, -z: one form
    return {"m_sg_nom": masc_sg, "f_sg": fem,
            "m_pl": pluralize(masc_sg), "f_pl": pluralize(fem)}


def conjugate_br(infinitive):
    """The same present tense, re-slotted for Brazil: tu drops out."""
    full = conjugate(infinitive)
    return {"eu": full["eu"],
            "voce_ele_ela": full["ele_ela_voce"],
            "nos": full["nos"],
            "voces_eles_elas": full["eles_elas_voces"]}


def personal_infinitive_br(infinitive):
    full = personal_infinitive(infinitive)
    return {"eu": full["eu"],
            "voce_ele_ela": full["ele_ela_voce"],
            "nos": full["nos"],
            "voces_eles_elas": full["eles_elas_voces"]}


def future_subjunctive_br(infinitive):
    full = future_subjunctive(infinitive)
    return {"eu": full["eu"],
            "voce_ele_ela": full["ele_ela_voce"],
            "nos": full["nos"],
            "voces_eles_elas": full["eles_elas_voces"]}



# --------------------------------------------------------------- SELF-CHECK

def _selfcheck():
    cases = [
        # the three -ão patterns, which is the whole reason for the tables
        ("coração", "corações"), ("pão", "pães"), ("irmão", "irmãos"),
        ("mão", "mãos"), ("alemão", "alemães"), ("estação", "estações"),
        # -l families
        ("animal", "animais"), ("papel", "papéis"), ("lençol", "lençóis"),
        ("azul", "azuis"), ("funil", "funis"), ("fácil", "fáceis"),
        # an existing accent means the stress is earlier, so no new accent
        ("possível", "possíveis"), ("amável", "amáveis"), ("réptil", "répteis"),
        # -m, -r, -z, -s
        ("homem", "homens"), ("jardim", "jardins"), ("mulher", "mulheres"),
        ("luz", "luzes"), ("país", "países"), ("lápis", "lápis"),
        # the accent goes when -ês/-ás pluralise, but stays on the -ís hiatus
        ("mês", "meses"), ("português", "portugueses"), ("ananás", "ananases"),
        # a hiatus keeps its accent in the plural; a plain -z does not gain one
        ("raiz", "raízes"), ("juiz", "juízes"), ("luz", "luzes"), ("feliz", "felizes"),
        ("férias", "férias"), ("óculos", "óculos"),   # plural-only nouns
        ("casa", "casas"), ("café", "cafés"),
    ]
    for word, want in cases:
        got = pluralize(word)
        assert got == want, f"pluralize({word!r}) = {got!r}, expected {want!r}"

    assert conjugate("falar")["nos"] == "falamos"
    assert conjugate("comer")["tu"] == "comes"
    assert conjugate("partir")["eles_elas_voces"] == "partem"
    assert conjugate("conhecer")["eu"] == "conheço"
    assert conjugate("dirigir")["eu"] == "dirijo"
    assert conjugate("erguer")["eu"] == "ergo"
    assert conjugate("ser")["eu"] == "sou"
    assert conjugate("pôr")["ele_ela_voce"] == "põe"
    # the -ear class: stressed stem takes an i, the nós form does not
    assert conjugate("passear")["eu"] == "passeio"
    assert conjugate("passear")["nos"] == "passeamos"
    assert conjugate("pentear")["eles_elas_voces"] == "penteiam"
    # -zir apocopates the third person singular
    assert conjugate("conduzir")["ele_ela_voce"] == "conduz"
    assert conjugate("traduzir")["eu"] == "traduzo"

    # regular verbs: the two forms coincide, which is why they get confused
    assert personal_infinitive("falar") == future_subjunctive("falar")
    # irregular verbs: they do not, which is the lesson
    assert personal_infinitive("ser")["nos"] == "sermos"
    assert future_subjunctive("ser")["nos"] == "formos"
    assert personal_infinitive("fazer")["nos"] == "fazermos"
    assert future_subjunctive("fazer")["nos"] == "fizermos"

    assert decline_adjective("bonito") == {
        "m_sg_nom": "bonito", "f_sg": "bonita",
        "m_pl": "bonitos", "f_pl": "bonitas"}
    assert decline_adjective("português")["f_sg"] == "portuguesa"
    assert decline_adjective("trabalhador")["f_sg"] == "trabalhadora"
    assert decline_adjective("alemão")["f_sg"] == "alemã"
    assert decline_adjective("verde")["m_pl"] == "verdes"
    assert decline_adjective("espanhol")["f_sg"] == "espanhola"
    assert decline_adjective("espanhol")["m_pl"] == "espanhóis"
    # Brazil: four slots, and você takes the third-person form
    br = conjugate_br("falar")
    assert list(br) == PERSONS_BR
    assert br["voce_ele_ela"] == "fala"
    assert br["nos"] == "falamos"
    assert conjugate_br("ser")["voce_ele_ela"] == "é"
    assert future_subjunctive_br("ir")["nos"] == "formos"
    print("portuguese_morph self-check passed")


if __name__ == "__main__":
    _selfcheck()
