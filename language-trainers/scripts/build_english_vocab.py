#!/usr/bin/env python3
"""Build vocab_en.json: a curated A1-A2 English word list, glossed in German.

This is the starter deck for the English trainer (see HANDOFF_EN.md) --
English is the HEADWORD here (the language being drilled, with its own
conjugation/principal-parts/plural/comparison), German is the bare gloss, same
direction as the Polish trainer (pl headword / de gloss) but with English's far
lighter grammar: no case, no gender, no adjective agreement. Regular forms are
derived by scripts/english_morph.py; this file only says what's IRREGULAR or
otherwise worth drilling, same split as latin_morph.py/build_latin_vocab.py.

8 starter lessons (greetings, family, numbers/time, food, everyday verbs,
adjectives, home, time/weather) -- a deliberately small first slice to prove
the engine out, same way every other trainer here grew lesson by lesson rather
than shipping complete. More lessons are easy to add: append to the lists
below and re-run.

    python3 scripts/build_english_vocab.py
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import english_morph as M

entries = []
_ids = {"verb": 0, "noun": 0, "adjective": 0, "other": 0}


def _id(pos):
    prefix = {"verb": "v", "noun": "n", "adjective": "a"}.get(pos, "o")
    _ids.setdefault(pos, 0)
    _ids[pos] += 1
    return f"{prefix}{_ids[pos]:03d}"


def add_verb(base, de, lesson, cloze=None):
    pp = M.principal_parts(base)
    e = {
        "en": "to " + base, "de": de, "pos": "verb", "id": _id("verb"), "lesson": lesson,
        "conjugation": M.conjugate_present(base),
    }
    if pp:
        e["principal_parts"] = pp
    if cloze:
        e["cloze"] = [{"en": en_s, "de": de_s} for en_s, de_s in cloze]
    entries.append(e)
    return e


def add_noun(word, de, lesson, irregular_plural=False, uncountable=False, cloze=None):
    e = {"en": word, "de": de, "pos": "noun", "id": _id("noun"), "lesson": lesson}
    if not uncountable:
        try:
            e["plural"] = M.plural_of(word, irregular=irregular_plural)
        except AssertionError:
            raise
        # only keep the plural field when it's actually worth drilling --
        # i.e. not the fully-predictable "+s" case
        if not irregular_plural and e["plural"] == word + "s":
            del e["plural"]
    if cloze:
        e["cloze"] = [{"en": en_s, "de": de_s} for en_s, de_s in cloze]
    entries.append(e)
    return e


def add_adjective(word, de, lesson, degree=None, cloze=None):
    e = {"en": word, "de": de, "pos": "adjective", "id": _id("adjective"), "lesson": lesson}
    if degree is not None or word in M.IRREGULAR_COMPARISON:
        e["comparison"] = M.comparison_forms(word, degree or "more")
    if cloze:
        e["cloze"] = [{"en": en_s, "de": de_s} for en_s, de_s in cloze]
    entries.append(e)
    return e


def add_other(pos, word, de, lesson, cloze=None):
    e = {"en": word, "de": de, "pos": pos, "id": _id("other"), "lesson": lesson}
    if cloze:
        e["cloze"] = [{"en": en_s, "de": de_s} for en_s, de_s in cloze]
    entries.append(e)
    return e


# === Lesson 1: Greetings & basics ===========================================
add_other("pronoun", "I", "ich", "1")
add_other("pronoun", "you", "du", "1")
add_other("pronoun", "he", "er", "1")
add_other("pronoun", "she", "sie", "1")
add_other("pronoun", "it", "es", "1")
add_other("pronoun", "we", "wir", "1")
add_other("pronoun", "they", "sie", "1")

add_verb("be", "sein", "1", cloze=[
    ("I {am} happy.", "Ich bin glücklich."),
    ("You {are} late.", "Du bist spät dran."),
    ("She {is} a doctor.", "Sie ist Ärztin."),
])

add_other("phrase", "hello", "hallo", "1")
add_other("phrase", "good morning", "guten Morgen", "1")
add_other("phrase", "good evening", "guten Abend", "1")
add_other("phrase", "good night", "gute Nacht", "1")
add_other("phrase", "goodbye", "auf Wiedersehen", "1")
add_other("phrase", "please", "bitte", "1")
add_other("phrase", "thank you", "danke", "1")
add_other("phrase", "yes", "ja", "1")
add_other("phrase", "no", "nein", "1")
add_other("phrase", "excuse me", "entschuldigung", "1")
add_other("phrase", "sorry", "es tut mir leid", "1")
add_other("phrase", "how are you?", "wie geht es dir?", "1", cloze=[
    ("“How {are you}?” — “Fine, thanks.”", "„Wie geht es dir?“ — „Gut, danke.“"),
])
add_other("phrase", "my name is", "ich heiße", "1")
add_other("phrase", "nice to meet you", "freut mich", "1")

# === Lesson 2: Family ========================================================
add_noun("father", "Vater", "2")
add_noun("mother", "Mutter", "2")
add_noun("parent", "Elternteil", "2")
add_noun("brother", "Bruder", "2")
add_noun("sister", "Schwester", "2")
add_noun("son", "Sohn", "2")
add_noun("daughter", "Tochter", "2")
add_noun("child", "Kind", "2", irregular_plural=True, cloze=[
    ("The {child} is playing in the garden.", "Das Kind spielt im Garten."),
])
add_noun("husband", "Ehemann", "2")
add_noun("wife", "Ehefrau", "2")  # regular -fe -> -ves spelling change (wives)
add_noun("grandmother", "Großmutter", "2")
add_noun("grandfather", "Großvater", "2")
add_noun("friend", "Freund", "2", cloze=[
    ("She is my best {friend}.", "Sie ist meine beste Freundin."),
])
add_noun("family", "Familie", "2")
add_noun("baby", "Baby", "2")

# === Lesson 3: Numbers & time =================================================
for w, de in [("one","eins"),("two","zwei"),("three","drei"),("four","vier"),("five","fünf"),
              ("six","sechs"),("seven","sieben"),("eight","acht"),("nine","neun"),("ten","zehn")]:
    add_other("number", w, de, "3")

add_other("adverb", "today", "heute", "3")
add_other("adverb", "tomorrow", "morgen", "3")
add_other("adverb", "yesterday", "gestern", "3")
add_noun("day", "Tag", "3", cloze=[
    ("Have a nice {day}!", "Hab einen schönen Tag!"),
])
add_noun("week", "Woche", "3")
add_noun("month", "Monat", "3")
add_noun("year", "Jahr", "3")
add_noun("hour", "Stunde", "3")
add_noun("minute", "Minute", "3")
add_noun("time", "Zeit", "3", uncountable=True)

# === Lesson 4: Food & drink ===================================================
add_noun("bread", "Brot", "4", uncountable=True)
add_noun("water", "Wasser", "4", uncountable=True)
add_noun("coffee", "Kaffee", "4", uncountable=True)
add_noun("tea", "Tee", "4", uncountable=True)
add_noun("milk", "Milch", "4", uncountable=True)
add_noun("apple", "Apfel", "4")
add_noun("egg", "Ei", "4")
add_noun("cheese", "Käse", "4", uncountable=True)
add_noun("meat", "Fleisch", "4", uncountable=True)
add_noun("fish", "Fisch", "4", irregular_plural=True)
add_noun("vegetable", "Gemüse", "4")
add_noun("fruit", "Obst", "4", uncountable=True)
add_noun("breakfast", "Frühstück", "4")
add_noun("lunch", "Mittagessen", "4")
add_noun("dinner", "Abendessen", "4")
add_noun("restaurant", "Restaurant", "4")

add_verb("eat", "essen", "4", cloze=[
    ("I {eat} breakfast at seven.", "Ich frühstücke um sieben."),
    ("Yesterday we {ate} fish.", "Gestern haben wir Fisch gegessen."),
])
add_verb("drink", "trinken", "4", cloze=[
    ("He {drinks} coffee every morning.", "Er trinkt jeden Morgen Kaffee."),
])
add_verb("cook", "kochen", "4")

# === Lesson 5: Everyday verbs ==================================================
add_verb("go", "gehen", "5", cloze=[
    ("I {go} to work by bus.", "Ich fahre mit dem Bus zur Arbeit."),
    ("She {went} home early.", "Sie ging früh nach Hause."),
])
add_verb("come", "kommen", "5", cloze=[
    ("Can you {come} here, please?", "Kannst du bitte herkommen?"),
])
add_verb("have", "haben", "5", cloze=[
    ("He {has} two sisters.", "Er hat zwei Schwestern."),
])
add_verb("do", "tun", "5")
add_verb("make", "machen", "5", cloze=[
    ("I {make} dinner every evening.", "Ich mache jeden Abend das Abendessen."),
])
add_verb("see", "sehen", "5", cloze=[
    ("I {see} you tomorrow.", "Ich sehe dich morgen."),
])
add_verb("know", "wissen", "5")
add_verb("think", "denken", "5")
add_verb("want", "wollen", "5")
add_verb("need", "brauchen", "5")
add_verb("like", "mögen", "5", cloze=[
    ("I {like} this song.", "Ich mag dieses Lied."),
])
add_verb("work", "arbeiten", "5", cloze=[
    ("She {works} in a hospital.", "Sie arbeitet in einem Krankenhaus."),
])
add_verb("live", "wohnen", "5", cloze=[
    ("They {live} in Berlin.", "Sie wohnen in Berlin."),
])
add_verb("speak", "sprechen", "5", cloze=[
    ("Do you {speak} German?", "Sprichst du Deutsch?"),
])
add_verb("understand", "verstehen", "5")
add_verb("read", "lesen", "5")
add_verb("write", "schreiben", "5")
add_verb("buy", "kaufen", "5", cloze=[
    ("I {bought} a new phone.", "Ich habe ein neues Handy gekauft."),
])
add_verb("give", "geben", "5")
add_verb("take", "nehmen", "5")
add_verb("sleep", "schlafen", "5", cloze=[
    ("The baby {is sleeping}.", "Das Baby schläft."),
])
add_verb("run", "rennen", "5")
add_verb("walk", "laufen", "5")

# === Lesson 6: Adjectives ======================================================
add_adjective("big", "groß", "6", degree="er", cloze=[
    ("This house is very {big}.", "Dieses Haus ist sehr groß."),
])
add_adjective("small", "klein", "6", degree="er")
add_adjective("good", "gut", "6", cloze=[
    ("The food was really {good}.", "Das Essen war wirklich gut."),
])
add_adjective("bad", "schlecht", "6")
add_adjective("happy", "glücklich", "6", degree="more")
add_adjective("sad", "traurig", "6", degree="more")
add_adjective("hot", "heiß", "6", degree="er")
add_adjective("cold", "kalt", "6", degree="er", cloze=[
    ("It's very {cold} today.", "Es ist heute sehr kalt."),
])
add_adjective("new", "neu", "6", degree="er")
add_adjective("old", "alt", "6", degree="er")
add_adjective("young", "jung", "6", degree="er")
add_adjective("beautiful", "schön", "6", degree="more")
add_adjective("ugly", "hässlich", "6", degree="more")
add_adjective("fast", "schnell", "6", degree="er")
add_adjective("slow", "langsam", "6", degree="more")
add_adjective("easy", "einfach", "6", degree="more")
add_adjective("difficult", "schwierig", "6", degree="more")
add_adjective("expensive", "teuer", "6", degree="more")
add_adjective("cheap", "billig", "6", degree="more")
add_adjective("long", "lang", "6", degree="er")
add_adjective("short", "kurz", "6", degree="er")
add_adjective("strong", "stark", "6", degree="er")
add_adjective("weak", "schwach", "6", degree="er")
add_adjective("clean", "sauber", "6", degree="more")
add_adjective("dirty", "schmutzig", "6", degree="more")
add_adjective("important", "wichtig", "6", degree="more")
add_adjective("interesting", "interessant", "6", degree="more")
add_adjective("boring", "langweilig", "6", degree="more")
add_adjective("many", "viele", "6")
add_adjective("little", "wenig", "6")
add_adjective("much", "viel", "6")
add_adjective("far", "weit", "6")

# === Lesson 7: Home & objects ==================================================
add_noun("house", "Haus", "7")
add_noun("room", "Zimmer", "7")
add_noun("kitchen", "Küche", "7")
add_noun("bathroom", "Badezimmer", "7")
add_noun("bedroom", "Schlafzimmer", "7")
add_noun("door", "Tür", "7")
add_noun("window", "Fenster", "7")
add_noun("table", "Tisch", "7")
add_noun("chair", "Stuhl", "7")
add_noun("bed", "Bett", "7")
add_noun("book", "Buch", "7", cloze=[
    ("I'm reading a good {book}.", "Ich lese ein gutes Buch."),
])
add_noun("phone", "Telefon", "7")
add_noun("computer", "Computer", "7")
add_noun("key", "Schlüssel", "7")
add_noun("bag", "Tasche", "7")
add_noun("money", "Geld", "7", uncountable=True)
add_noun("car", "Auto", "7")
add_noun("clock", "Uhr", "7")

# === Lesson 8: Time, days & weather ============================================
for w, de in [("Monday","Montag"),("Tuesday","Dienstag"),("Wednesday","Mittwoch"),
              ("Thursday","Donnerstag"),("Friday","Freitag"),("Saturday","Samstag"),
              ("Sunday","Sonntag")]:
    add_noun(w, de, "8")

add_noun("morning", "Morgen", "8")
add_noun("afternoon", "Nachmittag", "8")
add_noun("evening", "Abend", "8")
add_noun("night", "Nacht", "8")
add_noun("weather", "Wetter", "8", uncountable=True)
add_noun("sun", "Sonne", "8")
add_noun("rain", "Regen", "8", uncountable=True)
add_noun("snow", "Schnee", "8", uncountable=True)
add_noun("cloud", "Wolke", "8")
add_noun("wind", "Wind", "8")

# === Lesson 9: More common verbs (fills out the irregular-verb table) =======
add_verb("begin", "anfangen", "9")
add_verb("break", "brechen", "9", cloze=[
    ("Be careful, you'll {break} it.", "Pass auf, du machst es kaputt."),
])
add_verb("bring", "bringen", "9")
add_verb("build", "bauen", "9")
add_verb("catch", "fangen", "9")
add_verb("choose", "wählen", "9")
add_verb("cut", "schneiden", "9")
add_verb("draw", "zeichnen", "9")
add_verb("drive", "fahren", "9", cloze=[
    ("He {drives} to work every day.", "Er fährt jeden Tag zur Arbeit."),
])
add_verb("fall", "fallen", "9")
add_verb("feed", "füttern", "9")
add_verb("feel", "fühlen", "9", cloze=[
    ("I {feel} tired today.", "Ich fühle mich heute müde."),
])
add_verb("fight", "kämpfen", "9")
add_verb("find", "finden", "9", cloze=[
    ("I can't {find} my keys.", "Ich kann meine Schlüssel nicht finden."),
])
add_verb("fly", "fliegen", "9")
add_verb("forget", "vergessen", "9", cloze=[
    ("Please don't {forget} your bag.", "Vergiss bitte deine Tasche nicht."),
])
add_verb("get", "bekommen", "9")
add_verb("grow", "wachsen", "9")
add_verb("hear", "hören", "9")
add_verb("hold", "halten", "9")
add_verb("hurt", "wehtun", "9")
add_verb("keep", "behalten", "9")
add_verb("leave", "verlassen", "9", cloze=[
    ("The train {leaves} at nine.", "Der Zug fährt um neun ab."),
])
add_verb("lend", "leihen", "9")
add_verb("let", "lassen", "9")
add_verb("light", "anzünden", "9")
add_verb("lose", "verlieren", "9")
add_verb("meet", "treffen", "9", cloze=[
    ("Let's {meet} at the station.", "Lass uns am Bahnhof treffen."),
])
add_verb("pay", "bezahlen", "9")
add_verb("put", "legen", "9")
add_verb("ride", "reiten", "9")
add_verb("ring", "klingeln", "9")
add_verb("rise", "steigen", "9")
add_verb("say", "sagen", "9", cloze=[
    ("What did you {say}?", "Was hast du gesagt?"),
])
add_verb("sell", "verkaufen", "9")
add_verb("send", "schicken", "9")
add_verb("shine", "scheinen", "9")
add_verb("shoot", "schießen", "9")
add_verb("shut", "schließen", "9")
add_verb("sing", "singen", "9")
add_verb("sit", "sitzen", "9")
add_verb("spend", "ausgeben", "9")
add_verb("stand", "stehen", "9")
add_verb("steal", "stehlen", "9")
add_verb("swim", "schwimmen", "9")
add_verb("teach", "unterrichten", "9")
add_verb("tell", "erzählen", "9")
add_verb("throw", "werfen", "9")
add_verb("wake", "aufwachen", "9")
add_verb("wear", "tragen", "9", cloze=[
    ("She's {wearing} a red dress.", "Sie trägt ein rotes Kleid."),
])
add_verb("win", "gewinnen", "9")

# === Lesson 10: People, body & animals (fills out the irregular-plural table) ===
add_noun("man", "Mann", "10", irregular_plural=True)
add_noun("woman", "Frau", "10", irregular_plural=True)
add_noun("person", "Person", "10", irregular_plural=True, cloze=[
    ("She's a very kind {person}.", "Sie ist ein sehr netter Mensch."),
])
add_noun("foot", "Fuß", "10", irregular_plural=True)
add_noun("tooth", "Zahn", "10", irregular_plural=True)
add_noun("mouse", "Maus", "10", irregular_plural=True)
add_noun("goose", "Gans", "10", irregular_plural=True)
add_noun("sheep", "Schaf", "10", irregular_plural=True)


# === Cross-check: every override in the morph tables is actually used =======
used_verb_bases = [e["en"][3:] for e in entries if e["pos"] == "verb"]  # strip "to "
used_noun_bases = [e["en"] for e in entries if e["pos"] == "noun"]
used_adj_bases = [e["en"] for e in entries if e["pos"] == "adjective"]
M.check_unused(used_verb_bases, M.IRREGULAR_PAST_PARTICIPLE, "IRREGULAR_PAST_PARTICIPLE")
M.check_unused(used_verb_bases, M.IRREGULAR_PRESENT, "IRREGULAR_PRESENT")
M.check_unused(used_noun_bases, M.IRREGULAR_PLURAL, "IRREGULAR_PLURAL")
M.check_unused(used_adj_bases, M.IRREGULAR_COMPARISON, "IRREGULAR_COMPARISON")

# === Guard: no duplicate ids, no blank fields ===============================
ids = [e["id"] for e in entries]
assert len(ids) == len(set(ids)), "duplicate entry id"
for e in entries:
    assert e.get("en") and e.get("de"), f"blank en/de in {e}"

data = {"meta": {"language": "English", "reference": "German", "version": "v1"}, "entries": entries}
out_path = os.path.join(LT, "vocab_en.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"wrote {out_path}: {len(entries)} entries "
      f"({sum(1 for e in entries if e['pos']=='verb')} verbs, "
      f"{sum(1 for e in entries if e['pos']=='noun')} nouns, "
      f"{sum(1 for e in entries if e['pos']=='adjective')} adjectives, "
      f"{sum(1 for e in entries if e['pos'] not in ('verb','noun','adjective'))} other)")
