#!/usr/bin/env python3
"""Behavioural checks for BOTH Portuguese trainers.

Each deck marks the other variety's form, and the claim that matters is that
BOTH grade correct — a learner who says `trem` must not be marked wrong by a
deck that says `comboio`, nor the reverse. That is a runtime property of
checkAnswer, not of the data, so it is tested by running each app's own code.

Running the same probe over both apps is the point: they come out of one
generator, so a check that only ever saw the European one would pass while the
Brazilian app was dead. The person paradigms differ (five slots against four),
so `persons` is asserted per app rather than shared.

Also checks that each of the five special banks really produces questions with
two distinct options, since they all share one code path and a mistake there
would silently collapse a bank into a giveaway.

    python3 scripts/check_portuguese.py
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LT = os.path.join(HERE, "..")
# app file -> how many persons its conjugation table must have. Brazil folds
# tu into você, so four; Portugal keeps tu, so five.
APPS = {"portuguese_trainer.html": 5, "brazilian_trainer.html": 4}

PROBE = r"""
const out = { brPairs: 0, brAccepted: 0, brMissed: [], banks: {}, bankBad: [] };

// --- 1. every marked Brazilian form must grade exact against its entry ------
// The field is `alt` — the OTHER variety's form, whichever deck this is. It
// was `br` before one generator started producing both decks, and the rename
// left this probe reading a field that no longer exists: 0 pairs found, and
// "0/0 accepted" reported as a pass. Hence the brPairs === 0 failure below.
VOCAB_DATA.entries.forEach(function(e) {
  if (!e.alt) return;
  out.brPairs++;
  const q = { entryId: e.id, target: e.pt, answerLabel: "Portuguese" };
  const own = checkAnswer(q, e.pt);
  const other = checkAnswer(q, e.alt);
  if (own === "exact" && other === "exact") out.brAccepted++;
  else out.brMissed.push(e.pt + "/" + e.alt + " -> own:" + own + " other:" + other);
});

// --- 2. each bank generates a real two-way choice --------------------------
Object.keys(enabledModes).forEach(function(m) { enabledModes[m] = true; });
["ser_estar", "por_para", "personal_inf", "fut_subj", "false_friend"].forEach(function(bank) {
  const seen = {};
  let made = 0;
  for (let i = 0; i < 200; i++) {
    const q = generateQuestion(bank);
    if (!q) continue;
    made++;
    seen[q.entryId || q.rawTarget] = true;
    const opts = (q.choices || []).map(function(c) { return c.text; });
    if (opts.length < 2) out.bankBad.push(bank + ": only " + opts.length + " option(s)");
    else if (opts[0] === opts[1]) out.bankBad.push(bank + ": both options are " + opts[0]);
    if (q.correct && opts.indexOf(q.correct) === -1)
      out.bankBad.push(bank + ": correct answer is not among the options");
  }
  out.banks[bank] = { made: made, distinct: Object.keys(seen).length };
});

// --- 3. no dead drill types -----------------------------------------------
// enabledModes is a SECOND list of mode names, written as bare object keys, so
// a rename that only touches quoted strings leaves it stale. That silently
// enabled two modes the engine no longer had and never enabled three new
// banks — five of twelve drill types dead, and every one of them still shown
// as a pill you could turn on.
out.dead = [];
out.unknown = [];
const declared = MODE_LABELS.map(function(m) { return m[0]; });
declared.forEach(function(m) { if (!(m in enabledModes)) out.unknown.push(m); });
Object.keys(enabledModes).forEach(function(m) {
  if (declared.indexOf(m) === -1) { out.unknown.push(m); return; }
  let made = 0;
  for (let i = 0; i < 60; i++) if (generateQuestion(m)) made++;
  if (made === 0) out.dead.push(m);
});

// --- 4. the paradigm has the right number of persons -----------------------
// The Brazilian app re-slots the conjugation to four persons. If PRONOUN_LABELS
// and the deck's forms ever disagree the drill renders blank cells, which no
// other check here would notice.
out.persons = Object.keys(PRONOUN_LABELS);
out.personMismatch = [];
VOCAB_DATA.entries.forEach(function(e) {
  if (!e.conjugation) return;
  out.persons.forEach(function(p) {
    if (!e.conjugation[p]) out.personMismatch.push(e.pt + " has no " + p);
  });
  Object.keys(e.conjugation).forEach(function(p) {
    if (out.persons.indexOf(p) === -1)
      out.personMismatch.push(e.pt + " has " + p + ", which no label names");
  });
});

// --- 5. Portuguese accents are near-misses, not wrong answers --------------
// The diacritic map is shared with Polish, German and Spanish and had none of
// Portuguese's own marks, so `coracao` was two edits from `coração` and graded
// plain wrong. These are the accents the language uses most, and this is the
// mistake every learner makes on a phone keyboard.
out.diacritic = [];
// Only accent differences belong here: `accao` for `ação` is the pre-1990
// spelling, a different letter, and grades "typo" — which is right.
[["coracao", "coração"], ["irma", "irmã"], ["voce", "você"], ["pao", "pão"],
 ["mes", "mês"], ["avo", "avô"], ["licao", "lição"]].forEach(function(pair) {
  const g = gradeAnswer(pair[0], pair[1]);
  if (g !== "diacritic") out.diacritic.push(pair[0] + " vs " + pair[1] + " -> " + g);
});

// A label naming a Spanish article means the app is still half its parent.
out.spanishLabels = [];
[DECL_LABELS, NOUN_LABELS, PRONOUN_LABELS].forEach(function(set) {
  Object.keys(set).forEach(function(k) {
    if (/\b(el|la|los|las)\b/.test(set[k])) out.spanishLabels.push(k + ": " + set[k]);
  });
});

// --- 6. the personal infinitive and future subjunctive must not coincide ----
// where the deck says they differ, or the drill has no answer to distinguish.
(VOCAB_DATA.special.fut_subj || []).forEach(function(it) {
  if (it.wrong === it.pt.match(/\{([^}]*)\}/)[1] && ["falar","chegar"].indexOf(it.verb) === -1)
    out.bankBad.push("fut_subj " + it.id + ": distractor equals the answer");
});

console.log(JSON.stringify(out));
"""


def run(app, want_persons):
    src = open(os.path.join(LT, app), encoding="utf-8").read()
    js = src.split("<script>", 1)[1].rsplit("</script>", 1)[0]
    stub = open(os.path.join(HERE, "dom_stub.js"), encoding="utf-8").read()
    d = tempfile.mkdtemp()
    p = os.path.join(d, "p.js")
    open(p, "w", encoding="utf-8").write(stub + js + PROBE)
    r = subprocess.run(["node", p], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2000:])
        sys.exit(1)
    res = json.loads(r.stdout)

    fails = []
    if len(res["persons"]) != want_persons:
        fails.append(f"{len(res['persons'])} persons in PRONOUN_LABELS, expected {want_persons}")
    fails += res["personMismatch"][:4]
    fails += [f"accent-only miss graded {d}" for d in res["diacritic"]]
    fails += [f"label still names a Spanish article — {s}" for s in res["spanishLabels"]]
    if res["brPairs"] == 0:
        fails.append("no Brazilian variants in the deck at all")
    if res["brAccepted"] != res["brPairs"]:
        fails.append(f"{res['brPairs'] - res['brAccepted']} variant pairs not both accepted")
    for bank, info in res["banks"].items():
        if info["made"] == 0:
            fails.append(f"{bank}: produced no questions")
    fails += res["bankBad"][:6]
    for m in res.get("dead", []):
        fails.append(f"drill type {m!r} is offered but generates nothing")
    for m in res.get("unknown", []):
        fails.append(f"{m!r} is in one mode list but not the other")

    print(f"drill types: {12 - len(res.get('dead', []))}/12 generate questions, "
          f"{len(res['persons'])} persons")
    print(f"variants: {res['brAccepted']}/{res['brPairs']} pairs accept both forms")
    for bank, info in res["banks"].items():
        print(f"  {bank:14} {info['made']:3} questions, {info['distinct']:2} distinct items")
    for m in res["brMissed"][:8]:
        print(f"  MISS {m}")
    for f in fails:
        print(f"  FAIL {f}")
    return fails


def main():
    bad = False
    for app, persons in APPS.items():
        print(f"=== {app} ===")
        bad |= bool(run(app, persons))
        print()
    if bad:
        sys.exit(1)
    print("all Portuguese checks pass, both variants")


if __name__ == "__main__":
    main()
