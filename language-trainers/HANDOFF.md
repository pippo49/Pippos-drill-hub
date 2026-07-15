# Polish trainer — handoff for new chat

I'm continuing work on my self-contained Polish→German vocabulary trainer (single HTML file, PWA on GitHub Pages, used on iPhone). I'm learning Polish with German as the reference language. **Attach the latest `polish_trainer.html` and `vocab.json`** with this message (filenames may have a suffix like `_2` — adjust the paths below to whatever is actually uploaded). Keep responses concise — I'm token-conscious and will spot-check/correct errors myself.

## First step in the new session (rebuild your working files)
The container resets between chats, so reconstruct the editable pieces from the uploaded build before changing anything (adjust the upload filenames if they differ):
```python
import json
html=open('/mnt/user-data/uploads/polish_trainer.html',encoding='utf-8').read()
key='const VOCAB_DATA = '; i=html.index(key)+len(key); rest=html[i:]
obj,end=json.JSONDecoder().raw_decode(rest, rest.index('{'))
open('head.html','w',encoding='utf-8').write(html[:i])      # everything up to the data
open('tail.html','w',encoding='utf-8').write(rest[end:])    # the JS after the data (starts with ';')
import shutil; shutil.copy('/mnt/user-data/uploads/vocab.json','vocab_v3.json')
```

## Rebuild + validate procedure (ALWAYS do after any edit)
1. `data_compact.json` = `json.dumps(json.load(open('vocab_v3.json')),ensure_ascii=False,separators=(',',':'))`
2. `cat head.html data_compact.json tail.html > /mnt/user-data/outputs/polish_trainer.html`
3. `cp vocab_v3.json /mnt/user-data/outputs/vocab.json`
4. Extract JS: `html.split('<script>',1)[1].rsplit('</script>',1)[0]` → `check.js`; run `node --check check.js`.
5. Runtime probe with a DOM stub (recreate a minimal `document`/`window`/`localStorage` stub, prepend to `check.js`, then call `generateQuestion("<mode>")` in a loop to verify pools/forms). Then `present_files`.

## Data schema (`vocab.json` = `{entries:[...], meta:{}}`)
Entry: `pl, de, pos, id, lesson`.
- Verbs: `conjugation{ja,ty,on_ona_ono,my,wy,oni_one}`, `aspect`, `conjugation_label?`.
- Adjectives: `declension{m_sg_nom,f_sg_nom,n_sg_nom,nv_pl_nom}`, `decl_table?`.
- Nouns: `gender (m/f/n/pl-only)`, `animate?`, `plural`, and **`noun_decl{acc_sg, gen_sg, nom_pl, acc_pl, gen_pl}`** (drives the Noun cases drill; Nom sg = the headword, not stored). A noun may store a *partial* `noun_decl` (e.g. mass nouns like `mleko` have only `acc_sg`/`gen_sg`); the drill only asks the keys that are present, so omit unnatural plural slots rather than inventing them.
- **Cloze**: `cloze` = array of `{pl, de}`; the target word in `pl` is wrapped in `{...}` (e.g. `"Rano piję {kawę}."`). Answer = the inflected in-sentence form. The cloze answer is authored independently of `noun_decl`, so write the correct inflection even if that entry's `noun_decl` still has an error. Multi-word noun phrases / plural-only nouns have no `noun_decl`.
- Multi-translations live comma/slash-joined in `de`.

## Drill modes (9), all default-on
`pl_de, de_pl, conjugate, decline, noun_case, antonym, synonym, multiple_choice, cloze`.
- Each mode = `[key,label]` in `MODE_LABELS`; gated in `selectionCanAsk`; generated in `generateQuestion`.
- **`aspect_pair` mode was removed** (user preference). Aspect partners are drilled via the **synonym** mode instead: every `aspect_pair` link is mirrored into `synonyms` (both directions), and the synonym drill tags verbs with their aspect — `(pf.)`/`(impf.)` — in the prompt and in the displayed answer (`rawTarget`). Grading still uses the bare words (`acceptableAnswers` untagged). The `aspect_pair` data field remains on entries (harmless, unused by any mode); keep mirroring it into `synonyms` for any new verb pairs.
- `noun_case` picks a random key from `noun_decl` (`Object.keys`); labels in `NOUN_LABELS`.
- **Cloze (current UX — changed):** ONE `Cloze` button in the drill row. It is **hard by default** — each question shows only the German prompt with a **"Show hint"** link beside it that reveals the dictionary-form hint for that word only. State is a per-question flag `clozeHintShown` (NOT persisted); it is reset to `false` at the top of `pickQuestion`, so every new word is hard again automatically. After answering (`feedback` set) the hint reveals anyway. The old persisted hard-mode toggle (`CLOZE_HARD_KEY` / `clozeHard` / the separate "Cloze hard" button) has been removed. The `.hint-link` style lives in the head CSS.
- Grading uses `normalize()` (lowercases, strips punctuation, diacritic-tolerant).

## State of the deck (~2234 entries, 1370 nouns)
- Noun morphology: gender/plural for all single-word nouns; full Nom/Acc/Gen sg+pl paradigm on ~1107 nouns.
- **Cloze DONE for 160 words (~320 sentences).** Coverage prioritised by frequency/concreteness and by lessons currently being learned (most recent batch = lessons 1–8). Most words have 2 sentences mixing cases (acc/gen/nom) and persons (ja/ty/on…).
- **Noun-decl corrections applied (this session, ~40 entries):** fixed the masculine-personal animacy/locative-stem glitch (gen_sg was a locative `-u`, acc_pl was the nominative) on dyrektor, aktor, Europejczyk, duch, kuzyn, Niemiec, mężczyzna, student; masc-inanimate gen_sg `-a` (was `-u`) on adapter, ananas, arbuz, bagażnik, bakłażan, bezpiecznik, biustonosz, grosz, telewizor, ręcznik; feminine `-ia` gen_pl truncation (alergii, baterii, bazylii, biżuterii); vowel alternations (błąd→błędu…, sposób/spokój/postój/głód ó→o, podłoga→podłóg, szkoła→szkół, wiosna→wiosen mobile-e, cukier→cukru mobile-e); adjectival nouns początkująca / początkujący; plus napój gen_pl napojów, południe gen_pl południ, sprzedawca acc_sg sprzedawcę, pościel gender f + pościeli, dzień gen_sg dnia, rok plural→lata/lat, mleko plural slots dropped.

## What's next / pending
1. **Cloze: pause and use it.** At 160 words we hit the planned "stop and drill" mark. Before adding more, USE the trainer to surface data errors. When resuming, prefer (a) words from the lessons actively being learned, and (b) a 3rd/4th sentence (new case/person) on already-covered common words over brand-new rare words. Format = `cloze` array of `{pl,de}`, target in `{}`, answers inflected, ~2 per word. Batch size: I'll say how many per turn (have been doing 30).
2. **Noun genitive spot-check (ongoing, lexical).** I'm verifying entries manually over time. Known systemic bug classes in the remaining data: (a) masculine **inanimate gen_sg -a vs -u** (lexical — many tools/fruits/devices wrongly default to `-u`), (b) masculine **personal nouns mis-flagged `animate:false`** with locative `-u` in gen_sg and nominative in acc_pl, (c) **ó→o** non-alternation, (d) feminine **-ia** gen_pl truncation, (e) gen_pl zero-ending with fleeting-e / o→ó. **Do NOT run a blanket auto-fix script** for these — the rules have real lexical exceptions (native `ziemia→ziem`, `ciocia→cioć`; some ó doesn't alternate). Fix verified entries individually, or produce a *candidate-suspects list* for me to eyeball first.
3. **Deferred enrichment (my call, not auto-done):** split `piec` (v027) into the verb (to bake) + a separate masc noun `piec` (Ofen, gen_sg pieca); add a full adjectival paradigm to `początkujący` (pd0600, currently `noun_decl` empty so it's skipped by the case drill).

## My preferences
Direct, concise, scannable answers; lead with the result. I add new words via photos or notes and you do the enrichment/translation (no Apple Shortcut). I'll correct real-world errors — revise rather than hedge. Only apply grammar corrections you're confident are right; flag the uncertain ones instead of guessing.
