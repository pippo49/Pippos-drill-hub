#!/usr/bin/env python3
"""Behavioural checks for the Portuguese trainer.

The deck is European Portuguese with Brazilian forms marked. The claim that
matters is that BOTH grade correct — a learner who says `trem` must not be
marked wrong by a deck that says `comboio`. That is a runtime property of
checkAnswer, not of the data, so it is tested by running the app's own code.

Also checks that each of the five special banks really produces questions with
two distinct options, since they all share one code path and a mistake there
would silently collapse a bank into a giveaway.

    python3 scripts/check_portuguese.py
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LT = os.path.join(HERE, "..")
APP = os.path.join(LT, "portuguese_trainer.html")

PROBE = r"""
const out = { brPairs: 0, brAccepted: 0, brMissed: [], banks: {}, bankBad: [] };

// --- 1. every marked Brazilian form must grade exact against its entry ------
VOCAB_DATA.entries.forEach(function(e) {
  if (!e.br) return;
  out.brPairs++;
  const q = { entryId: e.id, target: e.pt, answerLabel: "Portuguese" };
  const european = checkAnswer(q, e.pt);
  const brazilian = checkAnswer(q, e.br);
  if (european === "exact" && brazilian === "exact") out.brAccepted++;
  else out.brMissed.push(e.pt + "/" + e.br + " -> pt:" + european + " br:" + brazilian);
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

// --- 4. the personal infinitive and future subjunctive must not coincide ----
// where the deck says they differ, or the drill has no answer to distinguish.
(VOCAB_DATA.special.fut_subj || []).forEach(function(it) {
  if (it.wrong === it.pt.match(/\{([^}]*)\}/)[1] && ["falar","chegar"].indexOf(it.verb) === -1)
    out.bankBad.push("fut_subj " + it.id + ": distractor equals the answer");
});

console.log(JSON.stringify(out));
"""


def main():
    src = open(APP, encoding="utf-8").read()
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

    print(f"drill types: {len(res['banks']) and ''}"
          f"{12 - len(res.get('dead', []))}/12 generate questions")
    print(f"Brazilian variants: {res['brAccepted']}/{res['brPairs']} pairs accept both forms")
    for bank, info in res["banks"].items():
        print(f"  {bank:14} {info['made']:3} questions, {info['distinct']:2} distinct items")
    for m in res["brMissed"][:8]:
        print(f"  MISS {m}")
    if fails:
        for f in fails:
            print(f"  FAIL {f}")
        sys.exit(1)
    print("\nall Portuguese checks pass")


if __name__ == "__main__":
    main()
