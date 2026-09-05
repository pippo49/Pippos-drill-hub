#!/usr/bin/env python3
"""Port the no-repeat, hard-stop round from Polish to the other apps.

Polish (patched by hand, then proven out) changed a round from open-ended --
a word could resurface before every word had a turn, and reaching full
coverage paused with "Stop and review, or keep going?" -- into one that asks
every (word, enabled drill type) pair exactly once and then stops straight
into the summary. See HANDOFF.md for the full history of that change,
including why coverage is per (word, mode) and not just per word.

This script applies the same change to spanish, italian, french and latin
(the four other hand-maintained sources). The transformation is mostly
language-agnostic -- buildPool's exclusion, selectionExhausted, pickQuestion's
interstitial, and showSelectionBreak/breakShown are byte-identical across all
five apps before this patch -- so one shared diff covers them, parameterised
only by:
  - each app's own translation-mode key names (es_en/en_es, it_en/en_it, ...)
    and native/gloss field names, for the MODE_ELIGIBLE table;
  - any extra entries-based mode (Latin's principal_parts);
  - any curated sentence banks (VOCAB_DATA.special), which Spanish, Italian
    and French have (two each) and Latin does not. A bank's items get the
    same per-(item, mode) hard exclusion as the vocab pool, keyed by the
    bank's own ids, and selectionExhausted gets a second loop over each
    enabled, pos-allowed bank so a round with a special mode enabled doesn't
    end while bank items remain uncovered -- or never end, if a special mode
    is the ONLY thing enabled and nothing in MODE_ELIGIBLE is tracking it.

Medical and the two Portuguese apps are GENERATED (from Latin and Spanish
respectively) -- this script does not touch them. Re-run their generators
after this patch; medical's generateQuestion is wholly custom and needs its
own equivalent change, done separately in make_medical_trainer.py. Portuguese
adds three more special modes on top of Spanish's two (personal_inf, fut_subj,
false_friend) -- make_portuguese_trainer.py's own patch extends SPECIAL_MODES
for those.

Re-runnable: checks whether it is already present.

    python3 scripts/patch_no_repeat_round.py
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LT = os.path.join(HERE, "..")


def read(p):
    return open(os.path.join(LT, p), encoding="utf-8").read()


def write(p, s):
    open(os.path.join(LT, p), "w", encoding="utf-8").write(s)


# --- Shared (language-agnostic) pieces, byte-identical across every app in
# its pre-patch state -- confirmed against Polish's own pre-patch source. ---

OLD_ROUNDASKED_DECL = (
    'let roundAsked = new Set();        '
    '// distinct entry ids asked this round (for selection coverage)'
)
NEW_ROUNDASKED_DECL = (
    '// "entryId|mode" pairs asked this round -- coverage is by WORD AND DRILL\n'
    '// TYPE, not just word: a word with both translation directions and cloze\n'
    '// enabled needs all three asked before it stops offering itself, not one.\n'
    'let roundAsked = new Set();'
)

OLD_BUILD_POOL_TAIL = """    if (pool.length === 0) { weights = []; return; }
    // Never ask the same word twice in a row, as long as there's an alternative
    if (pool.length > 1) {
      const last = recentIds[recentIds.length - 1];
      const trimmed = pool.filter(function(e){ return e.id !== last; });
      if (trimmed.length > 0) pool = trimmed;
    }
    // Hard floor: also exclude anything asked in the last NO_REPEAT_WINDOW turns,
    // as long as the current selection is big enough to still leave a choice.
    if (pool.length > 1 && recentIds.length > 0) {
      const noRepeatWindow = Math.min(recentIds.length, pool.length - 1, NO_REPEAT_WINDOW);
      if (noRepeatWindow > 0) {
        const banned = {};
        recentIds.slice(-noRepeatWindow).forEach(function(id){ banned[id] = true; });
        const fresh = pool.filter(function(e){ return !banned[e.id]; });
        if (fresh.length > 0) pool = fresh;
      }
    }
    weights = pool.map(function(e) {
      var w = weightFor(progress.stats, e.id);
      // Within this round, strongly prefer words not yet asked, so a round walks
      // through the whole selection once before repeating.
      if (!roundAsked.has(e.id)) w *= 6;
      // Soft penalty for recently asked words so they resurface much less often
      var idx = recentIds.lastIndexOf(e.id);
      if (idx >= 0) {
        var recency = recentIds.length - idx; // 1 = most recently asked
        w *= recency / (recency + 12);         // ~0.08 most-recent … →1 as it ages out
      }
      return w;
    });
  };"""

NEW_BUILD_POOL_TAIL = """    if (pool.length === 0) { weights = []; return; }
    // Hard stop: never repeat the same (word, drill type) pair within a round.
    // A word with pl_de, de_pl and cloze all enabled needs all three asked
    // before IT stops offering itself in any of them -- coverage is tracked
    // per mode, not just per word. Once every enabled-and-eligible pair for
    // the whole selection is covered, pickQuestion ends the round (see
    // selectionExhausted) instead of relying on this to run dry -- by the time
    // buildPool empties out for one mode, some other enabled mode still has an
    // uncovered pair, unless the whole round is genuinely done.
    pool = pool.filter(function(e){ return !roundAsked.has(e.id + "|" + mode); });
    if (pool.length === 0) { weights = []; return; }
    // Never ask the same word twice in a row, as long as there's an alternative
    if (pool.length > 1) {
      const last = recentIds[recentIds.length - 1];
      const trimmed = pool.filter(function(e){ return e.id !== last; });
      if (trimmed.length > 0) pool = trimmed;
    }
    // Hard floor: also exclude anything asked in the last NO_REPEAT_WINDOW turns.
    // recentIds is never reset between rounds, so this is what stops a new round
    // from immediately re-opening with the previous round's last few words.
    if (pool.length > 1 && recentIds.length > 0) {
      const noRepeatWindow = Math.min(recentIds.length, pool.length - 1, NO_REPEAT_WINDOW);
      if (noRepeatWindow > 0) {
        const banned = {};
        recentIds.slice(-noRepeatWindow).forEach(function(id){ banned[id] = true; });
        const fresh = pool.filter(function(e){ return !banned[e.id]; });
        if (fresh.length > 0) pool = fresh;
      }
    }
    weights = pool.map(function(e) {
      var w = weightFor(progress.stats, e.id);
      // Soft penalty for a word from the tail of the previous round, so it
      // doesn't open the new one too -- same carry-over as the filter above.
      var idx = recentIds.lastIndexOf(e.id);
      if (idx >= 0) {
        var recency = recentIds.length - idx; // 1 = most recently asked
        w *= recency / (recency + 12);         // ~0.08 most-recent … →1 as it ages out
      }
      return w;
    });
  };"""

OLD_ADD = '  roundAsked.add(currentQ.entryId);'
NEW_ADD = '  roundAsked.add(currentQ.entryId + "|" + currentQ.type);'

OLD_INTERSTITIAL = """  // Once every word in the current selection has been asked this round, pause
  // and let the user choose to stop (and review) or keep going.
  if (!breakShown && session.count > 0 && selectionExhausted()) {
    showSelectionBreak();
    return;
  }"""
NEW_INTERSTITIAL = """  // Once every word in the current selection has had a turn this round, the
  // round is over: no repeats before then (see buildPool), and none after --
  // go straight to the summary, where "Re-drill mistakes" and, once those
  // clear, "Redrill the full round" carry on from here.
  if (session.count > 0 && selectionExhausted()) {
    showSummary();
    return;
  }"""

SHOW_SELECTION_BREAK_BLOCK = """function showSelectionBreak() {
  summaryShowing = false;
  currentQ = null;
  feedback = null;
  const area = document.getElementById("card-area");
  area.innerHTML = "";
  const card = document.createElement("div");
  card.className = "card";

  const headRow = document.createElement("div");
  headRow.className = "card-head";
  const label = document.createElement("div");
  label.className = "prompt-label";
  label.textContent = "Selection complete";
  headRow.appendChild(label);
  card.appendChild(headRow);

  const msg = document.createElement("div");
  msg.className = "prompt";
  msg.textContent = "You've been through every word in this selection. Stop and review, or keep going?";
  card.appendChild(msg);

  const actions = document.createElement("div");
  actions.className = "actions";
  const end = document.createElement("button");
  end.type = "button"; end.className = "btn-primary";
  end.textContent = "End & show summary";
  end.addEventListener("click", showSummary);
  actions.appendChild(end);
  const cont = document.createElement("button");
  cont.type = "button"; cont.className = "btn-ghost";
  cont.textContent = "Keep going";
  cont.addEventListener("click", function() { breakShown = true; pickQuestion(false); });
  actions.appendChild(cont);
  card.appendChild(actions);

  area.appendChild(card);
}

"""

OLD_EXHAUSTED = """function selectionExhausted() {
  const selIds = VOCAB_DATA.entries
    .filter(function(e){
      if (hardestMode) return !!(hardestIds && hardestIds[e.id]) && selectionCanAsk(e);
      return enabledLessons[e.lesson] && enabledPos[e.pos] && selectionCanAsk(e);
    })
    .map(function(e){ return e.id; });
  if (selIds.length === 0) return false;
  for (let i = 0; i < selIds.length; i++) {
    if (!roundAsked.has(selIds[i])) return false;
  }
  return true;
}"""

# {bank_loop} is "" for apps with no curated sentence banks (Latin), or the
# per-app SPECIAL_MODES loop for those that do (Spanish/Italian/French).
NEW_EXHAUSTED_TEMPLATE = """function selectionExhausted() {{
  const sel = VOCAB_DATA.entries.filter(function(e){{
    if (hardestMode) return !!(hardestIds && hardestIds[e.id]);
    return enabledLessons[e.lesson] && enabledPos[e.pos];
  }});
  const enabled = Object.keys(enabledModes).filter(function(m){{ return enabledModes[m]; }});
  // Exhausted means every (word, enabled drill type) pair the selection can
  // actually produce has been asked -- not just every word in SOME mode.
  // `any` guards the case where the selection has nothing askable at all
  // (matches the old selectionCanAsk-based check: nothing to ask is not the
  // same as everything asked).
  let any = false;
  for (let i = 0; i < sel.length; i++) {{
    const e = sel[i];
    for (let j = 0; j < enabled.length; j++) {{
      const m = enabled[j];
      if (!MODE_ELIGIBLE[m]) continue;
      if (!MODE_ELIGIBLE[m](e)) continue;
      any = true;
      if (!roundAsked.has(e.id + "|" + m)) return false;
    }}
  }}{bank_loop}
  return any;
}}"""

BANK_LOOP_TEMPLATE = """
  // Curated sentence banks (VOCAB_DATA.special) are a separate, non-lesson-
  // scoped pool with their own coverage requirement: every item in an
  // enabled, pos-allowed bank must be asked too before the round is done.
  for (let i = 0; i < SPECIAL_MODES.length; i++) {
    const m = SPECIAL_MODES[i];
    if (!enabledModes[m] || !specialModeAllowed(m)) continue;
    const bank = (VOCAB_DATA.special && VOCAB_DATA.special[m]) || [];
    for (let k = 0; k < bank.length; k++) {
      any = true;
      if (!roundAsked.has(bank[k].id + "|" + m)) return false;
    }
  }"""

# Shared across the three apps that HAVE curated sentence banks: the hard
# per-(item, mode) exclusion, inserted right where `items` is first bound.
OLD_BANK_ITEMS_START = """    if (bank.length === 0) return null;
    let items = bank;
    if (bank.length > 1) {
      const last = recentIds[recentIds.length - 1];
      const trimmed = bank.filter(function(x){ return x.id !== last; });
      if (trimmed.length > 0) items = trimmed;
    }"""
NEW_BANK_ITEMS_START = """    if (bank.length === 0) return null;
    let items = bank;
    // Same hard stop as the vocab pool: never repeat a bank item within a
    // round (see buildPool's roundAsked exclusion). Must run BEFORE the
    // last-id/no-repeat-window narrowing below, and those must narrow
    // `items` (not re-derive from `bank`), or this gets silently discarded --
    // the two used to be interchangeable because nothing had narrowed `items`
    // yet at that point; that stopped being true the moment this was added.
    items = items.filter(function(x){ return !roundAsked.has(x.id + "|" + mode); });
    if (items.length === 0) return null;
    if (items.length > 1) {
      const last = recentIds[recentIds.length - 1];
      const trimmed = items.filter(function(x){ return x.id !== last; });
      if (trimmed.length > 0) items = trimmed;
    }"""


def patch_shared(src, name):
    if "MODE_ELIGIBLE" in src:
        return src, "already present"
    assert src.count(OLD_ROUNDASKED_DECL) == 1, f"{name}: roundAsked decl not found"
    src = src.replace(OLD_ROUNDASKED_DECL, NEW_ROUNDASKED_DECL)
    assert src.count(OLD_BUILD_POOL_TAIL) == 1, f"{name}: buildPool tail not found"
    src = src.replace(OLD_BUILD_POOL_TAIL, NEW_BUILD_POOL_TAIL)
    assert src.count(OLD_ADD) == 1, f"{name}: roundAsked.add site not found"
    src = src.replace(OLD_ADD, NEW_ADD)
    assert src.count(OLD_INTERSTITIAL) == 1, f"{name}: interstitial check not found"
    src = src.replace(OLD_INTERSTITIAL, NEW_INTERSTITIAL)
    assert src.count(SHOW_SELECTION_BREAK_BLOCK) == 1, f"{name}: showSelectionBreak block not found"
    src = src.replace(SHOW_SELECTION_BREAK_BLOCK, "")
    return src, "patched"


def strip_breakshown(src, name):
    """Remove the now-dead breakShown flag: 1 declaration + 5 bare resets
    (3 filter-render functions, startHardestRound, startNewRound)."""
    lines = src.split("\n")
    decl_removed = False
    kept = []
    bare_removed = 0
    for ln in lines:
        stripped = ln.strip()
        if stripped.startswith("let breakShown = false;"):
            decl_removed = True
            continue
        if stripped == "breakShown = false;":
            bare_removed += 1
            continue
        kept.append(ln)
    assert decl_removed, f"{name}: breakShown declaration not found"
    assert bare_removed == 5, f"{name}: expected 5 bare breakShown resets, found {bare_removed}"
    return "\n".join(kept)


def patch_exhausted(src, name, mode_eligible_js, has_banks):
    bank_loop = BANK_LOOP_TEMPLATE if has_banks else ""
    new_exhausted = NEW_EXHAUSTED_TEMPLATE.format(bank_loop=bank_loop)
    assert src.count(OLD_EXHAUSTED) == 1, f"{name}: selectionExhausted not found"
    src = src.replace(OLD_EXHAUSTED, new_exhausted)
    return src


def patch_mode_eligible(src, name, mode_labels_block, mode_eligible_js):
    assert src.count(mode_labels_block) == 1, f"{name}: MODE_LABELS block not found"
    src = src.replace(mode_labels_block, mode_labels_block + "\n\n" + mode_eligible_js)
    return src


def patch_bank_items(src, name):
    assert src.count(OLD_BANK_ITEMS_START) >= 1, f"{name}: bank items start not found"
    src = src.replace(OLD_BANK_ITEMS_START, NEW_BANK_ITEMS_START)
    return src


def patch_special_modes(src, name, special_allowed_close, special_modes_js):
    assert src.count(special_allowed_close) == 1, f"{name}: specialModeAllowed close not found"
    src = src.replace(special_allowed_close, special_allowed_close + "\n" + special_modes_js)
    return src


# --- Per-app config -------------------------------------------------------

def mode_eligible_js(field, gloss, translate_modes, extra=""):
    lines = [f'  {m}: (e) => e.{field} && e.{gloss},' for m in translate_modes]
    body = "\n".join(lines)
    return f"""// Whether a given drill type CAN ask a given entry at all, independent of
// whether that mode is currently enabled. Mirrors each mode's own buildPool
// filter in generateQuestion exactly -- kept as one table so the two can't
// drift apart -- and is what per-(word, drill type) round coverage is
// measured against in selectionExhausted.
const MODE_ELIGIBLE = {{
{body}
  conjugate: (e) => e.pos === "verb" && e.conjugation,
  decline: (e) => e.pos === "adjective" && e.declension,
  noun_case: (e) => e.pos === "noun" && e.noun_decl,
  cloze: (e) => e.cloze && e.cloze.length,
  antonym: (e) => e.antonyms && e.antonyms.length > 0,
  synonym: (e) => e.synonyms && e.synonyms.length > 0,{extra}
}};"""


APPS = {
    "spanish_trainer.html": dict(
        mode_labels_block=(
            'const MODE_LABELS = [\n'
            '  ["es_en", "ES → EN"],\n'
            '  ["en_es", "EN → ES"],\n'
            '  ["conjugate", "Conjugate"],\n'
            '  ["decline", "Decline"],\n'
            '  ["noun_case", "Noun forms"],\n'
            '  ["antonym", "Antonyms"],\n'
            '  ["synonym", "Synonyms"],\n'
            '  ["multiple_choice", "Multiple choice"],\n'
            '  ["cloze", "Cloze"],\n'
            '  ["ser_estar", "Ser vs estar"],\n'
            '  ["por_para", "Por vs para"],\n'
            '];'
        ),
        mode_eligible=mode_eligible_js("es", "en", ["es_en", "en_es", "multiple_choice"]),
        has_banks=True,
        special_allowed_close=(
            'function specialModeAllowed(type) {\n'
            '  // Sentence-bank drills draw from VOCAB_DATA.special rather than entries,\n'
            '  // so they have no entry id to match against the hardest set.\n'
            '  if (hardestMode) return false;\n'
            '  if (type === "ser_estar") return !!enabledPos.verb;\n'
            '  if (type === "por_para") return !!enabledPos.preposition;\n'
            '  return true;\n'
            '}'
        ),
        special_modes=["ser_estar", "por_para"],
    ),
    "italian_trainer.html": dict(
        mode_labels_block=(
            'const MODE_LABELS = [\n'
            '  ["it_en", "IT → EN"],\n'
            '  ["en_it", "EN → IT"],\n'
            '  ["conjugate", "Conjugate"],\n'
            '  ["decline", "Decline"],\n'
            '  ["noun_case", "Noun forms"],\n'
            '  ["antonym", "Antonyms"],\n'
            '  ["synonym", "Synonyms"],\n'
            '  ["multiple_choice", "Multiple choice"],\n'
            '  ["cloze", "Cloze"],\n'
            '  ["essere_stare", "Essere vs stare"],\n'
            '  ["avere_essere", "Avere vs essere"],\n'
            '];'
        ),
        mode_eligible=mode_eligible_js("it", "en", ["it_en", "en_it", "multiple_choice"]),
        has_banks=True,
        special_allowed_close=(
            'function specialModeAllowed(type) {\n'
            '  // Sentence-bank drills draw from VOCAB_DATA.special rather than entries,\n'
            '  // so they have no entry id to match against the hardest set.\n'
            '  if (hardestMode) return false;\n'
            '  // Both Italian banks drill verb usage, so both follow the Verbs toggle.\n'
            '  if (type === "essere_stare" || type === "avere_essere") return !!enabledPos.verb;\n'
            '  return true;\n'
            '}'
        ),
        special_modes=["essere_stare", "avere_essere"],
    ),
    "french_trainer.html": dict(
        mode_labels_block=(
            'const MODE_LABELS = [\n'
            '  ["fr_en", "FR → EN"],\n'
            '  ["en_fr", "EN → FR"],\n'
            '  ["conjugate", "Conjugate"],\n'
            '  ["decline", "Decline"],\n'
            '  ["noun_case", "Noun forms"],\n'
            '  ["antonym", "Antonyms"],\n'
            '  ["synonym", "Synonyms"],\n'
            '  ["multiple_choice", "Multiple choice"],\n'
            '  ["cloze", "Cloze"],\n'
            '  ["tu_vous", "Tu vs vous"],\n'
            '  ["avoir_etre", "Avoir vs être"],\n'
            '];'
        ),
        mode_eligible=mode_eligible_js("fr", "en", ["fr_en", "en_fr", "multiple_choice"]),
        has_banks=True,
        special_allowed_close=(
            'function specialModeAllowed(type) {\n'
            '  // Sentence-bank drills draw from VOCAB_DATA.special rather than entries,\n'
            '  // so they have no entry id to match against the hardest set.\n'
            '  if (hardestMode) return false;\n'
            '  // Both French banks drill verb usage, so both follow the Verbs toggle.\n'
            '  if (type === "tu_vous" || type === "avoir_etre") return !!enabledPos.verb;\n'
            '  return true;\n'
            '}'
        ),
        special_modes=["tu_vous", "avoir_etre"],
    ),
    "latin_trainer.html": dict(
        mode_labels_block=(
            'const MODE_LABELS = [\n'
            '  ["la_en", "LA → EN"],\n'
            '  ["en_la", "EN → LA"],\n'
            '  ["conjugate", "Conjugate"],\n'
            '  ["decline", "Decline"],\n'
            '  ["noun_case", "Noun forms"],\n'
            '  ["antonym", "Antonyms"],\n'
            '  ["synonym", "Synonyms"],\n'
            '  ["multiple_choice", "Multiple choice"],\n'
            '  ["cloze", "Cloze"],\n'
            '  ["principal_parts", "Principal parts"],\n'
            '];'
        ),
        mode_eligible=mode_eligible_js(
            "la", "en", ["la_en", "en_la", "multiple_choice"],
            extra='\n  principal_parts: (e) => e.pos === "verb" && e.principal_parts && e.principal_parts.length > 1,',
        ),
        has_banks=False,
        special_allowed_close=None,
        special_modes=[],
    ),
}


def special_modes_js(modes):
    arr = ", ".join(f'"{m}"' for m in modes)
    return (
        "// Every curated-sentence-bank mode this app has, so selectionExhausted\n"
        "// and the bank's own hard exclusion can find them generically.\n"
        f"const SPECIAL_MODES = [{arr}];"
    )


def patch(fname, cfg):
    src = read(fname)
    notes = []
    src, note = patch_shared(src, fname)
    notes.append(f"shared round logic {note}")
    if note == "already present":
        write(fname, src)
        return " · ".join(notes)

    src = strip_breakshown(src, fname)
    notes.append("breakShown removed")

    src = patch_mode_eligible(src, fname, cfg["mode_labels_block"], cfg["mode_eligible"])
    notes.append("MODE_ELIGIBLE added")

    if cfg["has_banks"]:
        src = patch_special_modes(src, fname, cfg["special_allowed_close"], special_modes_js(cfg["special_modes"]))
        src = patch_bank_items(src, fname)
        notes.append(f"special-bank coverage added ({', '.join(cfg['special_modes'])})")

    src = patch_exhausted(src, fname, cfg["mode_eligible"], cfg["has_banks"])
    notes.append("selectionExhausted rewritten")

    write(fname, src)
    return " · ".join(notes)


def main():
    for fname, cfg in APPS.items():
        print(f"{fname}: {patch(fname, cfg)}")


if __name__ == "__main__":
    main()
