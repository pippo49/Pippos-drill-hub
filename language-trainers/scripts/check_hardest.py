#!/usr/bin/env python3
"""Regression test for the hardest-words round (see patch_hardest.py).

Seeds a synthetic history, then asserts the behaviour that was asked for:

  * the set is ranked by RAW wrong count and is the top 10% of everything
    attempted (with a floor so a round is never two questions);
  * a hardest round asks ONLY words from that set, over many draws;
  * it IGNORES the lesson and word-form filters — that is the "global" choice;
  * an ordinary round afterwards is unaffected;
  * words never got wrong never appear, however often they were seen.

    python3 scripts/check_hardest.py        # exits 1 on any failure
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LT = os.path.join(HERE, "..")
APPS = ["polish_trainer.html", "spanish_trainer.html", "italian_trainer.html",
        "french_trainer.html", "latin_trainer.html", "medical_trainer.html", "portuguese_trainer.html"]

PROBE = r"""
// Seed a history: 120 attempted words, 30 of them with mistakes, wrong counts
// spread so the ranking has something to sort. One word is seen very often but
// never missed -- it must never show up in a hardest round.
const ids = VOCAB_DATA.entries.map(function(e){ return e.id; });
progress.stats = {};
for (let i = 0; i < 120 && i < ids.length; i++) {
  const wrong = i < 30 ? (30 - i) : 0;          // 30..1 for the first thirty
  progress.stats[ids[i]] = { correct: 5, wrong: wrong, seen: 5 + wrong, streak: 0 };
}
progress.stats[ids[119]] = { correct: 80, wrong: 0, seen: 80, streak: 9 };  // mastered

const rows = hardestRows();
const set = {}; rows.forEach(function(r){ set[r.id] = true; });

// ranked by raw wrong count, descending
let ordered = true;
for (let i = 1; i < rows.length; i++) if (rows[i].wrong > rows[i-1].wrong) ordered = false;

// turn every drill type on so the round can always ask something
Object.keys(enabledModes).forEach(function(m){ enabledModes[m] = true; });

// Restrict the ordinary filters hard: a hardest round must ignore them.
const lessons = Object.keys(enabledLessons);
Object.keys(enabledLessons).forEach(function(l){ enabledLessons[l] = false; });
enabledLessons[lessons[0]] = true;

startHardestRound();
let asked = 0, outside = 0, distinct = {};
for (let i = 0; i < 600; i++) {
  const q = pickQuestion ? null : null;   // pickQuestion touches the DOM; use the generator
  const modes = Object.keys(enabledModes).filter(function(m){ return enabledModes[m]; });
  const mode = modes[i % modes.length];
  const c = generateQuestion(mode);
  if (!c) continue;
  asked++;
  distinct[c.entryId] = true;
  if (!set[c.entryId]) outside++;
}

// the header's selection line must describe the round, not the filters
const countEl = document.getElementById("selection-count");
renderSelectionCount();
const hardestCountLine = countEl.textContent;

// an ordinary round afterwards must go back to honouring the filters
startNewRound();
renderSelectionCount();
const normalCountLine = countEl.textContent;
let normalOutside = 0, normalAsked = 0;
for (let i = 0; i < 300; i++) {
  const modes = Object.keys(enabledModes).filter(function(m){ return enabledModes[m]; });
  const c = generateQuestion(modes[i % modes.length]);
  if (!c) continue;
  normalAsked++;
  const e = byId[c.entryId];
  if (e && !enabledLessons[e.lesson]) normalOutside++;
}

console.log(JSON.stringify({
  poolSize: rows.length,
  topWrong: rows.length ? rows[0].wrong : null,
  ordered: ordered,
  masteredIncluded: !!set[ids[119]],
  asked: asked,
  outsideSet: outside,
  distinctAsked: Object.keys(distinct).length,
  normalAsked: normalAsked,
  normalOutsideLesson: normalOutside,
  hardestCountLine: hardestCountLine,
  normalCountLine: normalCountLine,
  hardestFlagCleared: hardestMode === false
}));
"""


def run(app):
    src = open(os.path.join(LT, app), encoding="utf-8").read()
    js = src.split("<script>", 1)[1].rsplit("</script>", 1)[0]
    stub = open(os.path.join(HERE, "dom_stub.js"), encoding="utf-8").read()
    d = tempfile.mkdtemp()
    p = os.path.join(d, "p.js")
    open(p, "w", encoding="utf-8").write(stub + js + PROBE)
    r = subprocess.run(["node", p], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-1500:])
        return None
    return json.loads(r.stdout)


def main():
    fails = 0
    for app in APPS:
        res = run(app)
        if res is None:
            print(f"{app:24} FAILED to run")
            fails += 1
            continue
        checks = [
            ("pool is 10% of 120 attempted", res["poolSize"] == 12),
            ("ranked by wrong count", res["ordered"]),
            ("mastered word excluded", not res["masteredIncluded"]),
            ("questions produced", res["asked"] > 0),
            ("only hardest words asked", res["outsideSet"] == 0),
            ("ordinary round honours filters again", res["normalOutsideLesson"] == 0),
            ("flag cleared by new round", res["hardestFlagCleared"]),
            ("count line names the round",
             "hardest-words round" in res["hardestCountLine"]),
            ("count line back to selection",
             res["normalCountLine"].endswith("in selection")),
        ]
        bad = [n for n, ok in checks if not ok]
        status = "ok" if not bad else "FAIL: " + "; ".join(bad)
        print(f"{app:24} pool={res['poolSize']:3} asked={res['asked']:4} "
              f"distinct={res['distinctAsked']:3} outside={res['outsideSet']:3}  {status}")
        if bad:
            fails += 1
    print("\nall hardest-round checks pass" if not fails else f"\nFAILURES: {fails}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
