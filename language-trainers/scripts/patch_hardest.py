#!/usr/bin/env python3
"""Add a "hardest words" round to the language trainers.

Why it is needed. The per-item weighting already favours words you get wrong,
but only softly: an always-wrong item scores 5 against 1 for a mastered one, and
an unseen item outranks both at 12. In a deck of ~1000 that still buys a hard
word roughly one question in seven, and only once coverage is complete. Soft
weighting cannot concentrate practice — the same conclusion reached earlier for
repeat avoidance, where only a hard exclusion moved the distribution.

The round drills ONLY the words you have got wrong most often.

Owner's design choices (asked before building):
  ranking  — raw wrong count, no minimum-attempts floor. A near-miss already
             counts as half a wrong when recorded, so typos carry weight.
  scope    — global. It deliberately IGNORES the lesson and word-form filters,
             so it is always the hardest words overall, not the hardest within
             whatever happens to be selected.
  shape    — a separate round button, like the existing "Re-drill N missed",
             rather than a drill type or a fourth filter. It reuses the round
             machinery and touches no existing selection logic.

Enabled DRILL TYPES still apply — the round has to ask its questions somehow,
and this way "hardest words, as cloze" works.

Re-runnable: every patch checks whether it is already present.

    python3 scripts/patch_hardest.py
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LT = os.path.join(HERE, "..")
APPS = ["polish_trainer.html", "spanish_trainer.html", "italian_trainer.html",
        "french_trainer.html", "latin_trainer.html", "medical_trainer.html",
        "portuguese_trainer.html"]

CORE_JS = r'''
// --- Hardest-words round --------------------------------------------------
// The weighting below already prefers items you get wrong, but softly: 5 for an
// always-wrong item against 1 for a mastered one, and 12 for an unseen one, so
// in a deck this size a hard word still only comes up about one question in
// seven. This round draws ONLY from the words with the most wrong answers.
// Deliberately global: it ignores the lesson and word-form filters, so it is
// the hardest words overall rather than the hardest within the current view.
const HARDEST_SHARE = 0.10;    // top 10% of everything attempted
const HARDEST_MIN_POOL = 8;    // below this there is too little history to be useful

let hardestMode = false;       // is the current round a hardest-words round?
let hardestIds = null;         // {id: true} fixed at the start of that round

// Ranked by raw wrong count, as asked for. recordAnswer already scores a
// near-miss as half a wrong, so typos count toward difficulty without a typo
// outranking an outright wrong answer.
function hardestRows() {
  const stats = (progress && progress.stats) || {};
  const rows = [];
  let attempted = 0;
  Object.keys(stats).forEach(function(id) {
    const s = stats[id];
    if (!s || !s.seen || !byId[id]) return;   // entries only; unseen never qualifies
    attempted++;
    if (s.wrong > 0) rows.push({ id: id, wrong: s.wrong, seen: s.seen });
  });
  rows.sort(function(a, b) {
    if (b.wrong !== a.wrong) return b.wrong - a.wrong;
    return (b.wrong / b.seen) - (a.wrong / a.seen);   // tie-break on the worse rate
  });
  // 10% of everything attempted, but never more than there are words with a
  // mistake against them -- a word you have never got wrong is not hard.
  const target = Math.max(HARDEST_MIN_POOL, Math.ceil(attempted * HARDEST_SHARE));
  return rows.slice(0, Math.min(target, rows.length));
}

function startHardestRound() {
  const rows = hardestRows();
  if (rows.length === 0) return;
  hardestIds = {};
  rows.forEach(function(r) { hardestIds[r.id] = true; });
  session = { count: 0, results: [] };
  summaryShowing = false;
  reviewMode = false;
  reviewQueue = [];
  reviewOrigin = [];
  roundAsked = new Set();
  breakShown = false;
  hardestMode = true;
  pickQuestion();
  renderHardestButton();
  renderSelectionCount();   // the header line must describe this round, not the filters
}

function renderHardestButton() {
  const row = document.getElementById("hardest-row");
  if (!row) return;
  while (row.firstChild) row.removeChild(row.firstChild);
  const rows = hardestRows();
  const ready = rows.length >= HARDEST_MIN_POOL;
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "btn-hardest";
  btn.textContent = ready ? "Drill my hardest words (" + rows.length + ")"
                          : "Drill my hardest words";
  if (ready) btn.addEventListener("click", startHardestRound);
  else btn.disabled = true;
  row.appendChild(btn);
  const note = document.createElement("span");
  note.className = "hardest-note";
  note.textContent = hardestMode
    ? "hardest-words round in progress"
    : ready ? "the " + rows.length + " you get wrong most often — ignores the filters below"
            : "unlocks once " + HARDEST_MIN_POOL + " different words have been missed (" +
              rows.length + " so far)";
  row.appendChild(note);
}
'''

BUTTON_HTML = '''    <div class="hardest-row" id="hardest-row"></div>
  </header>'''

BUTTON_CSS = '''  .hardest-row{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:10px}
  .btn-hardest{font:inherit;font-size:13px;font-weight:600;padding:7px 13px;border-radius:8px;
    border:1px solid var(--ink);background:var(--ink);color:var(--paper);cursor:pointer}
  .btn-hardest:disabled{opacity:.4;cursor:default}
  .hardest-note{font-size:12px;color:var(--muted)}
'''


def read(p):
    return open(os.path.join(LT, p), encoding="utf-8").read()


def write(p, s):
    open(os.path.join(LT, p), "w", encoding="utf-8").write(s)


def patch(name):
    src = read(name)
    if "hardestRows" in src:
        return "already present"
    notes = []

    # 1. core JS, before the round starter it sits next to
    anchor = "function startNewRound() {"
    assert src.count(anchor) == 1, f"{name}: startNewRound not found"
    src = src.replace(anchor, CORE_JS.strip() + "\n\n" + anchor)

    # 2. reset the flag whenever an ordinary round begins, and put the header's
    #    selection line back to describing the filters
    old = """function startNewRound() {
  session = { count: 0, results: [] };
  summaryShowing = false;
  reviewMode = false;"""
    assert src.count(old) == 1, f"{name}: startNewRound body not found"
    src = src.replace(old, old.replace("  reviewMode = false;",
                                       "  reviewMode = false;\n  hardestMode = false;\n  hardestIds = null;"))
    old = """  breakShown = false;
  pickQuestion();
}"""
    assert src.count(old) == 1, f"{name}: startNewRound tail not found"
    src = src.replace(old, """  breakShown = false;
  pickQuestion();
  renderHardestButton();
  renderSelectionCount();
}""")

    # 3. the pool. In a hardest round the lesson/word-form filters are bypassed
    #    entirely -- that is the "global" choice, made deliberately.
    old = ("    pool = entries.filter(function(e){ return filter(e) && "
           "enabledLessons[e.lesson] && enabledPos[e.pos]; });")
    assert src.count(old) == 1, f"{name}: buildPool predicate not found"
    new = """    pool = entries.filter(function(e){
      if (!filter(e)) return false;
      // A hardest-words round is global on purpose: it ignores the lesson and
      // word-form filters so it always drills the hardest words overall.
      if (hardestMode) return !!(hardestIds && hardestIds[e.id]);
      return enabledLessons[e.lesson] && enabledPos[e.pos];
    });"""
    src = src.replace(old, new)

    # 4. "have I covered the selection?" must mean the hardest set in that round
    old = """function selectionExhausted() {
  const selIds = VOCAB_DATA.entries
    .filter(function(e){ return enabledLessons[e.lesson] && enabledPos[e.pos] && selectionCanAsk(e); })
    .map(function(e){ return e.id; });"""
    assert src.count(old) == 1, f"{name}: selectionExhausted not found"
    new = """function selectionExhausted() {
  const selIds = VOCAB_DATA.entries
    .filter(function(e){
      if (hardestMode) return !!(hardestIds && hardestIds[e.id]) && selectionCanAsk(e);
      return enabledLessons[e.lesson] && enabledPos[e.pos] && selectionCanAsk(e);
    })
    .map(function(e){ return e.id; });"""
    src = src.replace(old, new)

    # 5. curated sentence banks draw from VOCAB_DATA.special, not entries, so
    #    they cannot honour hardestIds -- keep them out of the round entirely.
    if "function specialModeAllowed(type)" in src:
        src = re.sub(r"function specialModeAllowed\(type\) \{",
                     "function specialModeAllowed(type) {\n"
                     "  // Sentence-bank drills draw from VOCAB_DATA.special rather than entries,\n"
                     "  // so they have no entry id to match against the hardest set.\n"
                     "  if (hardestMode) return false;",
                     src, count=1)
        notes.append("special banks gated")

    # 6. keep the button's count fresh -- renderStats runs after every answer
    old = "function renderStats() {"
    assert src.count(old) == 1, f"{name}: renderStats not found"
    src = src.replace(old, old + "\n  renderHardestButton();")

    # 7. mention the round in the empty state, so a dead end explains itself
    old = '      : "No words match the selected drill types, lessons, and word forms.";'
    assert src.count(old) == 1, f"{name}: empty-state chain not found"
    new = ('      : hardestMode ? "None of the selected drill types can ask your hardest words. '
           'Turn on more drill types, or start a new round."\n'
           '      : "No words match the selected drill types, lessons, and word forms.";')
    src = src.replace(old, new)

    # 8. offer it from the round summary too
    old = """    const next = document.createElement("button");
    next.type = "button"; next.className = "btn-ghost";
    next.textContent = "New round";
    next.addEventListener("click", startNewRound);
    actions.appendChild(next);"""
    assert src.count(old) == 1, f"{name}: summary buttons not found"
    src = src.replace(old, old + """
    if (hardestRows().length >= HARDEST_MIN_POOL) {
      const hard = document.createElement("button");
      hard.type = "button"; hard.className = "btn-ghost";
      hard.textContent = "Hardest words";
      hard.addEventListener("click", startHardestRound);
      actions.appendChild(hard);
    }""")

    # 10. the header's "N words in selection" line counts the filtered selection,
    #     which is not what a hardest round is drilling -- during the round it
    #     would claim 880 words while the pool is 12. Say what is actually in play.
    old = """  const n = VOCAB_DATA.entries.filter(function(e){
    return enabledLessons[e.lesson] && enabledPos[e.pos] && selectionCanAsk(e);
  }).length;
  el.textContent = n + (n === 1 ? " word" : " words") + " in selection";"""
    assert src.count(old) == 1, f"{name}: renderSelectionCount body not found"
    new = """  if (hardestMode && hardestIds) {
    const h = VOCAB_DATA.entries.filter(function(e){
      return hardestIds[e.id] && selectionCanAsk(e);
    }).length;
    el.textContent = h + (h === 1 ? " word" : " words") + " in this hardest-words round";
    return;
  }
  const n = VOCAB_DATA.entries.filter(function(e){
    return enabledLessons[e.lesson] && enabledPos[e.pos] && selectionCanAsk(e);
  }).length;
  el.textContent = n + (n === 1 ? " word" : " words") + " in selection";"""
    src = src.replace(old, new)

    # 9. markup + styling
    assert src.count("  </header>") == 1, f"{name}: header close not found"
    src = src.replace("  </header>", BUTTON_HTML)
    anchor_css = "  .empty {"
    assert src.count(anchor_css) >= 1, f"{name}: CSS anchor not found"
    src = src.replace(anchor_css, BUTTON_CSS + anchor_css, 1)

    write(name, src)
    return "patched" + (" (" + ", ".join(notes) + ")" if notes else "")


def main():
    for name in APPS:
        print(f"{name}: {patch(name)}")


if __name__ == "__main__":
    main()
