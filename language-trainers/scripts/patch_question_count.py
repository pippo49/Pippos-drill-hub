#!/usr/bin/env python3
"""Show how many QUESTIONS a selection holds, not just how many words.

"N words in selection" already existed; it undercounts what a round actually
asks now that coverage is per (word, drill type) pair (see
patch_no_repeat_round.py) -- a selection with translation and conjugate both
enabled produces roughly twice as many questions as words, and the old line
never said so.

renderSelectionCount was byte-identical across Polish, Spanish, Italian,
French and Latin (confirmed before writing this), so one shared patch covers
all five. It counts every (word, enabled mode) pair via MODE_ELIGIBLE -- the
same table selectionExhausted checks coverage against, just without the
roundAsked filter, so it is the round's full size rather than what is left of
it -- plus every item of an enabled, pos-allowed curated bank via
SPECIAL_MODES, guarded by `typeof SPECIAL_MODES !== "undefined"` so the same
code works unchanged on Latin and Polish, which have no such banks.

Medical and the two Portuguese apps are generated (from Latin and Spanish).
renderSelectionCount is NOT among the regions make_medical_trainer.py swaps,
so medical inherits this patched version verbatim on the next regeneration --
it already resolves against medical's own MODE_ELIGIBLE, defined in the
region that generator DOES swap. make_portuguese_trainer.py doesn't touch
renderSelectionCount either (no es/pt field reference in it), so it likewise
just needs regenerating, not a generator change.

Re-runnable: checks whether it is already present.

    python3 scripts/patch_question_count.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LT = os.path.join(HERE, "..")

APPS = [
    "polish_trainer.html",
    "spanish_trainer.html",
    "italian_trainer.html",
    "french_trainer.html",
    "latin_trainer.html",
]

OLD = '''function renderSelectionCount() {
  const el = document.getElementById("selection-count");
  if (!el) return;
  const anyLesson = ALL_LESSONS.some(function(l){ return enabledLessons[l]; });
  const anyPos = ALL_POS.some(function(p){ return enabledPos[p]; });
  const anyMode = Object.keys(enabledModes).some(function(m){ return enabledModes[m]; });
  if (!anyLesson) { el.textContent = "no lessons selected"; return; }
  if (!anyPos) { el.textContent = "no word forms selected"; return; }
  if (!anyMode) { el.textContent = "no drill types selected"; return; }
  if (hardestMode && hardestIds) {
    const h = VOCAB_DATA.entries.filter(function(e){
      return hardestIds[e.id] && selectionCanAsk(e);
    }).length;
    el.textContent = h + (h === 1 ? " word" : " words") + " in this hardest-words round";
    return;
  }
  const n = VOCAB_DATA.entries.filter(function(e){
    return enabledLessons[e.lesson] && enabledPos[e.pos] && selectionCanAsk(e);
  }).length;
  el.textContent = n + (n === 1 ? " word" : " words") + " in selection";
}'''

NEW = '''function renderSelectionCount() {
  const el = document.getElementById("selection-count");
  if (!el) return;
  const anyLesson = ALL_LESSONS.some(function(l){ return enabledLessons[l]; });
  const anyPos = ALL_POS.some(function(p){ return enabledPos[p]; });
  const anyMode = Object.keys(enabledModes).some(function(m){ return enabledModes[m]; });
  if (!anyLesson) { el.textContent = "no lessons selected"; return; }
  if (!anyPos) { el.textContent = "no word forms selected"; return; }
  if (!anyMode) { el.textContent = "no drill types selected"; return; }
  const enabledModeList = Object.keys(enabledModes).filter(function(m){ return enabledModes[m]; });
  // Every (word, drill type) pair a round would actually ask, plus every item
  // of a curated sentence bank whose mode is enabled and pos-allowed (apps
  // with no SPECIAL_MODES array simply contribute none) -- the same tally
  // selectionExhausted measures round coverage against, just without the
  // roundAsked filter, so this is the whole round's size, not what's left.
  const countQuestions = function(sel) {
    let q = 0;
    for (let i = 0; i < sel.length; i++) {
      for (let j = 0; j < enabledModeList.length; j++) {
        const m = enabledModeList[j];
        if (MODE_ELIGIBLE[m] && MODE_ELIGIBLE[m](sel[i])) q++;
      }
    }
    if (typeof SPECIAL_MODES !== "undefined") {
      SPECIAL_MODES.forEach(function(m){
        if (!enabledModes[m] || !specialModeAllowed(m)) return;
        q += ((VOCAB_DATA.special && VOCAB_DATA.special[m]) || []).length;
      });
    }
    return q;
  };
  if (hardestMode && hardestIds) {
    const sel = VOCAB_DATA.entries.filter(function(e){
      return hardestIds[e.id] && selectionCanAsk(e);
    });
    const h = sel.length;
    const q = countQuestions(sel);
    el.textContent = h + (h === 1 ? " word" : " words") + " \\u00b7 " +
      q + (q === 1 ? " question" : " questions") + " in this hardest-words round";
    return;
  }
  const sel = VOCAB_DATA.entries.filter(function(e){
    return enabledLessons[e.lesson] && enabledPos[e.pos] && selectionCanAsk(e);
  });
  const n = sel.length;
  const q = countQuestions(sel);
  el.textContent = n + (n === 1 ? " word" : " words") + " \\u00b7 " +
    q + (q === 1 ? " question" : " questions") + " in selection";
}'''


def read(p):
    return open(os.path.join(LT, p), encoding="utf-8").read()


def write(p, s):
    open(os.path.join(LT, p), "w", encoding="utf-8").write(s)


def patch(name):
    src = read(name)
    if "countQuestions" in src:
        return "already present"
    assert src.count(OLD) == 1, f"{name}: renderSelectionCount not found"
    src = src.replace(OLD, NEW)
    write(name, src)
    return "patched"


def main():
    for name in APPS:
        print(f"{name}: {patch(name)}")


if __name__ == "__main__":
    main()
