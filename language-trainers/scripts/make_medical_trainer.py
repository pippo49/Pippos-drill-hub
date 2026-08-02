#!/usr/bin/env python3
"""Build medical_trainer.html from latin_trainer.html.

The engine (grading, SRS weighting, review rounds, the three selection filters,
the error box, the PWA registration) is shared and copied verbatim. What this
script replaces is everything domain-specific: the drill modes, the answerable
check, the extras panel, the labels and the branding.

Re-runnable: it always starts from latin_trainer.html, so engine fixes made
there flow into the medical app on the next run. Anything medical-only lives
here, not in the generated HTML.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "latin_trainer.html")
DST = os.path.join(HERE, "..", "medical_trainer.html")

# --------------------------------------------------------------- new engine bits

MODE_LABELS = '''const MODE_LABELS = [
  ["element_meaning", "Element \\u2192 meaning"],
  ["meaning_element", "Meaning \\u2192 element"],
  ["term_meaning", "Term \\u2192 meaning"],
  ["build", "Build the term"],
  ["analyse", "Break it down"],
  ["doublet", "Greek \\u2194 Latin"],
  ["plural", "Plurals"],
  ["confusable", "Easily confused"],
  ["abbreviation", "Prescription Latin"],
  ["multiple_choice", "Multiple choice"],
  ["cloze", "Clinical context"],
];

// The three element kinds that behave alike in the element drills.
const ELEMENT_POS = { prefix: 1, suffix: 1, root: 1 };

// An element may be typed with or without its slash and hyphens: "cardi/o",
// "cardio" and "cardi" are the same answer, and so are "-ectomy" and "ectomy".
function formVariants(form) {
  const out = [form, form.replace(/[-\\/]/g, "")];
  if (form.indexOf("/") >= 0) {
    const base = form.split("/")[0];
    out.push(base, base.replace(/-/g, ""));
  }
  if (form.charAt(0) === "-") out.push(form.slice(1));
  if (form.charAt(form.length - 1) === "-") out.push(form.slice(0, -1));
  return out.filter(function(v, i, a) { return v && a.indexOf(v) === i; });
}

// Glosses read "surgical removal, excision" \\u2014 accept either half alone.
function glossVariants(gloss) {
  const out = [gloss];
  gloss.split(/[;,]/).forEach(function(p) { const t = p.trim(); if (t) out.push(t); });
  return out.filter(function(v, i, a) { return v && a.indexOf(v) === i; });
}'''

GENERATE = r'''// === QUESTION GENERATORS ===
// Medical terminology is not a translation task, so these modes differ from the
// conversational trainers'. The core skill is morphological: take an unfamiliar
// term apart (analyse), put a correct one together from a description (build),
// and know which element carries which meaning in each direction. Added to that
// are the two things students are actually examined on and reliably get wrong:
// Greek/Latin doublets, and irregular classical plurals.
function generateQuestion(mode) {
  const entries = VOCAB_DATA.entries;
  let pool = [], weights = [];

  const buildPool = (filter) => {
    pool = entries.filter(function(e){ return filter(e) && enabledLessons[e.lesson] && enabledPos[e.pos]; });
    if (pool.length === 0) { weights = []; return; }
    if (pool.length > 1) {
      const last = recentIds[recentIds.length - 1];
      const trimmed = pool.filter(function(e){ return e.id !== last; });
      if (trimmed.length > 0) pool = trimmed;
    }
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
      const recency = recentIds.length - recentIds.lastIndexOf(e.id);
      if (recentIds.indexOf(e.id) >= 0) w *= recency / (recency + 12);
      return Math.max(w, 0.02);
    });
  };

  if (mode === "element_meaning") {
    buildPool(e => ELEMENT_POS[e.pos] && e.en);
    if (pool.length === 0) return null;
    const e = weightedPick(pool, weights);
    return { type: mode, entryId: e.id, prompt: e.term,
             promptLabel: e.origin + " " + e.pos,
             answerLabel: "Meaning", target: e.en, rawTarget: e.en,
             acceptableAnswers: glossVariants(e.en) };
  }

  if (mode === "meaning_element") {
    buildPool(e => ELEMENT_POS[e.pos] && e.en);
    if (pool.length === 0) return null;
    const e = weightedPick(pool, weights);
    // Several elements share one meaning on purpose (nephr/o and ren/o are both
    // "kidney"), so accept any element of the same kind carrying this gloss --
    // otherwise half the doublets would grade a correct answer wrong.
    const same = entries.filter(function(x){ return ELEMENT_POS[x.pos] && x.pos === e.pos && x.en === e.en; });
    let accept = [];
    same.forEach(function(x){ accept = accept.concat(formVariants(x.term)); });
    return { type: mode, entryId: e.id, prompt: e.en,
             promptLabel: "Which " + e.pos + "?",
             answerLabel: e.pos.charAt(0).toUpperCase() + e.pos.slice(1),
             target: e.term,
             rawTarget: same.map(function(x){ return x.term; }).join(" / "),
             acceptableAnswers: accept };
  }

  if (mode === "term_meaning") {
    buildPool(e => e.pos === "term" && e.en);
    if (pool.length === 0) return null;
    const e = weightedPick(pool, weights);
    return { type: mode, entryId: e.id, prompt: e.term,
             promptLabel: "What does this term mean?",
             answerLabel: "Meaning", target: e.en, rawTarget: e.en,
             acceptableAnswers: glossVariants(e.en) };
  }

  if (mode === "build") {
    buildPool(e => e.pos === "term" && e.parts && e.parts.length);
    if (pool.length === 0) return null;
    const e = weightedPick(pool, weights);
    return { type: mode, entryId: e.id, prompt: e.en,
             subPrompt: e.parts.length + " elements",
             promptLabel: "Build the term",
             answerLabel: "Term", target: e.term, rawTarget: e.term };
  }

  if (mode === "analyse") {
    buildPool(e => e.pos === "term" && e.parts && e.parts.length > 1);
    if (pool.length === 0) return null;
    const e = weightedPick(pool, weights);
    const i = Math.floor(Math.random() * e.parts.length);
    return { type: mode, entryId: e.id, prompt: e.term,
             subPrompt: "Which element here means “" + e.part_glosses[i] + "”?",
             promptLabel: "Break it down",
             answerLabel: "Element",
             target: e.parts[i], rawTarget: e.parts[i],
             acceptableAnswers: formVariants(e.parts[i]) };
  }

  if (mode === "doublet") {
    buildPool(e => e.counterpart);
    if (pool.length === 0) return null;
    const e = weightedPick(pool, weights);
    const want = e.origin === "Greek" ? "Latin" : "Greek";
    return { type: mode, entryId: e.id,
             prompt: e.term + "   (" + e.origin + ")",
             subPrompt: "Both mean “" + e.counterpart_gloss + "”. Give the " + want + " form.",
             promptLabel: "Greek ↔ Latin",
             answerLabel: want + " form",
             target: e.counterpart, rawTarget: e.counterpart,
             acceptableAnswers: formVariants(e.counterpart) };
  }

  if (mode === "plural") {
    buildPool(e => e.pos === "plural" && e.plural);
    if (pool.length === 0) return null;
    const e = weightedPick(pool, weights);
    if (Math.random() < 0.75) {
      return { type: mode, entryId: e.id, prompt: e.term, subPrompt: e.en,
               promptLabel: "Give the plural", answerLabel: "Plural",
               target: e.plural, rawTarget: e.plural };
    }
    return { type: mode, entryId: e.id, prompt: e.plural, subPrompt: e.en,
             promptLabel: "Give the singular", answerLabel: "Singular",
             target: e.term, rawTarget: e.term };
  }

  if (mode === "confusable") {
    buildPool(e => e.pos === "confusable" && e.pair_term);
    if (pool.length === 0) return null;
    const e = weightedPick(pool, weights);
    const useA = Math.random() < 0.5;
    // Deliberately a two-way forced choice. Padding it out with terms from
    // other pairs made the options incoherent (a root against two suffixes),
    // and the whole point of this drill is discriminating THIS pair.
    const correct = useA ? e.term : e.pair_term;
    const other   = useA ? e.pair_term : e.term;
    const gloss   = useA ? e.en : e.pair_gloss;
    const otherGloss = useA ? e.pair_gloss : e.en;
    const choices = shuffle([{ text: correct, trans: gloss },
                             { text: other, trans: otherGloss }]);
    return { type: mode, entryId: e.id, prompt: gloss,
             promptLabel: "Which of the two means this?",
             answerLabel: "Term",
             rawTarget: correct, correct: correct, choices: choices };
  }

  if (mode === "abbreviation") {
    buildPool(e => e.pos === "abbreviation" && e.latin);
    if (pool.length === 0) return null;
    const e = weightedPick(pool, weights);
    if (Math.random() < 0.6) {
      // The Latin is deliberately withheld here -- it would give the answer away.
      return { type: mode, entryId: e.id, prompt: e.term,
               promptLabel: "What does this direction mean?",
               answerLabel: "Meaning", target: e.en, rawTarget: e.en,
               acceptableAnswers: glossVariants(e.en) };
    }
    return { type: mode, entryId: e.id, prompt: e.latin,
             subPrompt: "“" + e.en + "”",
             promptLabel: "Give the abbreviation",
             answerLabel: "Abbreviation", target: e.term, rawTarget: e.term,
             acceptableAnswers: [e.term, e.term.replace(/\./g, "")] };
  }

  if (mode === "multiple_choice") {
    buildPool(e => e.term && e.en && e.pos !== "confusable");
    if (pool.length === 0) return null;
    const e = weightedPick(pool, weights);
    const termToMeaning = Math.random() < 0.5;
    const field = termToMeaning ? "en" : "term";
    const back  = termToMeaning ? "term" : "en";
    const correct = e[field];
    const taken = {}; taken[correct] = 1;
    const distractors = [];
    const fillFrom = function(arr) {
      const sh = shuffle(arr);
      for (let i = 0; i < sh.length && distractors.length < 3; i++) {
        const val = sh[i][field];
        if (val && !taken[val]) { taken[val] = 1; distractors.push({ text: val, trans: sh[i][back] }); }
      }
    };
    // Same kind of element first, so the distractors are genuinely plausible.
    fillFrom(entries.filter(function(x){ return x.pos === e.pos && x.id !== e.id && x[field]; }));
    if (distractors.length < 3) fillFrom(entries.filter(function(x){ return x.id !== e.id && x[field]; }));
    const choices = shuffle([{ text: correct, trans: e[back] }].concat(distractors));
    return { type: mode, entryId: e.id,
             prompt: e[termToMeaning ? "term" : "en"],
             promptLabel: termToMeaning ? "Choose the meaning" : "Choose the term",
             answerLabel: termToMeaning ? "Meaning" : "Term",
             rawTarget: correct, correct: correct, choices: choices };
  }

  if (mode === "cloze") {
    buildPool(e => e.cloze && e.cloze.length);
    if (pool.length === 0) return null;
    const e = weightedPick(pool, weights);
    const arr = Array.isArray(e.cloze) ? e.cloze : [e.cloze];
    const c = arr[Math.floor(Math.random() * arr.length)];
    const m = c.sent.match(/\{([^}]*)\}/);
    const answer = m ? m[1] : "";
    return { type: mode, entryId: e.id,
             prompt: c.sent.replace(/\{[^}]*\}/, "_____"),
             subPrompt: "Fill the gap with the correct term.",
             hint: e.en,
             // the other clinical words in THIS sentence, so the explanation
             // does not itself need explaining
             clozeTerms: c.terms || null,
             promptLabel: "Clinical context",
             answerLabel: "Term", target: answer, rawTarget: answer };
  }

  return null;
}'''

SELECTION = '''function selectionCanAsk(e) {
  if ((enabledModes.element_meaning || enabledModes.meaning_element) && ELEMENT_POS[e.pos] && e.en) return true;
  if ((enabledModes.term_meaning) && e.pos === "term" && e.en) return true;
  if (enabledModes.build && e.pos === "term" && e.parts) return true;
  if (enabledModes.analyse && e.parts && e.parts.length > 1) return true;
  if (enabledModes.doublet && e.counterpart) return true;
  if (enabledModes.plural && e.plural) return true;
  if (enabledModes.confusable && e.pos === "confusable" && e.pair_term) return true;
  if (enabledModes.abbreviation && e.pos === "abbreviation" && e.latin) return true;
  if (enabledModes.multiple_choice && e.term && e.en && e.pos !== "confusable") return true;
  if (enabledModes.cloze && e.cloze) return true;
  return false;
}'''

# The extras panel: for medicine the valuable reveal is the etymology and the
# element breakdown, not a paradigm table. Reuses the conj-* CSS classes.
EXTRAS = r'''function buildElementSection() {
  if (!currentQ || !feedback) return null;
  const e = byId[currentQ.entryId];
  if (!e) return null;

  const wrap = document.createElement("div");
  wrap.className = "conj-section";
  const btn = document.createElement("button");
  btn.type = "button"; btn.className = "conj-toggle";
  btn.textContent = "Show breakdown";
  const tbl = document.createElement("div");
  tbl.className = "conj-table";
  let any = false;

  const heading = function(text) {
    const h = document.createElement("div");
    h.className = "conj-label"; h.textContent = text;
    tbl.appendChild(h); any = true;
  };
  const pairRow = function(left, right) {
    const row = document.createElement("div"); row.className = "conj-row";
    const l = document.createElement("span"); l.className = "cp"; l.textContent = left;
    const r = document.createElement("span"); r.style.whiteSpace = "pre-wrap"; r.textContent = right;
    row.appendChild(l); row.appendChild(r); tbl.appendChild(row); any = true;
  };
  const noteRow = function(text) {
    const row = document.createElement("div"); row.className = "conj-row";
    const s = document.createElement("span"); s.style.whiteSpace = "pre-wrap"; s.textContent = text;
    row.appendChild(s); tbl.appendChild(row); any = true;
  };

  // Which language each element comes from is the substance of this deck, so it
  // is labelled on every element, not just on the word as a whole.
  if (e.parts && e.part_glosses) {
    heading("Elements");
    e.parts.forEach(function(p, i) {
      const org = (e.part_origins && e.part_origins[i]) || "";
      pairRow(p, e.part_glosses[i] + (org ? "   — " + org : ""));
    });
  }

  if (e.origin) {
    const hybrid = String(e.origin).indexOf("Hybrid") === 0;
    heading(e.parts ? "Word origin" : "Origin");
    if (e.parts && !hybrid) {
      noteRow(e.origin + " throughout");
    } else if (hybrid) {
      // Name which side is which: a Latin stem under a Greek ending is the
      // usual shape, and it is why such terms look irregular beside their
      // Greek-throughout neighbours.
      const orgs = e.part_origins || [];
      const last = orgs[orgs.length - 1], rest = orgs.slice(0, -1);
      let how = "Greek and Latin elements in one word.";
      if (last === "Greek" && rest.indexOf("Latin") >= 0) {
        how = "A Latin stem with a Greek ending — the usual shape.";
      } else if (last === "Latin" && rest.indexOf("Greek") >= 0) {
        how = "A Greek stem with a Latin ending.";
      }
      noteRow(e.origin + "\n" + how);
    } else {
      noteRow(e.origin);
    }
  }

  if (e.counterpart) {
    heading((e.origin === "Greek" ? "Latin" : "Greek") + " counterpart");
    pairRow(e.counterpart, e.counterpart_gloss);
  }
  if (e.plural) {
    heading("Plural");
    pairRow(e.term + " → " + e.plural, e.plural_rule);
  }
  if (e.pair_term) {
    heading("Do not confuse with");
    pairRow(e.pair_term, e.pair_gloss);
  }
  if (e.latin) { heading("Latin"); noteRow(e.latin); }
  if (e.note) { heading("Notes"); noteRow(e.note); }
  // The notes illustrate an element with real words ("appendectomy,
  // nephrectomy"). Spell out what those mean rather than leaving the learner to
  // guess; the generator resolves every one and fails the build if it cannot.
  if (e.note_terms && e.note_terms.length) {
    heading("Terms used above");
    e.note_terms.forEach(function(t) { pairRow(t[0], t[1]); });
  }
  // A cloze sentence is real clinical prose and uses words beyond the answer;
  // these belong to the sentence just asked, not to the entry.
  if (currentQ.clozeTerms && currentQ.clozeTerms.length) {
    heading("Other terms in this sentence");
    currentQ.clozeTerms.forEach(function(t) { pairRow(t[0], t[1]); });
  }
  if (!any) return null;

  btn.addEventListener("click", function() {
    const open = tbl.className.indexOf("open") >= 0;
    tbl.className = open ? "conj-table" : "conj-table open";
    btn.textContent = (open ? "Show" : "Hide") + " breakdown";
  });
  wrap.appendChild(btn);
  wrap.appendChild(tbl);
  return wrap;
}'''


def cut(text, start_marker, end_marker, what):
    """Replace the block from start_marker up to (not including) end_marker."""
    i = text.index(start_marker)
    j = text.index(end_marker, i)
    return i, j


def main():
    src = open(SRC, encoding="utf-8").read()

    # ---- data blob: swap the Latin deck for a placeholder rebuild.py will fill
    m = re.search(r"const VOCAB_DATA = .*?;\n", src, re.S)
    assert m, "could not find the VOCAB_DATA line"
    src = src[:m.start()] + 'const VOCAB_DATA = {"entries":[],"lessons":[]};\n' + src[m.end():]

    def swap(start, end, new, label):
        nonlocal src
        i = src.index(start)
        j = src.index(end, i + len(start))
        src = src[:i] + new + "\n\n" + src[j:]
        print("  replaced", label)

    # ---- drill modes
    swap("const MODE_LABELS = [", "// === QUESTION GENERATORS ===", MODE_LABELS, "MODE_LABELS")
    swap("// === QUESTION GENERATORS ===", "function checkAnswer(q, input)", GENERATE, "generateQuestion")
    swap("function selectionCanAsk(e) {", "function renderSelectionCount()", SELECTION, "selectionCanAsk")
    swap("function buildConjSection() {", "function buildEndRow()", EXTRAS, "extras panel")

    # ---- everything that still points at the old panel or the old modes
    src = src.replace("buildConjSection()", "buildElementSection()")
    src = src.replace(
        'const conj = buildElementSection();', 'const conj = buildElementSection();')

    # default-on modes
    old_modes = re.search(r"let enabledModes = \{.*?\};", src, re.S)
    assert old_modes, "could not find enabledModes"
    src = src[:old_modes.start()] + (
        "let enabledModes = {\n"
        "  element_meaning: true, meaning_element: true, term_meaning: true,\n"
        "  build: true, analyse: true, doublet: true, plural: true,\n"
        "  confusable: true, abbreviation: true, multiple_choice: true, cloze: true,\n"
        "};") + src[old_modes.end():]

    # element-kind labels for the Word-forms filter
    old_pos = re.search(r"const POS_LABELS = \{.*?\};", src, re.S)
    assert old_pos, "could not find POS_LABELS"
    src = src[:old_pos.start()] + (
        'const POS_LABELS = { prefix:"Prefixes", suffix:"Suffixes", root:"Roots",\n'
        '  term:"Built terms", plural:"Plurals", confusable:"Confusable pairs",\n'
        '  anatomical:"Anatomical terms", abbreviation:"Prescription Latin" };'
    ) + src[old_pos.end():]

    # ---- deck-summary plurals: the fallback p + "s" gave "suffixs"/"prefixs"
    old_plural = ('const PLURAL = { noun:"nouns", verb:"verbs", adjective:"adjectives", adverb:"adverbs",\n'
                  '    pronoun:"pronouns", number:"numbers", phrase:"phrases", preposition:"prepositions", conjunction:"conjunctions" };')
    new_plural = ('const PLURAL = { root:"roots", term:"terms", suffix:"suffixes", prefix:"prefixes",\n'
                  '    plural:"plurals", confusable:"confusable pairs", anatomical:"anatomical terms",\n'
                  '    abbreviation:"abbreviations" };')
    assert src.count(old_plural) == 1, "deck-summary PLURAL map not found"
    src = src.replace(old_plural, new_plural)

    # ---- the slash is notation here, not a separator
    # In the Latin/Polish decks "a / b" lists alternative answers, so gradeAnswer
    # splits the target on both comma and slash. A combining form IS spelled with
    # a slash (cardi/o), so that split tore every root in half and graded a
    # perfectly typed answer as a typo. Split on comma only; the modes supply
    # their alternatives through acceptableAnswers instead.
    old_split = "const alts = [target.trim()].concat(target.split(/[,/]/).map(a => a.trim())).filter(Boolean);"
    new_split = "const alts = [target.trim()].concat(target.split(/,/).map(a => a.trim())).filter(Boolean);"
    assert src.count(old_split) == 1, "gradeAnswer alt-splitting not found"
    src = src.replace(old_split, new_split)

    # ---- branding, storage keys, service worker
    for a, b in [
        ("<title>Lingua Latina — Latin / English trainer</title>",
         "<title>Terminologia Medica — Latin &amp; Greek for medicine</title>"),
        ('href="./latin-trainer-manifest.json"', 'href="./medical-trainer-manifest.json"'),
        ('href="./icons/latin-trainer-icon-192.png"', 'href="./icons/medical-trainer-icon-192.png"'),
        ('content="Latin Trainer"', 'content="Med Terms"'),
        ('<h1>Lingua Latina<span class="accent">·</span><span class="subtitle">latina / english</span></h1>',
         '<h1>Terminologia<span class="accent">·</span><span class="subtitle">medical latin &amp; greek</span></h1>'),
        ("latin_trainer_progress", "medical_trainer_progress"),
        ("latin_trainer_lessons", "medical_trainer_lessons"),
        ("latin_trainer_pos", "medical_trainer_pos"),
        ("'./latin-trainer-sw.js', { scope: './latin_trainer.html' }",
         "'./medical-trainer-sw.js', { scope: './medical_trainer.html' }"),
    ]:
        assert src.count(a) >= 1, f"branding string not found: {a[:60]}"
        src = src.replace(a, b)

    # The Latin macron machinery is inert here (no diacritics in the deck) but
    # harmless; the filler list still helps glosses like "the study of the liver".
    open(DST, "w", encoding="utf-8").write(src)
    print(f"wrote {DST}")


if __name__ == "__main__":
    main()
