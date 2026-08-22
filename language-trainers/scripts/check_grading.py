#!/usr/bin/env python3
"""Regression test for the answer-acceptance rules (see patch_grading.py).

Covers the French app (English contractions, question forms, agreement) and the
Polish one, whose reference language is German and which therefore has no
contraction handling but the same phrase/filler/agreement rules.

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

# --- Polish (reference language German, so no contractions) ---------------
# (input, target, expected grade) -- graded through the app's gradeAnswer.
POLISH_PAIRS = [
    # A comma inside a phrase is not an alternative separator: the intact target
    # must be offered alongside the split parts, or a full answer can never match.
    ("es kann sein, vielleicht", "es kann sein, vielleicht", "exact"),
    ("auf polnische Art, auf Polnisch", "auf polnische Art, auf Polnisch", "exact"),
    # ...while a real comma-separated alternatives list still accepts each part
    ("sprechen", "sprechen, reden", "exact"),
    ("reden", "sprechen, reden", "exact"),
    # Reflexive particles stay interchangeable
    ("sich entschuldigen", "entschuldigen", "exact"),
    ("entschuldigen", "sich entschuldigen", "exact"),
    # ...but stripping them must never empty an answer: "się" is itself a
    # headword (pd0773, "man"), and an emptied target graded German "sich" exact.
    ("się", "się", "exact"),
    ("sich", "się", "wrong"),
    # guards: genuinely wrong answers stay wrong
    ("dobry", "zły", "wrong"),
    ("dzień dobry", "dobranoc", "wrong"),
]

# DE->PL: a German prompt carries no gender or number, so every agreeing
# nominative form answers it, and a curated synonym is interchangeable.
# Safe for Polish because `declension` holds nominative forms only (unlike Latin).
POLISH_HEADWORDS = ["duży", "mały", "dobry", "iść"]

# ...but NOT an aspect partner. Polish mirrors every aspect_pair link into
# `synonyms`, so the widening above would silently accept a perfective for an
# imperfective prompt. The deck drills that distinction on purpose — the
# Synonyms drill asks for the partner explicitly and tags it (pf.)/(impf.) —
# so a bare German infinitive must not take either.
#
# This only reaches pairs the deck glosses DIFFERENTLY (mówić "sprechen, reden"
# vs powiedzieć "sagen") — 6 of the 24 pairs. For the other 18 both verbs carry
# the same German word, and the older cross-entry rule accepts any entry sharing
# a gloss; refusing one there would mark a correct answer wrong, since the
# prompt genuinely translates to both. That rule is not what changed here.
POLISH_ASPECT_PAIRS = ["mówić", "płacić", "słuchać"]


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

    script = """
const PAIRS = %s;
const out = PAIRS.map(function(p){ return [p[0], p[1], p[2], gradeAnswer(p[0], p[1])]; });
console.log(JSON.stringify(out));
""" % json.dumps(POLISH_PAIRS)
    print("\nPolish gradeAnswer")
    for inp, target, want, got in json.loads(run("polish_trainer.html", script)):
        ok = got == want
        if not ok:
            fails += 1
        print(f"  {'ok ' if ok else 'FAIL'} {inp:34} vs {target:24} -> {got} (want {want})")

    script = """
const HEADS = %s;
const res = [];
HEADS.forEach(function(h) {
  const e = VOCAB_DATA.entries.filter(function(x){ return x.pl === h; })[0];
  if (!e) { res.push([h, null, []]); return; }
  let q = null;
  for (let i = 0; i < 40000 && !q; i++) {
    const c = generateQuestion("de_pl");
    if (c && c.entryId === e.id) q = c;
  }
  if (!q) { res.push([h, null, []]); return; }
  let forms = [];
  if (e.declension) forms = Object.keys(e.declension).map(function(k){ return e.declension[k]; });
  (e.synonyms || []).forEach(function(id) { if (byId[id]) forms.push(byId[id].pl); });
  res.push([h, q.prompt, forms.map(function(f){ return [f, checkAnswer(q, f)]; })]);
});
console.log(JSON.stringify(res));
""" % json.dumps(POLISH_HEADWORDS)
    print("\nDE->PL agreement and curated synonyms")
    for head, prompt, forms in json.loads(run("polish_trainer.html", script)):
        if prompt is None:
            print(f"  FAIL no question found for {head!r}")
            fails += 1
            continue
        print(f"  {head} — prompt {prompt!r}")
        for f, grade in forms:
            ok = grade == "exact"
            if not ok:
                fails += 1
            print(f"    {'ok ' if ok else 'FAIL'} {f:20} -> {grade}")

    script = """
const HEADS = %s;
const res = [];
HEADS.forEach(function(h) {
  const e = VOCAB_DATA.entries.filter(function(x){ return x.pl === h; })[0];
  if (!e || !e.aspect_pair || !byId[e.aspect_pair]) { res.push([h, null, null, null]); return; }
  let q = null;
  for (let i = 0; i < 40000 && !q; i++) {
    const c = generateQuestion("de_pl");
    if (c && c.entryId === e.id) q = c;
  }
  if (!q) { res.push([h, null, null, null]); return; }
  const partner = byId[e.aspect_pair].pl;
  res.push([h, q.prompt, partner, checkAnswer(q, partner)]);
});
console.log(JSON.stringify(res));
""" % json.dumps(POLISH_ASPECT_PAIRS)
    print("\nDE->PL does NOT accept an aspect partner")
    for head, prompt, partner, grade in json.loads(run("polish_trainer.html", script)):
        if prompt is None:
            print(f"  FAIL no aspect-paired question found for {head!r}")
            fails += 1
            continue
        ok = grade != "exact"
        if not ok:
            fails += 1
        print(f"    {'ok ' if ok else 'FAIL'} {head} — prompt {prompt!r}: {partner} -> {grade}")

    print("\nFAILURES:" if fails else "\nall grading checks pass", fails or "")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
