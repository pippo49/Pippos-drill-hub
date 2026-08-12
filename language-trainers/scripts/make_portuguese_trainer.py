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
OUT = os.path.join(LT, "portuguese_trainer.html")
DECK = os.path.join(LT, "vocab_pt.json")

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

PRONOUN_LABELS = {
    "eu": "eu", "tu": "tu", "ele_ela_voce": "ele / ela / você",
    "nos": "nós", "eles_elas_voces": "eles / elas / vocês",
}

LBL_OLD = ('promptLabel: mode === "ser_estar" ? "Ser vs estar — choose the form"'
           ' : "Por vs para — choose",')

BANKS = ["ser_estar", "por_para", "personal_inf", "fut_subj", "false_friend"]


def sub(src, old, new, count=1):
    assert src.count(old) == count, \
        f"anchor found {src.count(old)}x, expected {count}: {old[:70]!r}"
    return src.replace(old, new)


def build():
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
        ("spanish_trainer_progress", "portuguese_trainer_progress"),
        ("spanish_trainer_lessons", "portuguese_trainer_lessons"),
        ("spanish_trainer_pos", "portuguese_trainer_pos"),
        ("spanish-trainer-sw.js", "portuguese-trainer-sw.js"),
        ("spanish_trainer.html", "portuguese_trainer.html"),
        ("spanish-trainer-manifest.json", "portuguese-trainer-manifest.json"),
        ("spanish-trainer-icon-192.png", "portuguese-trainer-icon-192.png"),
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
    for a, b in [("Spanish / English trainer", "European Portuguese / English trainer"),
                 ('promptLabel: "Spanish"', 'promptLabel: "Portuguese"'),
                 ('answerLabel: "Spanish"', 'answerLabel: "Portuguese"'),
                 ("(Spanish)", "(Portuguese)"),
                 ("Spanish Trainer", "Portuguese Trainer"),
                 ("Spanish/English", "Portuguese/English"),
                 ("Vocabulario", "Vocabulário"),
                 ("español / english", "português de Portugal / english"),
                 ("Spanish trainer", "Portuguese trainer"),
                 ("Choose the Spanish", "Choose the Portuguese"),
                 ('answerLabel: plToDe ? "English" : "Spanish"',
                  'answerLabel: plToDe ? "English" : "Portuguese"')]:
        head = head.replace(a, b)
        engine_tail = engine_tail.replace(a, b)

    src = head + "const VOCAB_DATA = __DECK_PLACEHOLDER__;\n" + engine_tail

    # --- persons ------------------------------------------------------------
    old_pron = re.search(r"const PRONOUN_LABELS = \{.*?\};", src, re.S).group(0)
    new_pron = ("const PRONOUN_LABELS = {\n  " +
                ",\n  ".join(f'{k}: "{v}"' for k, v in PRONOUN_LABELS.items()) +
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

    open(OUT, "w", encoding="utf-8").write(src)
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
  return (e && e.br) ? e.br : null;
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
  pt.textContent = "Portugal: " + e.pt;
  const b = document.createElement("span");
  b.className = "variant-br";
  b.textContent = "Brasil: " + br;
  wrap.appendChild(pt);
  wrap.appendChild(b);
  return wrap;
}
'''


def splice_deck(src):
    deck = json.load(open(DECK, encoding="utf-8"))
    blob = json.dumps(deck, ensure_ascii=False, separators=(",", ":"))
    assert src.count("__DECK_PLACEHOLDER__") == 1, "placeholder missing"
    src = src.replace("__DECK_PLACEHOLDER__", blob)
    open(OUT, "w", encoding="utf-8").write(src)
    return deck


def main():
    src = build()
    deck = splice_deck(open(OUT, encoding="utf-8").read())
    print(f"portuguese_trainer.html  {len(deck['entries'])} entries, "
          f"{len(MODE_LABELS)} drill types, {len(deck['special'])} special banks")


if __name__ == "__main__":
    main()
