#!/usr/bin/env python3
"""Generate portuguese_trainer.html from spanish_trainer.html.

Same idea as make_medical_trainer.py: the app is GENERATED from an existing one
so engine fixes keep flowing to it. Edit this script, never the HTML.

Spanish is the right parent — the two languages share the drill shapes almost
exactly (four adjective forms, article+plural noun tables, one-level present
conjugation, two curated preposition/copula banks), so the diff is small enough
to be readable.

What changes:

  data field   `.es` becomes `.pt` throughout the engine. Only thirteen distinct
               contexts read it, so this is a mechanical rename rather than a
               rewrite.

  persons      Portuguese has no vós worth drilling: Portugal says vocês for
               plural you, exactly as Brazil does. The paradigm is five slots,
               not six.

  modes        Antonyms and synonyms are dropped (the deck links none yet), and
               three banks are added: personal infinitive, future subjunctive
               and false friends. All five banks share the ser_estar shape — a
               sentence with one braced answer and a `wrong` distractor — so the
               engine needs the mode names added and nothing else.

  variants     European Portuguese is primary. An entry with a `br` field shows
               both in the reveal panel and ACCEPTS both when typed: a learner
               who knows trem should not be marked wrong for a deck that says
               comboio.

    python3 scripts/make_portuguese_trainer.py
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LT = os.path.join(HERE, "..")
SRC = os.path.join(LT, "spanish_trainer.html")
# One generator, two apps. They differ in the deck, the person labels, the
# branding and which variety the reveal panel calls primary — nothing else, so
# an engine fix cannot land in one and miss the other.
VARIANTS = {
    "eu": dict(out="portuguese_trainer.html", deck="vocab_pt.json",
               slug="portuguese-trainer", title="European Portuguese",
               subtitle="português de Portugal / english",
               primary="Portugal", other="Brasil",
               # short_name is what fits under a home-screen icon, where
               # "European Portuguese Trainer" is truncated to nothing useful
               # and both apps would read the same
               short="Português PT", key="portuguese_trainer",
               persons={"eu": "eu", "tu": "tu", "ele_ela_voce": "ele / ela / você",
                        "nos": "nós", "eles_elas_voces": "eles / elas / vocês"}),
    "br": dict(out="brazilian_trainer.html", deck="vocab_br.json",
               slug="brazilian-trainer", title="Brazilian Portuguese",
               subtitle="português do Brasil / english",
               primary="Brasil", other="Portugal",
               short="Português BR", key="brazilian_trainer",
               # four slots: você takes the third-person form, so tu does not
               # get a column of its own
               persons={"eu": "eu", "voce_ele_ela": "você / ele / ela",
                        "nos": "nós", "voces_eles_elas": "vocês / eles / elas"}),
}

MODE_LABELS = [
    ("pt_en", "PT → EN"),
    ("en_pt", "EN → PT"),
    ("conjugate", "Conjugate"),
    ("decline", "Decline"),
    ("noun_case", "Noun forms"),
    ("multiple_choice", "Multiple choice"),
    ("cloze", "Cloze"),
    ("ser_estar", "Ser / estar / ficar"),
    ("por_para", "Por vs para"),
    ("personal_inf", "Personal infinitive"),
    ("fut_subj", "Future subjunctive"),
    ("false_friend", "False friends"),
]

LBL_OLD = ('promptLabel: mode === "ser_estar" ? "Ser vs estar — choose the form"'
           ' : "Por vs para — choose",')

BANKS = ["ser_estar", "por_para", "personal_inf", "fut_subj", "false_friend"]

ARTICLES_ES = '''  m_sg_nom: "masc. sg. (el ... )",
  f_sg: "fem. sg. (la ... )",
  m_pl: "masc. pl. (los ... )",
  f_pl: "fem. pl. (las ... )"'''
ARTICLES_PT = '''  m_sg_nom: "masc. sg. (o ... )",
  f_sg: "fem. sg. (a ... )",
  m_pl: "masc. pl. (os ... )",
  f_pl: "fem. pl. (as ... )"'''


def sub(src, old, new, count=1):
    assert src.count(old) == count, \
        f"anchor found {src.count(old)}x, expected {count}: {old[:70]!r}"
    return src.replace(old, new)


def build(cfg):
    src = open(SRC, encoding="utf-8").read()

    # Split the data blob out behind a placeholder so the .es -> .pt rename
    # cannot touch Spanish CONTENT — only the engine's field accesses.
    m = re.search(r"const VOCAB_DATA = \{.*?\};\n", src, re.S)
    assert m, "VOCAB_DATA blob not found"
    head, engine_tail = src[:m.start()], src[m.end():]

    # --- the .es -> .pt rename, engine only ---------------------------------
    def rename(s):
        s = re.sub(r'\.es\b', ".pt", s)
        s = s.replace('"es"', '"pt"').replace("'es'", "'pt'")
        s = s.replace('[plToDe ? "pt" : "en"]', '[plToDe ? "pt" : "en"]')
        return s

    head, engine_tail = rename(head), rename(engine_tail)

    # --- branding -----------------------------------------------------------
    pairs = [
        ("spanish_trainer_progress", cfg["key"] + "_progress"),
        ("spanish_trainer_lessons", cfg["key"] + "_lessons"),
        ("spanish_trainer_pos", cfg["key"] + "_pos"),
        ("spanish-trainer-sw.js", cfg["slug"] + "-sw.js"),
        ("spanish_trainer.html", cfg["out"]),
        ("spanish-trainer-manifest.json", cfg["slug"] + "-manifest.json"),
        ("spanish-trainer-icon-192.png", cfg["slug"] + "-icon-192.png"),
    ]
    for a, b in pairs:
        head = head.replace(a, b)
        engine_tail = engine_tail.replace(a, b)

    # Ordered longest-first: "Spanish / English trainer" must be replaced before
    # the bare "Spanish", or the first rule leaves the second nothing to match.
    # These run on head/engine_tail only — the deck sits behind a placeholder —
    # so replacing the bare word cannot touch entries like espanhol = "Spanish"
    # or the false-friend notes that mention Spanish on purpose.
    # Say WHICH Portuguese, everywhere it is named. The app shipped saying only
    # "português", which is how a Brazilian learner ended up asking whether it
    # was for them — it is not, and the label is the first place to say so.
    for a, b in [("Spanish / English trainer", cfg["title"] + " / English trainer"),
                 ('promptLabel: "Spanish"', 'promptLabel: "Portuguese"'),
                 ('answerLabel: "Spanish"', 'answerLabel: "Portuguese"'),
                 ("(Spanish)", "(Portuguese)"),
                 ("Spanish Trainer", "Portuguese Trainer"),
                 ("Spanish/English", "Portuguese/English"),
                 ("Vocabulario", "Vocabulário"),
                 ("español / english", cfg["subtitle"]),
                 ("Spanish trainer", "Portuguese trainer"),
                 ("Choose the Spanish", "Choose the Portuguese"),
                 ('answerLabel: plToDe ? "English" : "Portuguese"',
                  'answerLabel: plToDe ? "English" : "Portuguese"'),
                 # selectionCanAsk gates on enabledModes members as BARE keys,
                 # so the .es -> .pt field rename walked straight past them and
                 # left it testing es_en/en_pt, which do not exist here. The
                 # clause was therefore always false: with only the two
                 # translation drills selected both apps reported "0 words in
                 # selection" and an empty state, while generateQuestion kept
                 # producing questions. Same bug class as the enabledModes
                 # initialiser, in the one other place mode names appear unquoted.
                 ("enabledModes.es_en", "enabledModes.pt_en"),
                 ("enabledModes.en_es", "enabledModes.en_pt"),
                 ("// en_es: the Spanish word IS the answer).",
                  "// en_pt: the Portuguese word IS the answer)."),
                 ("// Accept the English of ANY entry with the same Spanish headword",
                  "// Accept the English of ANY entry with the same Portuguese headword"),
                 ("// Accept the Spanish of ANY entry sharing at least one English",
                  "// Accept the Portuguese of ANY entry sharing at least one English"),
                 # MODE_ELIGIBLE (round-coverage tracking) is the SAME bare-key
                 # trap as enabledModes above, in a table added after this
                 # generator's other bare-key fixes -- the .es -> .pt rename
                 # turns the VALUES (e.es -> e.pt) but not the KEYS, so without
                 # this a round with only translation drills enabled would
                 # never detect itself as exhausted (MODE_ELIGIBLE.pt_en would
                 # not exist) and never stop.
                 ("es_en: (e) => e.pt && e.en,", "pt_en: (e) => e.pt && e.en,"),
                 ("en_es: (e) => e.pt && e.en,", "en_pt: (e) => e.pt && e.en,")]:
        head = head.replace(a, b)
        engine_tail = engine_tail.replace(a, b)

    src = head + "const VOCAB_DATA = __DECK_PLACEHOLDER__;\n" + engine_tail

    # --- drills these apps do not offer --------------------------------------
    # The antonym and synonym drills were dropped (neither deck links any), but
    # selectionCanAsk kept gating on them. Harmless while the data is empty, and
    # exactly the stale bare-key reference check_portuguese.py now rejects, so
    # remove the clauses rather than allowlist them.
    for dead in ("  if (enabledModes.antonym && e.antonyms && e.antonyms.length > 0) return true;\n",
                 "  if (enabledModes.synonym && e.synonyms && e.synonyms.length > 0) return true;\n"):
        assert src.count(dead) == 1, "dead selectionCanAsk clause not found"
        src = src.replace(dead, "")

    # --- articles -----------------------------------------------------------
    # Found in a browser, not by a validator: the form labels still showed
    # Spanish articles, so the decline drill asked for `fem. pl. (las ... )` in
    # a Portuguese app. They are prose, not field names, which is why the
    # .es -> .pt rename walked straight past them.
    src = sub(src, ARTICLES_ES, ARTICLES_PT)
    src = sub(src, 'article: "definite article (el / la / los / las)",',
              'article: "definite article (o / a / os / as)",')

    # --- diacritics ---------------------------------------------------------
    # The shared map covers Polish, German and Spanish; Portuguese's own marks
    # were all missing. `coracao` for `coração` was therefore two edits away
    # rather than a diacritic near-miss, and graded plain wrong — on the two
    # accents the language uses most.
    src = sub(src, '"á":"a","é":"e","í":"i","ú":"u","ñ":"n"\n};',
              '"á":"a","é":"e","í":"i","ú":"u","ñ":"n",\n'
              '  "ã":"a","õ":"o","â":"a","ê":"e","ô":"o","ç":"c","à":"a"\n};')
    src = sub(src, "/[ąćęłńóśźżäöüßáéíúñ]/g", "/[ąćęłńóśźżäöüßáéíúñãõâêôçà]/g")

    # --- persons ------------------------------------------------------------
    old_pron = re.search(r"const PRONOUN_LABELS = \{.*?\};", src, re.S).group(0)
    new_pron = ("const PRONOUN_LABELS = {\n  " +
                ",\n  ".join(f'{k}: "{v}"' for k, v in cfg["persons"].items()) +
                "\n};")
    src = sub(src, old_pron, new_pron)

    # --- drill modes --------------------------------------------------------
    old_modes = re.search(r"const MODE_LABELS = \[.*?\];", src, re.S).group(0)
    new_modes = ("const MODE_LABELS = [\n" +
                 "".join(f'  ["{m}", "{lbl}"],\n' for m, lbl in MODE_LABELS) +
                 "];")
    src = sub(src, old_modes, new_modes)
    # enabledModes is a second, independent list of mode names written as BARE
    # object keys, so the quoted-string rename above does not touch it. Left
    # alone it enabled two modes the engine no longer has (es_en, en_es) and
    # never enabled the three new banks — five drill types silently dead.
    # Deriving it from MODE_LABELS is what stops the two lists drifting again.
    old_enabled = re.search(r"let enabledModes = \{.*?\};", src, re.S).group(0)
    new_enabled = ("let enabledModes = {\n  " +
                   ", ".join(f"{m}: true" for m, _ in MODE_LABELS) + "\n};")
    src = sub(src, old_enabled, new_enabled)

    src = src.replace('mode === "es_en"', 'mode === "pt_en"')
    src = src.replace('mode === "en_es"', 'mode === "en_pt"')
    src = src.replace('"es_en"', '"pt_en"').replace('"en_es"', '"en_pt"')
    src = src.replace('currentQ.type === "en_es"', 'currentQ.type === "en_pt"')

    # --- the three extra banks join the existing branch ---------------------
    src = sub(src, 'if (mode === "ser_estar" || mode === "por_para") {',
              'if (' + " || ".join(f'mode === "{b}"' for b in BANKS) + ") {")
    # SPECIAL_MODES is what round-coverage tracking (selectionExhausted, and
    # the bank's own per-item hard exclusion) iterates to know which enabled
    # modes draw from VOCAB_DATA.special rather than entries. Spanish only
    # has ser_estar/por_para; extend it to all five banks here, or a round
    # with only personal_inf enabled would never detect itself as exhausted.
    src = sub(src, 'const SPECIAL_MODES = ["ser_estar", "por_para"];',
              "const SPECIAL_MODES = [" + ", ".join(f'"{b}"' for b in BANKS) + "];")
    src = sub(src, '''  if (type === "ser_estar") return !!enabledPos.verb;
  if (type === "por_para") return !!enabledPos.preposition;''',
              '''  if (type === "ser_estar") return !!enabledPos.verb;
  if (type === "por_para") return !!enabledPos.preposition;
  // The personal infinitive and future subjunctive are verb drills; false
  // friends are mostly nouns and adjectives, so it rides on either being on.
  if (type === "personal_inf" || type === "fut_subj") return !!enabledPos.verb;
  if (type === "false_friend") return !!(enabledPos.noun || enabledPos.adjective);''')

    # The bank label was hardcoded to the two Spanish banks, so a personal
    # infinitive card announced itself as "Por vs para". Derive it from
    # MODE_LABELS instead, which is the list that already names them.
    src = sub(src, LBL_OLD, 'promptLabel: BANK_LABELS[mode] + " — choose",')
    src = sub(src, "let enabledModes = {",
              f'const VARIANT_PRIMARY = {cfg["primary"]!r};\n'
              f'const VARIANT_OTHER = {cfg["other"]!r};\n' +
              "const BANK_LABELS = " + json.dumps(
                  {m: lbl for m, lbl in MODE_LABELS if m in BANKS}, ensure_ascii=False) +
              ";\nlet enabledModes = {")

    # every bank now supplies its own distractor, so the por_para special case
    # (deriving "the other preposition") only applies when `wrong` is absent
    src = sub(src, '''    let other;
    if (mode === "por_para") {''',
              '''    let other;
    if (item.wrong) {
      other = item.wrong;
    } else if (mode === "por_para") {''')

    # --- Brazilian variants: shown on reveal, and accepted when typed -------
    src = sub(src, "function buildConjSection() {", BR_HELPERS + "\nfunction buildConjSection() {")

    # The variant row sits beside the conjugation table, in all three places the
    # card renders one — text answers, multiple choice, and the feedback redraw.
    src = src.replace("""  const conj = buildConjSection();
  if (conj) card.appendChild(conj);""",
                      """  const variant = buildVariantSection();
  if (variant) card.appendChild(variant);
  const conj = buildConjSection();
  if (conj) card.appendChild(conj);""")
    src = src.replace("""      const conj = buildConjSection();
      if (conj) card.appendChild(conj);""",
                      """      const variant = buildVariantSection();
      if (variant) card.appendChild(variant);
      const conj = buildConjSection();
      if (conj) card.appendChild(conj);""")
    src = sub(src, """  const conjSection = buildConjSection();
  if (conjSection) card.appendChild(conjSection);""",
              """  const variantSection = buildVariantSection();
  if (variantSection) card.appendChild(variantSection);
  const conjSection = buildConjSection();
  if (conjSection) card.appendChild(conjSection);""")

    # Accept the Brazilian form wherever the European one is the target. A
    # learner who knows `trem` is not wrong just because the deck says comboio.
    src = sub(src, """function checkAnswer(q, input) {
  if (q.acceptableAnswers) {""",
              """function checkAnswer(q, input) {
  // European Portuguese is the deck's primary, but the Brazilian form of the
  // same word is a correct answer, not a near miss.
  const br = brVariant(q.entryId);
  if (br && q.answerLabel !== "English") {
    const g = gradeAnswer(input, br);
    if (g === "exact") return g;
  }
  if (q.acceptableAnswers) {""")

    # styling for the variant row
    src = sub(src, "  .conj-section {", VARIANT_CSS + "  .conj-section {")

    return src


VARIANT_CSS = """  .variant-row { display: flex; gap: 14px; flex-wrap: wrap; margin-top: 10px;
    font-size: 13px; color: var(--muted); }
  .variant-br { font-style: italic; }
"""

BR_HELPERS = '''
// --- European / Brazilian variants ----------------------------------------
// The deck is European Portuguese. Where Brazil says something else the entry
// carries `br`, and a learner who knows that form must not be marked wrong —
// so it is accepted as an answer and shown in the reveal panel beside the
// primary form rather than instead of it.
function brVariant(entryId) {
  const e = byId[entryId];
  return (e && e.alt) ? e.alt : null;
}

function buildVariantSection() {
  if (!currentQ || !feedback) return null;
  const br = brVariant(currentQ.entryId);
  if (!br) return null;
  const e = byId[currentQ.entryId];
  const wrap = document.createElement("div");
  wrap.className = "variant-row";
  const pt = document.createElement("span");
  pt.className = "variant-pt";
  pt.textContent = VARIANT_PRIMARY + ": " + e.pt;
  const b = document.createElement("span");
  b.className = "variant-br";
  b.textContent = VARIANT_OTHER + ": " + br;
  wrap.appendChild(pt);
  wrap.appendChild(b);
  return wrap;
}
'''


def write_pwa(cfg):
    """The service worker and manifest are generated too.

    They were hand-copied for every earlier trainer, which is why a stale cache
    name or a start_url still pointing at the parent app is the classic way one
    of these ships broken. Deriving them from Spanish makes that impossible: the
    only thing that differs is the slug and the display name.
    """
    for name, sw in [(cfg["slug"] + "-sw.js", True),
                     (cfg["slug"] + "-manifest.json", False)]:
        src_name = "spanish-trainer-sw.js" if sw else "spanish-trainer-manifest.json"
        text = open(os.path.join(LT, src_name), encoding="utf-8").read()
        text = (text.replace("spanish-trainer", cfg["slug"])
                    .replace("spanish_trainer.html", cfg["out"])
                    .replace("Vocabulario — Spanish/English Trainer",
                             "Vocabulário — " + cfg["title"] + "/English Trainer")
                    .replace("Spanish Trainer", cfg["short"]))
        assert "spanish" not in text.lower(), f"{name} still mentions Spanish"
        open(os.path.join(LT, name), "w", encoding="utf-8").write(text)


def splice_deck(src, cfg):
    deck = json.load(open(os.path.join(LT, cfg["deck"]), encoding="utf-8"))
    blob = json.dumps(deck, ensure_ascii=False, separators=(",", ":"))
    assert src.count("__DECK_PLACEHOLDER__") == 1, "placeholder missing"
    src = src.replace("__DECK_PLACEHOLDER__", blob)
    open(os.path.join(LT, cfg["out"]), "w", encoding="utf-8").write(src)
    return deck


def main():
    for cfg in VARIANTS.values():
        deck = splice_deck(build(cfg), cfg)
        write_pwa(cfg)
        print(f"{cfg['out']:26} {len(deck['entries'])} entries, "
              f"{len(MODE_LABELS)} drill types, "
              f"{len(deck['special'])} special banks, "
              f"{len(cfg['persons'])} persons")


if __name__ == "__main__":
    main()
