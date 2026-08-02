#!/usr/bin/env python3
"""Regression test for the answer-acceptance fixes (see patch_grading.py).

Runs the trainer's own grading functions under node against the exact cases that
were reported as wrongly marked, plus guard cases that must STILL be rejected so
the fixes cannot quietly turn into "accept anything".

    python3 scripts/check_grading.py          # exits 1 on any failure
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LT = os.path.join(HERE, "..")

# (input, target, expected grade) -- graded through the app's gradeAnswer.
FRENCH_PAIRS = [
    # 1. English contractions, both directions
    ("it is", "it's", "exact"),
    ("what is your name?", "what's your name?", "exact"),
    ("I am fine, thanks", "I'm fine, thanks", "exact"),
    ("you are welcome", "you're welcome", "exact"),
    ("it's", "it is", "exact"),
    ("it does not matter", "it doesn't matter", "exact"),
    ("I cannot", "I can't", "exact"),
    ("we will not", "we won't", "exact"),
    # guards: French elision must survive contraction expansion untouched
    ("j'ai faim", "j'ai faim", "exact"),
    ("qu'est-ce que c'est ?", "qu'est-ce que c'est ?", "exact"),
    ("l'hôtel", "l'hôtel", "exact"),
    # guards: genuinely wrong answers stay wrong
    ("tu veux partir ?", "est-ce que tu veux venir ?", "wrong"),
    ("comment il s'appelle ?", "comment t'appelles-tu ?", "wrong"),
    ("bonjour", "bonsoir", "wrong"),
]

# EN->FR questions: (english prompt substring, answers that must be accepted)
FRENCH_ACCEPTS = [
    ("what's your name?", ["comment tu t'appelles ?", "comment vous appelez-vous ?",
                           "comment t'appelles-tu ?", "comment est-ce que tu t'appelles ?"]),
    ("how are you?", ["comment vas-tu ?", "comment allez-vous ?", "comment vous allez ?"]),
    ("you (informal sg.)", ["tu", "vous", "toi"]),
    # the reported case: deck stores the informal, learner writes the formal
    ("can you repeat?", ["pouvez-vous répéter ?", "vous pouvez répéter ?",
                         "est-ce que vous pouvez répéter ?"]),
    ("where are you from?", ["d'où venez-vous ?", "d'où vous venez ?"]),
    ("what does that mean?", ["qu'est-ce que ça veut dire ?", "ça veut dire quoi ?"]),
]

# EN->FR adjective: every agreeing form answers a prompt with no gender/number.
ADJECTIVE_HEADWORDS = ["grand", "petit", "bon", "heureux"]


def run(html, script):
    src = open(os.path.join(LT, html), encoding="utf-8").read()
    js = src.split("<script>", 1)[1].rsplit("</script>", 1)[0]
    stub = open(os.path.join(HERE, "dom_stub.js"), encoding="utf-8").read()
    d = tempfile.mkdtemp()
    p = os.path.join(d, "p.js")
    open(p, "w", encoding="utf-8").write(stub + js + script)
    r = subprocess.run(["node", p], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr)
        sys.exit(1)
    return r.stdout


def main():
    fails = 0

    script = """
const PAIRS = %s;
const out = PAIRS.map(function(p){ return [p[0], p[1], p[2], gradeAnswer(p[0], p[1])]; });
console.log(JSON.stringify(out));
""" % json.dumps(FRENCH_PAIRS)
    rows = json.loads(run("french_trainer.html", script))
    print("grading pairs")
    for inp, tgt, want, got in rows:
        ok = (got == want) if want != "wrong" else (got == "wrong")
        if not ok:
            fails += 1
        print(f"  {'ok ' if ok else 'FAIL'} {inp[:34]:36} vs {tgt[:34]:36} -> {got} (want {want})")

    script = """
const WANT = %s;
const res = [];
WANT.forEach(function(w) {
  let q = null;
  for (let i = 0; i < 20000 && !q; i++) {
    const c = generateQuestion("en_fr");
    if (c && c.prompt.toLowerCase().indexOf(w[0].toLowerCase()) >= 0) q = c;
  }
  if (!q) { res.push([w[0], null, []]); return; }
  res.push([w[0], q.target, w[1].map(function(a){ return [a, checkAnswer(q, a)]; })]);
});
console.log(JSON.stringify(res));
""" % json.dumps(FRENCH_ACCEPTS)
    print("\nEN->FR accepted answers")
    for prompt, target, tried in json.loads(run("french_trainer.html", script)):
        if target is None:
            print(f"  FAIL no question found for {prompt!r}")
            fails += 1
            continue
        print(f"  prompt {prompt!r} (stored answer {target!r})")
        for ans, grade in tried:
            ok = grade == "exact"
            if not ok:
                fails += 1
            print(f"    {'ok ' if ok else 'FAIL'} {ans:38} -> {grade}")

    script = """
const HEADS = %s;
const res = [];
HEADS.forEach(function(h) {
  const e = VOCAB_DATA.entries.filter(function(x){ return x.fr === h && x.declension; })[0];
  if (!e) { res.push([h, null, []]); return; }
  let q = null;
  for (let i = 0; i < 20000 && !q; i++) {
    const c = generateQuestion("en_fr");
    if (c && c.entryId === e.id) q = c;
  }
  if (!q) { res.push([h, null, []]); return; }
  const forms = Object.keys(e.declension).map(function(k){ return e.declension[k]; });
  res.push([h, q.prompt, forms.map(function(f){ return [f, checkAnswer(q, f)]; })]);
});
console.log(JSON.stringify(res));
""" % json.dumps(ADJECTIVE_HEADWORDS)
    print("\nEN->FR adjective agreement")
    for head, prompt, forms in json.loads(run("french_trainer.html", script)):
        if prompt is None:
            print(f"  (skipped {head}: not in deck)")
            continue
        print(f"  {head} — prompt {prompt!r}")
        for f, grade in forms:
            ok = grade == "exact"
            if not ok:
                fails += 1
            print(f"    {'ok ' if ok else 'FAIL'} {f:20} -> {grade}")

    print("\nFAILURES:" if fails else "\nall grading checks pass", fails or "")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
