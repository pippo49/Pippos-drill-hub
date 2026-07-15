# My self-study trainer — pattern & working preferences

A portable description of a vocabulary/skill trainer I built with Claude (originally Polish→German) and the way of working that produces good results. Use this to seed a new chat for the same tool or a similar one. I learn the target language with **German as the reference/answer language**.

## What the tool is
A **single self-contained `.html` file** — all HTML, CSS, JS, and the dataset inlined — that runs as a **PWA on GitHub Pages and is used on iPhone (iOS Safari)**. No build step, no framework, no external requests. The vocabulary lives inline as `const VOCAB_DATA = {entries:[...], meta:{}}`, and is also kept as a separate `vocab.json` for editing. (It started in React, then moved to a standalone HTML file specifically to fix iOS compatibility.)

### Hard constraints that matter
- **iOS Safari from `file://`/PWA**: even *referencing* `localStorage` can throw, so feature-test it (`LS_AVAILABLE`) and wrap every storage call in try/catch.
- **No browser-storage assumptions beyond that**: all state is plain JS + guarded `localStorage`.
- **Single file**: editing splits it into `head.html` (everything up to the data) + the compact JSON + `tail.html` (the JS after the data), then concatenates back.

## Architecture (what's inside)
- **State**: `progress` (per-entry stats, persisted under a `_progress` key), `enabledModes`, `enabledLessons`, `currentQ`, `feedback`, `session`, plus a review-round subsystem.
- **Drill modes** (each `[key,label]` in `MODE_LABELS`, generated in `generateQuestion`, gated in `selectionCanAsk`): translation both directions, verb conjugation, adjective declension, noun-case paradigm, antonym/synonym, aspect pairs, multiple choice, and cloze (fill-the-gap with the answer inflected in-sentence).
- **Filtering**: by **lesson** (L1–L15 + extras) and by mode; a live "N words in selection" count.
- **Grading** (`gradeAnswer`): graded, not binary — `exact` / `diacritic` (right letters, missing accents) / `typo` (within an edit-distance tolerance scaled by word length) / `wrong`. Normalisation lowercases, strips punctuation, and is diacritic-tolerant; reflexive particles (`się`/`sich`) are made optional; comma/slash-separated targets are all accepted (best grade wins).
- **Spaced-repetition weighting** (`weightFor`): never-seen words strongly preferred (weight 12); otherwise weight rises with inaccuracy (1→5) and decays with each correct streak; `weightedPick` samples from it. Near-misses (`typo`) hold the streak rather than resetting it.
- **Session / round / review loop**: a round runs until the selection is exhausted, then offers a break and an **end-of-round summary**; missed items feed a **review round that re-drills exactly those questions**. Keyboard-first (Enter submits / advances).
- **Cloze UX (current)**: one Cloze button, **hard by default** (German prompt only), with a per-question **"Show hint"** link that reveals the dictionary form for that word only and resets to hard on the next word. Not a persisted toggle.

## What works well for me (pedagogy)
- **Cloze with the answer inflected inside a real sentence**, ~2 sentences per word mixing cases and persons — this is the highest-value drill once a word is known.
- **Graded answers** (accept missing diacritics / minor typos as partial) rather than pass/fail.
- **Coverage prioritised by what I'm actually learning** (current lessons) and by frequency/concreteness — not the whole deck.
- **Depth over breadth past a point**: once ~150–300 common words have cloze, a 3rd/4th sentence on an existing word beats a first sentence on a rare one.
- Reference/answer language is **German** throughout.

## How I like to work (collaboration preferences)
- **Direct, concise, scannable. Lead with the result.** I'm token-conscious; skip preamble and hedging.
- **Revise, don't hedge.** State the correction confidently when you're sure; **flag uncertainty explicitly** instead of guessing. I will catch and correct real-world errors myself.
- **Only apply grammar/data corrections you're confident are right.** For systemic-looking bugs, prefer a *candidate-suspects list* I can eyeball over a blanket auto-fix script — morphology rules have lexical exceptions, so sweeping scripts introduce new errors.
- **Author new content correctly even when stored data is wrong.** (e.g. cloze answers are written with the correct inflection regardless of any error still in that entry's paradigm fields.)
- **Always rebuild + validate after edits**: recompile the single HTML, `node --check` the extracted JS, and run a DOM-stubbed runtime probe that calls `generateQuestion(mode)` in a loop before handing back files.
- **Continuity via a `HANDOFF.md`** that I attach with the build at the start of each chat (the container resets between chats). It documents the rebuild/validate procedure, the data schema, current state, and what's next.
- I add new words via **photos or notes**; you do the enrichment/translation/inflection.
- Batch large data work in chunks I specify (typically 30 words/turn).

## Data schema (reference)
`entry = {pl, de, pos, id, lesson, ...}` (substitute your languages for pl/de):
- **Verbs**: `conjugation{ja,ty,on_ona_ono,my,wy,oni_one}`, `aspect`.
- **Adjectives**: `declension{m_sg_nom,f_sg_nom,n_sg_nom,nv_pl_nom}`.
- **Nouns**: `gender`, `animate?`, `plural`, `noun_decl{acc_sg,gen_sg,nom_pl,acc_pl,gen_pl}` (nom sg = headword, not stored). Partial `noun_decl` is fine — the case drill only asks the keys present, so omit unnatural slots (e.g. mass nouns).
- **Cloze**: `cloze` = array of `{pl,de}`; target wrapped in `{...}`; answer = the inflected in-sentence form.
- Multiple translations: comma/slash-joined in the reference-language field.
