#!/usr/bin/env python3
"""Build vocab_la.json from curated dictionary entries + the morphology generator.

Source lists are compact (the forms a Latin dictionary actually prints); every
paradigm is expanded by latin_morph.py and assert-guarded there. Run:
    python3 scripts/build_latin_vocab.py
then rebuild + validate the trainer as usual.
"""
import json, os, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from latin_morph import decline_noun, conjugate_verb, decline_adjective

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'vocab_la.json')

# ---------------------------------------------------------------------------
# NOUNS: (nominative, genitive, gender, declension, i-stem?, English, lesson)
# Plural-only nouns are listed in PLURAL_ONLY_NOUNS below and give their
# genitive PLURAL instead (castra, castrōrum) since they have no singular.
# ---------------------------------------------------------------------------
NOUNS = [
    # --- L1 people & family -------------------------------------------------
    ("puella", "puellae", "f", 1, False, "girl", "1"),
    ("fēmina", "fēminae", "f", 1, False, "woman", "1"),
    ("puer", "puerī", "m", 2, False, "boy", "1"),
    ("vir", "virī", "m", 2, False, "man", "1"),
    ("homō", "hominis", "m", 3, False, "man, human being", "1"),
    ("pater", "patris", "m", 3, False, "father", "1"),
    ("māter", "mātris", "f", 3, False, "mother", "1"),
    ("frāter", "frātris", "m", 3, False, "brother", "1"),
    ("soror", "sorōris", "f", 3, False, "sister", "1"),
    ("fīlius", "fīliī", "m", 2, False, "son", "1"),
    ("fīlia", "fīliae", "f", 1, False, "daughter", "1"),
    ("amīcus", "amīcī", "m", 2, False, "friend", "1"),
    ("inimīcus", "inimīcī", "m", 2, False, "enemy (personal)", "1"),
    ("dominus", "dominī", "m", 2, False, "master, lord", "1"),
    ("domina", "dominae", "f", 1, False, "mistress, lady", "1"),
    ("servus", "servī", "m", 2, False, "slave", "1"),
    ("ancilla", "ancillae", "f", 1, False, "maidservant", "1"),
    ("nauta", "nautae", "m", 1, False, "sailor", "1"),
    ("agricola", "agricolae", "m", 1, False, "farmer", "1"),
    ("poēta", "poētae", "m", 1, False, "poet", "1"),
    ("nōmen", "nōminis", "n", 3, False, "name", "1"),
    ("vīta", "vītae", "f", 1, False, "life", "1"),
    ("mors", "mortis", "f", 3, True, "death", "1"),
    ("cīvis", "cīvis", "m", 3, True, "citizen", "1"),
    ("populus", "populī", "m", 2, False, "people", "1"),
    ("turba", "turbae", "f", 1, False, "crowd", "1"),
    ("comes", "comitis", "m", 3, False, "companion", "1"),
    ("hospes", "hospitis", "m", 3, False, "guest, host", "1"),
    ("senex", "senis", "m", 3, False, "old man", "1"),
    ("iuvenis", "iuvenis", "m", 3, True, "young man", "1"),

    # --- L2 house & daily life ---------------------------------------------
    ("domus", "domūs", "f", 4, False, "house, home", "2"),
    ("vīlla", "vīllae", "f", 1, False, "country house, villa", "2"),
    ("iānua", "iānuae", "f", 1, False, "door", "2"),
    ("hortus", "hortī", "m", 2, False, "garden, orchard", "2"),
    ("mēnsa", "mēnsae", "f", 1, False, "table", "2"),
    ("cubiculum", "cubiculī", "n", 2, False, "bedroom", "2"),
    ("culīna", "culīnae", "f", 1, False, "kitchen", "2"),
    ("ātrium", "ātriī", "n", 2, False, "atrium, hall", "2"),
    ("mūrus", "mūrī", "m", 2, False, "wall", "2"),
    ("tēctum", "tēctī", "n", 2, False, "roof, house", "2"),
    ("fenestra", "fenestrae", "f", 1, False, "window", "2"),
    ("lectus", "lectī", "m", 2, False, "bed, couch", "2"),
    ("aqua", "aquae", "f", 1, False, "water", "2"),
    ("ignis", "ignis", "m", 3, True, "fire", "2"),
    ("lūmen", "lūminis", "n", 3, False, "light, lamp", "2"),
    ("vestis", "vestis", "f", 3, True, "clothing, garment", "2"),
    ("toga", "togae", "f", 1, False, "toga", "2"),
    ("pecūnia", "pecūniae", "f", 1, False, "money", "2"),
    ("labor", "labōris", "m", 3, False, "work, toil", "2"),
    ("ōtium", "ōtiī", "n", 2, False, "leisure", "2"),
    ("negōtium", "negōtiī", "n", 2, False, "business, task", "2"),
    ("officium", "officiī", "n", 2, False, "duty", "2"),

    # --- L3 town, forum & buildings ----------------------------------------
    ("urbs", "urbis", "f", 3, True, "city", "3"),
    ("oppidum", "oppidī", "n", 2, False, "town", "3"),
    ("via", "viae", "f", 1, False, "road, way, street", "3"),
    ("forum", "forī", "n", 2, False, "forum, marketplace", "3"),
    ("templum", "templī", "n", 2, False, "temple, shrine", "3"),
    ("theātrum", "theātrī", "n", 2, False, "theatre", "3"),
    ("taberna", "tabernae", "f", 1, False, "shop, inn", "3"),
    ("porta", "portae", "f", 1, False, "gate", "3"),
    ("pōns", "pontis", "m", 3, True, "bridge", "3"),
    ("turris", "turris", "f", 3, True, "tower", "3"),
    ("aedificium", "aedificiī", "n", 2, False, "building", "3"),
    ("columna", "columnae", "f", 1, False, "column", "3"),
    ("statua", "statuae", "f", 1, False, "statue", "3"),
    ("locus", "locī", "m", 2, False, "place", "3"),
    ("pars", "partis", "f", 3, True, "part", "3"),

    # --- L4 food & farming --------------------------------------------------
    ("cibus", "cibī", "m", 2, False, "food", "4"),
    ("pānis", "pānis", "m", 3, True, "bread", "4"),
    ("vīnum", "vīnī", "n", 2, False, "wine", "4"),
    ("caro", "carnis", "f", 3, True, "meat, flesh", "4"),
    ("ōvum", "ōvī", "n", 2, False, "egg", "4"),
    ("cēna", "cēnae", "f", 1, False, "dinner", "4"),
    ("mel", "mellis", "n", 3, False, "honey", "4"),
    ("sāl", "salis", "m", 3, False, "salt", "4"),
    ("ager", "agrī", "m", 2, False, "field", "4"),
    ("terra", "terrae", "f", 1, False, "land, earth", "4"),
    ("frūmentum", "frūmentī", "n", 2, False, "grain, corn", "4"),
    ("arbor", "arboris", "f", 3, False, "tree", "4"),
    ("flōs", "flōris", "m", 3, False, "flower", "4"),
    ("rūs", "rūris", "n", 3, False, "countryside", "4"),
    ("fructus", "fructūs", "m", 4, False, "fruit, produce", "4"),

    # --- L5 body, health & senses ------------------------------------------
    ("corpus", "corporis", "n", 3, False, "body", "5"),
    ("caput", "capitis", "n", 3, False, "head", "5"),
    ("manus", "manūs", "f", 4, False, "hand, band of men", "5"),
    ("pēs", "pedis", "m", 3, False, "foot", "5"),
    ("oculus", "oculī", "m", 2, False, "eye", "5"),
    ("auris", "auris", "f", 3, True, "ear", "5"),
    ("ōs", "ōris", "n", 3, False, "mouth, face", "5"),
    ("cor", "cordis", "n", 3, True, "heart", "5"),
    ("sanguis", "sanguinis", "m", 3, False, "blood", "5"),
    ("vōx", "vōcis", "f", 3, False, "voice", "5"),
    ("vulnus", "vulneris", "n", 3, False, "wound", "5"),
    ("dolor", "dolōris", "m", 3, False, "pain, grief", "5"),
    ("somnus", "somnī", "m", 2, False, "sleep", "5"),
    ("morbus", "morbī", "m", 2, False, "disease", "5"),
    ("salūs", "salūtis", "f", 3, False, "health, safety", "5"),
    ("vīs", "vīs", "f", 3, True, "force, strength", "5"),

    # --- L6 school, writing & words ----------------------------------------
    ("liber", "librī", "m", 2, False, "book", "6"),
    ("littera", "litterae", "f", 1, False, "letter (of the alphabet)", "6"),
    ("verbum", "verbī", "n", 2, False, "word", "6"),
    ("magister", "magistrī", "m", 2, False, "teacher, master", "6"),
    ("discipulus", "discipulī", "m", 2, False, "pupil, student", "6"),
    ("schola", "scholae", "f", 1, False, "school", "6"),
    ("fābula", "fābulae", "f", 1, False, "story, play", "6"),
    ("carmen", "carminis", "n", 3, False, "song, poem", "6"),
    ("lingua", "linguae", "f", 1, False, "tongue, language", "6"),
    ("sententia", "sententiae", "f", 1, False, "opinion, sentence", "6"),
    ("exemplum", "exemplī", "n", 2, False, "example", "6"),
    ("studium", "studiī", "n", 2, False, "study, enthusiasm", "6"),
    ("ingenium", "ingeniī", "n", 2, False, "talent, character", "6"),
    ("mēns", "mentis", "f", 3, True, "mind", "6"),
    ("memoria", "memoriae", "f", 1, False, "memory", "6"),
    ("veritās", "veritātis", "f", 3, False, "truth", "6"),

    # --- L7 army, war & weapons --------------------------------------------
    ("bellum", "bellī", "n", 2, False, "war", "7"),
    ("pāx", "pācis", "f", 3, False, "peace", "7"),
    ("mīles", "mīlitis", "m", 3, False, "soldier", "7"),
    ("dux", "ducis", "m", 3, False, "leader, general", "7"),
    ("exercitus", "exercitūs", "m", 4, False, "army", "7"),
    ("legiō", "legiōnis", "f", 3, False, "legion", "7"),
    ("hostis", "hostis", "m", 3, True, "enemy (of the state)", "7"),
    ("gladius", "gladiī", "m", 2, False, "sword", "7"),
    ("hasta", "hastae", "f", 1, False, "spear", "7"),
    ("scūtum", "scūtī", "n", 2, False, "shield", "7"),
    ("proelium", "proeliī", "n", 2, False, "battle", "7"),
    ("victōria", "victōriae", "f", 1, False, "victory", "7"),
    ("perīculum", "perīculī", "n", 2, False, "danger", "7"),
    ("virtūs", "virtūtis", "f", 3, False, "courage, virtue", "7"),
    ("clāmor", "clāmōris", "m", 3, False, "shout, noise", "7"),
    ("custōs", "custōdis", "m", 3, False, "guard", "7"),

    # --- L8 government, law & Rome -----------------------------------------
    ("rēx", "rēgis", "m", 3, False, "king", "8"),
    ("rēgīna", "rēgīnae", "f", 1, False, "queen", "8"),
    ("cōnsul", "cōnsulis", "m", 3, False, "consul", "8"),
    ("senātus", "senātūs", "m", 4, False, "senate", "8"),
    ("lēx", "lēgis", "f", 3, False, "law", "8"),
    ("iūs", "iūris", "n", 3, False, "right, justice", "8"),
    ("imperium", "imperiī", "n", 2, False, "command, empire", "8"),
    ("rēs", "reī", "f", 5, False, "thing, matter, affair", "8"),
    ("cōnsilium", "cōnsiliī", "n", 2, False, "plan, advice", "8"),
    ("nūntius", "nūntiī", "m", 2, False, "messenger, message", "8"),
    ("praemium", "praemiī", "n", 2, False, "reward", "8"),
    ("poena", "poenae", "f", 1, False, "punishment, penalty", "8"),
    ("gēns", "gentis", "f", 3, True, "tribe, people, family", "8"),
    ("patria", "patriae", "f", 1, False, "fatherland, country", "8"),
    ("glōria", "glōriae", "f", 1, False, "glory, fame", "8"),
    ("honor", "honōris", "m", 3, False, "honour, office", "8"),
    ("potestās", "potestātis", "f", 3, False, "power, authority", "8"),

    # --- L9 gods, religion & myth ------------------------------------------
    ("deus", "deī", "m", 2, False, "god", "9"),
    ("dea", "deae", "f", 1, False, "goddess", "9"),
    ("sacerdōs", "sacerdōtis", "m", 3, False, "priest", "9"),
    ("āra", "ārae", "f", 1, False, "altar", "9"),
    ("sacrificium", "sacrificiī", "n", 2, False, "sacrifice", "9"),
    ("fātum", "fātī", "n", 2, False, "fate, destiny", "9"),
    ("fortūna", "fortūnae", "f", 1, False, "fortune, luck", "9"),
    ("animus", "animī", "m", 2, False, "mind, spirit, courage", "9"),
    ("anima", "animae", "f", 1, False, "soul, breath", "9"),
    ("umbra", "umbrae", "f", 1, False, "shadow, ghost", "9"),
    ("mōnstrum", "mōnstrī", "n", 2, False, "monster, omen", "9"),
    ("Iuppiter", "Iovis", "m", 3, False, "Jupiter", "9"),
    ("caelum", "caelī", "n", 2, False, "sky, heaven", "9"),
    ("nūmen", "nūminis", "n", 3, False, "divine power", "9"),

    # --- L10 travel, sea & geography ---------------------------------------
    ("mare", "maris", "n", 3, True, "sea", "10"),
    ("nāvis", "nāvis", "f", 3, True, "ship", "10"),
    ("portus", "portūs", "m", 4, False, "harbour, port", "10"),
    ("īnsula", "īnsulae", "f", 1, False, "island, apartment block", "10"),
    ("unda", "undae", "f", 1, False, "wave", "10"),
    ("ventus", "ventī", "m", 2, False, "wind", "10"),
    ("flūmen", "flūminis", "n", 3, False, "river", "10"),
    ("mōns", "montis", "m", 3, True, "mountain", "10"),
    ("silva", "silvae", "f", 1, False, "wood, forest", "10"),
    ("campus", "campī", "m", 2, False, "plain, field", "10"),
    ("iter", "itineris", "n", 3, False, "journey, route", "10"),
    ("equus", "equī", "m", 2, False, "horse", "10"),
    ("currus", "currūs", "m", 4, False, "chariot", "10"),
    ("rīpa", "rīpae", "f", 1, False, "bank (of a river)", "10"),
    ("saxum", "saxī", "n", 2, False, "rock, stone", "10"),
    ("lītus", "lītoris", "n", 3, False, "shore", "10"),

    # --- L11 time, seasons & weather ---------------------------------------
    ("tempus", "temporis", "n", 3, False, "time", "11"),
    ("diēs", "diēī", "m", 5, False, "day", "11"),
    ("nox", "noctis", "f", 3, True, "night", "11"),
    ("annus", "annī", "m", 2, False, "year", "11"),
    ("mēnsis", "mēnsis", "m", 3, True, "month", "11"),
    ("hōra", "hōrae", "f", 1, False, "hour", "11"),
    ("aestās", "aestātis", "f", 3, False, "summer", "11"),
    ("hiems", "hiemis", "f", 3, False, "winter", "11"),
    ("vēr", "vēris", "n", 3, False, "spring", "11"),
    ("sōl", "sōlis", "m", 3, False, "sun", "11"),
    ("lūna", "lūnae", "f", 1, False, "moon", "11"),
    ("stēlla", "stēllae", "f", 1, False, "star", "11"),
    ("nūbēs", "nūbis", "f", 3, True, "cloud", "11"),
    ("imber", "imbris", "m", 3, True, "rain, shower", "11"),
    ("lūx", "lūcis", "f", 3, False, "light, daylight", "11"),

    # --- L12 animals & nature ----------------------------------------------
    ("animal", "animālis", "n", 3, True, "animal", "12"),
    ("canis", "canis", "m", 3, False, "dog", "12"),
    ("avis", "avis", "f", 3, True, "bird", "12"),
    ("piscis", "piscis", "m", 3, True, "fish", "12"),
    ("leō", "leōnis", "m", 3, False, "lion", "12"),
    ("lupus", "lupī", "m", 2, False, "wolf", "12"),
    ("bōs", "bovis", "m", 3, False, "ox, cow", "12"),
    ("ovis", "ovis", "f", 3, True, "sheep", "12"),
    ("serpēns", "serpentis", "f", 3, True, "snake", "12"),
    ("aquila", "aquilae", "f", 1, False, "eagle", "12"),
]

# Plural-only nouns: (nom pl, GEN PL, gender, declension, i-stem?, English, lesson)
PLURAL_ONLY_NOUNS = [
    ("moenia", "moenium", "n", 3, True, "city walls", "3"),
    ("castra", "castrōrum", "n", 2, False, "camp", "7"),
    ("arma", "armōrum", "n", 2, False, "arms, weapons", "7"),
    ("tenebrae", "tenebrārum", "f", 1, False, "darkness", "11"),
    ("īnsidiae", "īnsidiārum", "f", 1, False, "ambush, trap", "7"),
    ("dīvitiae", "dīvitiārum", "f", 1, False, "riches, wealth", "8"),
]

# ---------------------------------------------------------------------------
# VERBS: (principal parts, conjugation, English, lesson)
# ---------------------------------------------------------------------------
VERBS = [
    # --- L13 core verbs I: 1st & 2nd conjugation ---------------------------
    (["amō", "amāre", "amāvī", "amātum"], 1, "to love", "13"),
    (["laudō", "laudāre", "laudāvī", "laudātum"], 1, "to praise", "13"),
    (["portō", "portāre", "portāvī", "portātum"], 1, "to carry", "13"),
    (["vocō", "vocāre", "vocāvī", "vocātum"], 1, "to call", "13"),
    (["parō", "parāre", "parāvī", "parātum"], 1, "to prepare", "13"),
    (["pugnō", "pugnāre", "pugnāvī", "pugnātum"], 1, "to fight", "13"),
    (["ambulō", "ambulāre", "ambulāvī", "ambulātum"], 1, "to walk", "13"),
    (["labōrō", "labōrāre", "labōrāvī", "labōrātum"], 1, "to work", "13"),
    (["spectō", "spectāre", "spectāvī", "spectātum"], 1, "to watch, look at", "13"),
    (["intrō", "intrāre", "intrāvī", "intrātum"], 1, "to enter", "13"),
    (["nārrō", "nārrāre", "nārrāvī", "nārrātum"], 1, "to tell, relate", "13"),
    (["superō", "superāre", "superāvī", "superātum"], 1, "to overcome, surpass", "13"),
    (["servō", "servāre", "servāvī", "servātum"], 1, "to save, guard", "13"),
    (["oppugnō", "oppugnāre", "oppugnāvī", "oppugnātum"], 1, "to attack", "13"),
    (["exspectō", "exspectāre", "exspectāvī", "exspectātum"], 1, "to wait for, expect", "13"),
    (["rogō", "rogāre", "rogāvī", "rogātum"], 1, "to ask", "13"),
    (["dō", "dare", "dedī", "datum"], 1, "to give", "13"),
    (["stō", "stāre", "stetī", "statum"], 1, "to stand", "13"),
    (["habeō", "habēre", "habuī", "habitum"], 2, "to have, hold", "13"),
    (["videō", "vidēre", "vīdī", "vīsum"], 2, "to see", "13"),
    (["moneō", "monēre", "monuī", "monitum"], 2, "to warn, advise", "13"),
    (["teneō", "tenēre", "tenuī", "tentum"], 2, "to hold", "13"),
    (["timeō", "timēre", "timuī"], 2, "to fear", "13"),
    (["maneō", "manēre", "mānsī", "mānsum"], 2, "to remain, stay", "13"),
    (["moveō", "movēre", "mōvī", "mōtum"], 2, "to move", "13"),
    (["respondeō", "respondēre", "respondī", "respōnsum"], 2, "to reply", "13"),
    (["iubeō", "iubēre", "iussī", "iussum"], 2, "to order, bid", "13"),
    (["dēleō", "dēlēre", "dēlēvī", "dēlētum"], 2, "to destroy", "13"),
    (["terreō", "terrēre", "terruī", "territum"], 2, "to frighten", "13"),
    (["doceō", "docēre", "docuī", "doctum"], 2, "to teach", "13"),
    (["rīdeō", "rīdēre", "rīsī", "rīsum"], 2, "to laugh, smile", "13"),
    (["sedeō", "sedēre", "sēdī", "sessum"], 2, "to sit", "13"),

    # --- L14 core verbs II: 3rd, 4th & irregular ---------------------------
    (["regō", "regere", "rēxī", "rēctum"], 3, "to rule", "14"),
    (["dūcō", "dūcere", "dūxī", "ductum"], 3, "to lead", "14"),
    (["mittō", "mittere", "mīsī", "missum"], 3, "to send", "14"),
    (["dīcō", "dīcere", "dīxī", "dictum"], 3, "to say, speak", "14"),
    (["scrībō", "scrībere", "scrīpsī", "scrīptum"], 3, "to write", "14"),
    (["legō", "legere", "lēgī", "lēctum"], 3, "to read, choose", "14"),
    (["agō", "agere", "ēgī", "āctum"], 3, "to do, drive", "14"),
    (["pōnō", "pōnere", "posuī", "positum"], 3, "to place, put", "14"),
    (["vincō", "vincere", "vīcī", "victum"], 3, "to conquer", "14"),
    (["currō", "currere", "cucurrī", "cursum"], 3, "to run", "14"),
    (["petō", "petere", "petīvī", "petītum"], 3, "to seek, ask for", "14"),
    (["gerō", "gerere", "gessī", "gestum"], 3, "to carry on, wage", "14"),
    (["trahō", "trahere", "trāxī", "tractum"], 3, "to drag, draw", "14"),
    (["vīvō", "vīvere", "vīxī", "vīctum"], 3, "to live", "14"),
    (["bibō", "bibere", "bibī"], 3, "to drink", "14"),
    (["claudō", "claudere", "clausī", "clausum"], 3, "to close, shut", "14"),
    (["crēdō", "crēdere", "crēdidī", "crēditum"], 3, "to believe, trust", "14"),
    (["ostendō", "ostendere", "ostendī", "ostentum"], 3, "to show", "14"),
    (["capiō", "capere", "cēpī", "captum"], "3io", "to take, capture", "14"),
    (["faciō", "facere", "fēcī", "factum"], "3io", "to make, do", "14"),
    (["fugiō", "fugere", "fūgī", "fugitum"], "3io", "to flee", "14"),
    (["iaciō", "iacere", "iēcī", "iactum"], "3io", "to throw", "14"),
    (["accipiō", "accipere", "accēpī", "acceptum"], "3io", "to receive, accept", "14"),
    (["audiō", "audīre", "audīvī", "audītum"], 4, "to hear, listen to", "14"),
    (["veniō", "venīre", "vēnī", "ventum"], 4, "to come", "14"),
    (["inveniō", "invenīre", "invēnī", "inventum"], 4, "to find", "14"),
    (["dormiō", "dormīre", "dormīvī", "dormītum"], 4, "to sleep", "14"),
    (["sentiō", "sentīre", "sēnsī", "sēnsum"], 4, "to feel, perceive", "14"),
    (["custōdiō", "custōdīre", "custōdīvī", "custōdītum"], 4, "to guard", "14"),
    (["impediō", "impedīre", "impedīvī", "impedītum"], 4, "to hinder", "14"),
    (["sum", "esse", "fuī"], 1, "to be", "14"),
    (["possum", "posse", "potuī"], 1, "to be able, can", "14"),
    (["eō", "īre", "iī", "itum"], 1, "to go", "14"),
    (["ferō", "ferre", "tulī", "lātum"], 1, "to bring, carry, bear", "14"),
    (["volō", "velle", "voluī"], 1, "to wish, be willing", "14"),
    (["nōlō", "nōlle", "nōluī"], 1, "to be unwilling, refuse", "14"),
    (["mālō", "mālle", "māluī"], 1, "to prefer", "14"),
]

# ---------------------------------------------------------------------------
# ADJECTIVES: (nominative, type, base-or-None, English, lesson)
# ---------------------------------------------------------------------------
ADJECTIVES = [
    ("bonus", "us", None, "good", "15"),
    ("malus", "us", None, "bad, wicked", "15"),
    ("magnus", "us", None, "big, great", "15"),
    ("parvus", "us", None, "small", "15"),
    ("longus", "us", None, "long", "15"),
    ("altus", "us", None, "high, deep", "15"),
    ("lātus", "us", None, "wide, broad", "15"),
    ("novus", "us", None, "new", "15"),
    ("antīquus", "us", None, "ancient, old", "15"),
    ("multus", "us", None, "much, many", "15"),
    ("plēnus", "us", None, "full", "15"),
    ("clārus", "us", None, "clear, famous", "15"),
    ("cārus", "us", None, "dear, precious", "15"),
    ("dūrus", "us", None, "hard, harsh", "15"),
    ("laetus", "us", None, "happy, glad", "15"),
    ("īrātus", "us", None, "angry", "15"),
    ("validus", "us", None, "strong", "15"),
    ("beātus", "us", None, "blessed, happy", "15"),
    ("certus", "us", None, "certain, sure", "15"),
    ("dignus", "us", None, "worthy", "15"),
    ("prīmus", "us", None, "first", "15"),
    ("sōlus", "us", None, "alone, only", "15"),
    ("tōtus", "us", None, "whole, entire", "15"),
    ("meus", "us", None, "my", "15"),
    ("tuus", "us", None, "your (sg.)", "15"),
    ("noster", "er", "nostr", "our", "15"),
    ("vester", "er", "vestr", "your (pl.)", "15"),
    ("miser", "er", "miser", "wretched, unhappy", "15"),
    ("pulcher", "er", "pulchr", "beautiful, handsome", "15"),
    ("aeger", "er", "aegr", "sick, ill", "15"),
    ("sacer", "er", "sacr", "sacred", "15"),
    ("līber", "er", "līber", "free", "15"),
    ("fortis", "3-2", None, "brave, strong", "15"),
    ("omnis", "3-2", None, "all, every", "15"),
    ("gravis", "3-2", None, "heavy, serious", "15"),
    ("facilis", "3-2", None, "easy", "15"),
    ("difficilis", "3-2", None, "difficult", "15"),
    ("similis", "3-2", None, "similar, like", "15"),
    ("trīstis", "3-2", None, "sad", "15"),
    ("brevis", "3-2", None, "short, brief", "15"),
    ("nōbilis", "3-2", None, "noble, well-known", "15"),
    ("crūdēlis", "3-2", None, "cruel", "15"),
    ("dulcis", "3-2", None, "sweet", "15"),
    ("fidēlis", "3-2", None, "faithful", "15"),
    ("ūtilis", "3-2", None, "useful", "15"),
    ("ingēns", "3-1", "ingent", "huge, enormous", "15"),
    ("audāx", "3-1", "audāc", "bold, daring", "15"),
    ("fēlīx", "3-1", "fēlīc", "lucky, fortunate", "15"),
    ("sapiēns", "3-1", "sapient", "wise", "15"),
    ("potēns", "3-1", "potent", "powerful", "15"),
    ("ācer", "3-3", "ācr", "keen, fierce, sharp", "15"),
    ("celer", "3-3", "celer", "swift, quick", "15"),
]

# ---------------------------------------------------------------------------
# Indeclinables and closed classes: (Latin, English, pos, lesson)
# ---------------------------------------------------------------------------
OTHERS = [
    # adverbs
    ("nōn", "not", "adverb", "1"), ("semper", "always", "adverb", "11"),
    ("saepe", "often", "adverb", "11"), ("numquam", "never", "adverb", "11"),
    ("nunc", "now", "adverb", "11"), ("tum", "then, at that time", "adverb", "11"),
    ("iam", "now, already", "adverb", "11"), ("hodiē", "today", "adverb", "11"),
    ("herī", "yesterday", "adverb", "11"), ("crās", "tomorrow", "adverb", "11"),
    ("diū", "for a long time", "adverb", "11"), ("statim", "immediately", "adverb", "11"),
    ("subitō", "suddenly", "adverb", "11"), ("mox", "soon", "adverb", "11"),
    ("ibi", "there", "adverb", "3"), ("hīc", "here", "adverb", "3"),
    ("ubi", "where, when", "adverb", "3"), ("undique", "from all sides", "adverb", "3"),
    ("bene", "well", "adverb", "15"), ("male", "badly", "adverb", "15"),
    ("valdē", "very, strongly", "adverb", "15"), ("tandem", "at last", "adverb", "15"),
    ("etiam", "also, even", "adverb", "15"), ("quoque", "also, too", "adverb", "15"),
    ("forte", "by chance", "adverb", "15"), ("frūstrā", "in vain", "adverb", "15"),
    ("celeriter", "quickly", "adverb", "15"), ("fortiter", "bravely", "adverb", "15"),
    ("facile", "easily", "adverb", "15"), ("cūr", "why", "adverb", "15"),
    # prepositions
    ("ad", "to, towards (+ acc.)", "preposition", "3"),
    ("in", "in, on (+ abl.); into (+ acc.)", "preposition", "3"),
    ("ex", "out of, from (+ abl.)", "preposition", "3"),
    ("ab", "from, by (+ abl.)", "preposition", "3"),
    ("cum", "with (+ abl.)", "preposition", "3"),
    ("sine", "without (+ abl.)", "preposition", "3"),
    ("per", "through (+ acc.)", "preposition", "3"),
    ("prope", "near (+ acc.)", "preposition", "3"),
    ("post", "after, behind (+ acc.)", "preposition", "3"),
    ("ante", "before, in front of (+ acc.)", "preposition", "3"),
    ("inter", "between, among (+ acc.)", "preposition", "3"),
    ("trāns", "across (+ acc.)", "preposition", "3"),
    ("sub", "under (+ abl./acc.)", "preposition", "3"),
    ("dē", "down from, about (+ abl.)", "preposition", "3"),
    ("prō", "in front of, on behalf of (+ abl.)", "preposition", "3"),
    ("contrā", "against (+ acc.)", "preposition", "7"),
    # conjunctions
    ("et", "and", "conjunction", "1"), ("sed", "but", "conjunction", "1"),
    ("aut", "or", "conjunction", "1"), ("nam", "for", "conjunction", "1"),
    ("quod", "because", "conjunction", "1"), ("quia", "because", "conjunction", "1"),
    ("sī", "if", "conjunction", "1"), ("ubi2", "when", "conjunction", "1"),
    ("dum", "while", "conjunction", "1"), ("tamen", "however, nevertheless", "conjunction", "1"),
    ("igitur", "therefore", "conjunction", "1"), ("enim", "for, indeed", "conjunction", "1"),
    ("atque", "and, and also", "conjunction", "1"), ("neque", "and not, nor", "conjunction", "1"),
    # pronouns
    ("ego", "I", "pronoun", "1"), ("tū", "you (sg.)", "pronoun", "1"),
    ("nōs", "we, us", "pronoun", "1"), ("vōs", "you (pl.)", "pronoun", "1"),
    ("is", "he, that", "pronoun", "1"), ("ea", "she, that", "pronoun", "1"),
    ("id", "it, that", "pronoun", "1"), ("hic", "this, this man", "pronoun", "1"),
    ("ille", "that, that man", "pronoun", "1"), ("quī", "who, which", "pronoun", "1"),
    ("quis", "who?", "pronoun", "1"), ("quid", "what?", "pronoun", "1"),
    ("sē", "himself, herself, themselves", "pronoun", "1"),
    ("nēmō", "no one", "pronoun", "1"), ("nihil", "nothing", "pronoun", "1"),
    ("omnia", "everything, all things", "pronoun", "1"),
    # numerals
    ("ūnus", "one", "number", "11"), ("duo", "two", "number", "11"),
    ("trēs", "three", "number", "11"), ("quattuor", "four", "number", "11"),
    ("quīnque", "five", "number", "11"), ("sex", "six", "number", "11"),
    ("septem", "seven", "number", "11"), ("octō", "eight", "number", "11"),
    ("novem", "nine", "number", "11"), ("decem", "ten", "number", "11"),
    ("centum", "a hundred", "number", "11"), ("mīlle", "a thousand", "number", "11"),
]

# Homographs differing only in part of speech (ubi adv. "where" / conj. "when")
# carry a numeric suffix in the source list purely to keep the Python keys
# unique; it is stripped here, and (la, pos) uniqueness does the real work.
DEDUPE_SUFFIX = {"ubi2": "ubi"}

# ---------------------------------------------------------------------------
# Cloze sentences: headword -> [(sentence with {target}, English), ...]
# ---------------------------------------------------------------------------
CLOZE = {
    "puella": [("{Puella} in viā ambulat.", "The girl walks in the road."),
               ("Magister {puellās} laudat.", "The teacher praises the girls.")],
    "puer": [("{Puerī} in hortō lūdunt.", "The boys play in the garden."),
             ("Pater {puerum} vocat.", "The father calls the boy.")],
    "via": [("In {viā} multī hominēs sunt.", "There are many people in the street."),
            ("{Viae} Rōmānae longae erant.", "Roman roads were long.")],
    "urbs": [("{Urbs} magna et clāra est.", "The city is great and famous."),
             ("Hostēs {urbem} oppugnāvērunt.", "The enemy attacked the city.")],
    "rēx": [("{Rēx} populum regit.", "The king rules the people."),
            ("Mīlitēs {rēgem} laudāvērunt.", "The soldiers praised the king.")],
    "mīles": [("{Mīles} fortiter pugnat.", "The soldier fights bravely."),
              ("Dux {mīlitēs} ad bellum dūxit.", "The leader led the soldiers to war.")],
    "corpus": [("{Corpus} mīlitis vulnerātum est.", "The soldier's body was wounded."),
               ("{Corpora} in lītore iacēbant.", "The bodies lay on the shore.")],
    "tempus": [("{Tempus} fugit.", "Time flies."),
               ("Illō {tempore} Rōma parva erat.", "At that time Rome was small.")],
    "diēs": [("{Diēs} longus est.", "The day is long."),
             ("Post trēs {diēs} vēnit.", "He came after three days.")],
    "nox": [("{Nox} erat obscūra.", "The night was dark."),
            ("{Nocte} mīlitēs vēnērunt.", "The soldiers came by night.")],
    "mare": [("{Mare} lātum est.", "The sea is wide."),
             ("Nāvis in {marī} nāvigat.", "The ship sails on the sea.")],
    "nāvis": [("{Nāvis} ad portum vēnit.", "The ship came to the harbour."),
              ("Multae {nāvēs} in portū erant.", "There were many ships in the harbour.")],
    "manus": [("{Manus} eius fortis est.", "His hand is strong."),
              ("In {manibus} gladiōs tenēbant.", "They held swords in their hands.")],
    "amō": [("Puella puerum {amat}.", "The girl loves the boy."),
            ("Nōs patriam {amāmus}.", "We love our country.")],
    "videō": [("Ego templum {videō}.", "I see the temple."),
              ("Herī rēgem {vīdimus}.", "Yesterday we saw the king.")],
    "sum": [("Puer in hortō {est}.", "The boy is in the garden."),
            ("Nōs Rōmānī {sumus}.", "We are Romans.")],
    "possum": [("Ego currere {possum}.", "I am able to run."),
               ("Mīlitēs urbem capere {poterant}.", "The soldiers were able to capture the city.")],
    "dūcō": [("Dux exercitum {dūcit}.", "The leader leads the army."),
             ("Caesar mīlitēs trāns flūmen {dūxit}.", "Caesar led the soldiers across the river.")],
    "dīcō": [("Quid {dīcis}?", "What are you saying?"),
             ("Poēta fābulam {dīxit}.", "The poet told a story.")],
    "faciō": [("Quid {facis}?", "What are you doing?"),
              ("Servī cēnam {fēcērunt}.", "The slaves made the dinner.")],
    "capiō": [("Hostēs oppidum {capiunt}.", "The enemy are capturing the town."),
              ("Mīlitēs multōs captīvōs {cēpērunt}.", "The soldiers captured many prisoners.")],
    "veniō": [("Amīcus meus {venit}.", "My friend is coming."),
              ("Nūntiī ad urbem {vēnērunt}.", "The messengers came to the city.")],
    "audiō": [("Vōcem {audiō}.", "I hear a voice."),
              ("{Audīvistīne} clāmōrem?", "Did you hear the shout?")],
    "scrībō": [("Poēta carmen {scrībit}.", "The poet is writing a poem."),
               ("Multās litterās {scrīpsī}.", "I wrote many letters.")],
    "eō": [("Ad forum {eō}.", "I am going to the forum."),
           ("Nōs ad templum {īmus}.", "We are going to the temple.")],
    "ferō": [("Servus aquam {fert}.", "The slave carries water."),
             ("Mīlitēs arma {tulērunt}.", "The soldiers carried arms.")],
    "volō": [("Ego venīre {volō}.", "I want to come."),
             ("Quid {vīs}?", "What do you want?")],
    "magnus": [("{Magna} urbs est.", "It is a great city."),
               ("{Magnī} mīlitēs pugnāvērunt.", "Great soldiers fought.")],
    "bonus": [("Puer {bonus} est.", "The boy is good."),
              ("{Bonae} puellae labōrant.", "The good girls work.")],
    "omnis": [("{Omnēs} cīvēs vēnērunt.", "All the citizens came."),
              ("{Omnia} bona sunt.", "All things are good.")],
    "fortis": [("Mīles {fortis} est.", "The soldier is brave."),
               ("{Fortēs} virī patriam servant.", "Brave men save their country.")],
    "ingēns": [("{Ingēns} mōnstrum vēnit.", "A huge monster came."),
               ("{Ingentēs} montēs vidēmus.", "We see huge mountains.")],
    "deus": [("{Deus} caelum regit.", "The god rules the sky."),
             ("Rōmānī {deōs} timēbant.", "The Romans feared the gods.")],
    "aqua": [("{Aqua} frīgida est.", "The water is cold."),
             ("Servī {aquam} portant.", "The slaves carry water.")],
    "liber": [("{Liber} in mēnsā est.", "The book is on the table."),
              ("Multōs {librōs} lēgī.", "I have read many books.")],
}

# ---------------------------------------------------------------------------
# Antonym / synonym pairs, by headword.
# ---------------------------------------------------------------------------
ANTONYMS = [
    ("bonus", "malus"), ("magnus", "parvus"), ("longus", "brevis"),
    ("novus", "antīquus"), ("laetus", "trīstis"), ("facilis", "difficilis"),
    ("bellum", "pāx"), ("vīta", "mors"), ("diēs", "nox"), ("aestās", "hiems"),
    ("amīcus", "inimīcus"), ("dominus", "servus"), ("pater", "māter"),
    ("frāter", "soror"), ("fīlius", "fīlia"), ("puer", "puella"),
    ("vir", "fēmina"), ("rēx", "rēgīna"), ("deus", "dea"), ("terra", "caelum"),
    ("sōl", "lūna"), ("lūx", "tenebrae"), ("bene", "male"), ("semper", "numquam"),
    ("labor", "ōtium"), ("ante", "post"), ("hodiē", "crās"),
]
SYNONYMS = [
    ("urbs", "oppidum"), ("perīculum", "morbus"), ("cōnsilium", "sententia"),
    ("gladius", "hasta"), ("clāmor", "vōx"), ("quod", "quia"),
    ("etiam", "quoque"), ("animus", "mēns"), ("hostis", "inimīcus"),
    ("timeō", "terreō"), ("via", "iter"),
]


def build():
    entries, by_head = [], {}
    n = 0

    def nid():
        nonlocal n
        n += 1
        return f"la{n:04d}"

    def add(entry, head_key):
        entries.append(entry)
        by_head.setdefault(head_key, entry)

    for nom, gen, gender, decl, istem, en, lesson in NOUNS:
        head = DEDUPE_SUFFIX.get(nom, nom)
        decl_forms = decline_noun(head, gen, gender, decl, istem=istem)
        e = {"la": head, "en": en, "pos": "noun", "id": nid(), "lesson": lesson,
             "gender": gender, "declension": decl, "gen_sg": gen, "noun_decl": decl_forms}
        add(e, nom)

    for nom, gen_pl, gender, decl, istem, en, lesson in PLURAL_ONLY_NOUNS:
        decl_forms = decline_noun(nom, gen_pl, gender, decl,
                                  istem=istem, plural_only=True)
        e = {"la": nom, "en": en, "pos": "noun", "id": nid(), "lesson": lesson,
             "gender": gender, "declension": decl, "gen_sg": gen_pl,
             "plural_only": True, "noun_decl": decl_forms}
        add(e, nom)

    for pp, conj, en, lesson in VERBS:
        head = pp[0]
        e = {"la": head, "en": en, "pos": "verb", "id": nid(), "lesson": lesson,
             "conjugation": conjugate_verb(pp, conj), "principal_parts": pp,
             "conj_class": conj}
        add(e, head)

    for nom, atype, base, en, lesson in ADJECTIVES:
        e = {"la": nom, "en": en, "pos": "adjective", "id": nid(), "lesson": lesson,
             "adj_type": atype, "declension_forms": atype,
             "declension": decline_adjective(nom, atype, base=base)}
        add(e, nom)

    for la, en, pos, lesson in OTHERS:
        head = DEDUPE_SUFFIX.get(la, la)
        e = {"la": head, "en": en, "pos": pos, "id": nid(), "lesson": lesson}
        add(e, la)

    # Cloze
    attached = 0
    for head, sents in CLOZE.items():
        e = by_head.get(head)
        assert e is not None, f"cloze references unknown headword {head!r}"
        e["cloze"] = [{"la": s, "en": t} for s, t in sents]
        attached += len(sents)

    # Antonyms / synonyms, linked both ways
    def link(pairs, field):
        for a, b in pairs:
            ea, eb = by_head.get(a), by_head.get(b)
            assert ea is not None, f"{field}: unknown headword {a!r}"
            assert eb is not None, f"{field}: unknown headword {b!r}"
            ea.setdefault(field, [])
            eb.setdefault(field, [])
            if eb["id"] not in ea[field]:
                ea[field].append(eb["id"])
            if ea["id"] not in eb[field]:
                eb[field].append(ea["id"])
    link(ANTONYMS, "antonyms")
    link(SYNONYMS, "synonyms")

    # ---- integrity checks -------------------------------------------------
    ids = [e["id"] for e in entries]
    assert len(ids) == len(set(ids)), "duplicate entry ids"
    keys = [(e["la"], e["pos"]) for e in entries]
    dupes = [k for k, c in collections.Counter(keys).items() if c > 1]
    assert not dupes, f"duplicate (la, pos) keys: {dupes}"
    byid = {e["id"]: e for e in entries}
    for e in entries:
        for field in ("antonyms", "synonyms"):
            for rid in e.get(field, []):
                assert rid in byid, f"{e['la']}: dangling {field} id {rid}"
        for c in e.get("cloze", []):
            assert c["la"].count("{") == 1 and c["la"].count("}") == 1, \
                f"{e['la']}: cloze must wrap exactly one target: {c['la']!r}"
        for group in ("noun_decl", "declension"):
            if isinstance(e.get(group), dict):
                for k, v in e[group].items():
                    assert v and v.strip(), f"{e['la']}: blank form for {group}.{k}"
        if e["pos"] == "verb":
            for tense, forms in e["conjugation"].items():
                assert len(forms) == 6, f"{e['la']}: {tense} has {len(forms)} persons"

    data = {
        "entries": entries,
        "meta": {"language": "Latin", "reference": "English",
                 "level": "school years 1-2", "version": "v1"},
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    counts = collections.Counter(e["pos"] for e in entries)
    print(f"wrote {os.path.normpath(OUT)}: {len(entries)} entries")
    print("  " + " · ".join(f"{v} {k}" for k, v in counts.most_common()))
    print(f"  cloze sentences: {attached} across {len(CLOZE)} words")
    print(f"  antonym pairs: {len(ANTONYMS)} · synonym pairs: {len(SYNONYMS)}")


if __name__ == "__main__":
    build()
