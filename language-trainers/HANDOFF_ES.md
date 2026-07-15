# Spanish trainer — handoff for new chat

Self-contained Spanish→English vocabulary trainer (single HTML file, same engine as my Polish trainer, PWA-ready, used on iPhone). English is the reference/answer language. **Attach `spanish_trainer.html` and `vocab_es.json`** with this message. Keep responses concise — lead with results; I spot-check errors myself.

## First step in a new session (container resets)
```python
import json
html=open('/mnt/user-data/uploads/spanish_trainer.html',encoding='utf-8').read()
key='const VOCAB_DATA = '; i=html.index(key)+len(key); rest=html[i:]
obj,end=json.JSONDecoder().raw_decode(rest, rest.index('{'))
open('es_head.html','w',encoding='utf-8').write(html[:i])
open('es_tail.html','w',encoding='utf-8').write(rest[end:])
import shutil; shutil.copy('/mnt/user-data/uploads/vocab_es.json','vocab_es.json')
```

## Rebuild + validate (ALWAYS after any edit)
1. Compact the JSON (`separators=(',',':')`), `cat es_head.html data_es_compact.json es_tail.html > /mnt/user-data/outputs/spanish_trainer.html`, copy `vocab_es.json` to outputs.
2. Extract JS between `<script>...</script>` → `node --check`.
3. DOM-stub runtime probe: loop `generateQuestion(mode)` for all modes: `es_en, en_es, conjugate, decline, noun_case, antonym, synonym, multiple_choice, cloze, ser_estar, por_para`. Then `present_files`.

## Data schema (`vocab_es.json` = `{entries:[...], meta:{}, special:{}}`)
Entry: `es, en, pos, id (es####), lesson ("1".."15")`.
- **Verbs**: `conjugation{yo, tu, el_ella_usted, nosotros, vosotros, ellos_ellas_ustedes}` — present tense, includes irregulars/stem-changers (curated). Impersonal weather verbs (llover, nevar) have NO conjugation field → skipped by the conjugate drill, work everywhere else.
- **Adjectives**: `declension{m_sg_nom, f_sg, m_pl, f_pl}` (m_sg_nom = headword key, skipped by the drill).
- **Nouns**: `gender (m/f)`, `plural`, `noun_decl{article, plural}` → drives the "Noun forms" drill. `agua` is f but stored article `el`. Plural-only nouns stored invariable; `vacaciones`/`tijeras`/`gafas` use article `las`, `celos`/`deberes` use `los` (gafas `la`→`las` and deberes `el`→`los` fixed in v4.1). Invariables: paraguas, microondas, lavavajillas, tenis, tenis de mesa, celos. Special plurals: jerséis, currículums, champús, caracteres, resúmenes (accent ADDED — examen pattern), paces/timideces (-z→-ces).
- **Cloze**: `cloze` = array of `{es, en}`, target wrapped in `{...}`, answer = in-sentence form (conjugated verb, plural noun, gendered adjective, apocopation `un {buen}/{mal}` ...). Answers may legitimately be forms outside the stored paradigms (e.g. `mal`, `muchas`) — the flag-only cross-check will report these; verify by eye, don't auto-fix.
- `antonyms` / `synonyms` = arrays of entry ids, linked both directions.
- **Homographs are allowed** as separate entries differing in pos (mañana/tarde noun+adverb; sueño noun + soñar verb family). Uniqueness key = (es, pos), NOT es alone.
- **`special`** (NEW, v3): curated sentence banks for the two MC-style drills, NOT lesson-scoped, ids outside es#### space:
  - `special.ser_estar` = 60 × `{id: se###, es (target form in braces), en, wrong (same person/number of the other verb, curated), note (short rule tag)}`. 29/31 ser/estar answer split. Covers profession/identity/origin/material/events/possession/date/time (ser) vs location/temp states/gerund/resulting states/fixed expressions incl. estar a + date, estar equivocado/casado (estar) + meaning-changers (aburrido, listo, rico).
  - `special.por_para` = 60 × `{id: pp###, es, en, note}` (33 por / 27 para). Counterpart choice generated in-engine, case-matched for sentence-initial `{Para}`/`{Por}`. Covers all core uses + fixed expressions (por suerte, por lo general, preguntar por, estudiar para).

## Engine differences vs Polish trainer
Field names `es`/`en`; mode keys `es_en`/`en_es`; localStorage keys `spanish_trainer_progress` / `spanish_trainer_lessons`; grading filler words = `to, me, te, se, nos, os`; no aspect/case machinery. **Accent-insensitive grading**: DIACRITIC_MAP covers á é í ó ú ü ñ (plus Polish/German legacy chars) — accent-less input grades "diacritic" = full credit with a reminder. ñ→n is included by deliberate choice. The header deck meta-line and stats placeholder are **generated at load from VOCAB_DATA** (renderDeckMeta IIFE near the top of the JS) — never hardcode counts in the HTML.

**Special drill modes (v3)**: `ser_estar` and `por_para` reuse the multiple-choice button UI. The MC gates were generalized from `type === "multiple_choice"` to `currentQ.choices` presence (three places: chooseOption guard, renderCard branch, number-key handler). The rule tag (`note`) rides on the correct option as its `trans` gloss — revealed after answering. Repeat-avoid uses recentIds with the bank ids. `selectionExhausted` returns false when only special modes are enabled (banks aren't entries), so no break loop. `progress.stats` records se###/pp### ids harmlessly; `byId` lookups elsewhere are null-guarded.

## State of the deck (v4, July 2026) — POLISH PARITY REACHED
- **1126 entries**: 610 nouns, 233 verbs, 147 adjectives, 71 adverbs, 15 pronouns, 15 prepositions, 14 numbers, 12 phrases, 9 conjunctions. Level A1–A2.
- Growth history: v1 seed 502 → +100 food/restaurant+travel/transport → +100 body/health, clothes/shopping, weather/nature, animals, hobbies → +100 house/furniture, work/school, connectors/position → +100 emotions/character adj., media/communication, quantities/materials → v3 +100 all-noun batch: 28 city/services (L6), 11 appearance (L9), 14 character/personality (L2), 44 abstract A2 (L1), 3 top-ups → **v4 +124 rebalance batch: 62 verbs (L14, incl. -zco: desaparecer/ofrecer/parecer/reconocer/producir; -uyo: construir/incluir; tener/poner compounds: obtener/proponer; stem-changers: comprobar/mostrar/mover/sonar/sugerir; g→j: proteger), 43 adjectives (L15, incl. capaz→capaces, hablador→habladora, invariable gratis), 19 adverbs/phrases (L1/L3)**.
- **Cloze: 190 words × 2 sentences (380)** — batch 5 (v3): 30 high-frequency verbs incl. stem-changers (costar, preferir, seguir, doler; conozco, traigo, oigo, envío). Batch 6 (v4): 30 everyday-routine verbs (estudiar, conducir→conduzco, despertar→despierta, almorzar→almuerzo, repetir→repite, recoger→recojo, gastar, ahorrar...). Both batches zero flags.
- ~60 antonym pairs, synonym links incl. salario↔sueldo.
- Morphology: rule-based generator with curated exceptions. Plural accent-drop rule is scoped to FINAL-syllable stress only (jamón→jamones but túnel→túneles). Watch the reverse case: resumen→resúmenes (accent added).

## Session workflow (proven across 6 expansion + 6 cloze batches)
1. Before authoring a batch: dump the candidate word list, dupe-check against `set(e['es'])` in one shot (typical hit rate 3–18 dupes per 100 — lessons overlap more than expected).
2. Author with curated morphology (REG_AR/REG_ER/REG_IR lambdas + explicit tables for irregulars); assert-guard every insert. **Read the dupe-check output carefully — the fresh list is what survives, not the candidate list** (a `cita` slipped through v3 by misreading).
3. Cloze answers authored independently, then flag-only cross-check vs stored forms.
4. Full-deck validation (id uniqueness, (es,pos) uniqueness, conjugation/declension key sets, article whitelist, antonym/synonym id integrity, single-brace cloze, special-bank integrity) → rebuild → node --check → DOM-stub probe (300/mode, 11 modes) → present_files.

## What's next / pending
1. Deck is at Polish parity (1126) — further expansion only on demand (B1 drift risk; deck is A1–A2).
2. Cloze batch 7+ (116 uncovered verbs after v4 added 62 new ones; also everyday nouns/adjectives).
3. Candidate third special drill: saber/conocer or muy/mucho (same MC pattern — engine already generalized, only a new bank + 3 registrations needed: enabledModes, MODE_LABELS, generateQuestion branch condition).
4. Antonym/synonym links for v3/v4 entries (ancho↔estrecho, justo↔injusto, soltero↔casado, ventaja↔desventaja, éxito↔fracaso...) — none linked yet.
5. Pretérito indefinido as second `conjugation_label` layer (deferred).

## My preferences
Direct, concise, lead with the result; batch sizes as I specify; only apply corrections you're confident in, flag the rest; no blanket auto-sweeps on lexical morphology; always rebuild + validate before presenting files.
