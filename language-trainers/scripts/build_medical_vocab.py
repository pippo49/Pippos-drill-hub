#!/usr/bin/env python3
"""Generate vocab_med.json for the medical terminology trainer.

Run from the language-trainers directory:

    python3 scripts/build_medical_vocab.py
    python3 scripts/rebuild.py medical_trainer.html vocab_med.json
    python3 scripts/validate.py medical_trainer.html

Like the Latin and Italian generators, this one is assert-guarded so bad data
fails the build instead of shipping. The checks that matter:

1. Every element form is unique. A duplicate would make the meaning→element
   drill unanswerable (two right answers, one accepted).
2. Every part named in TERMS exists in the element tables — no invented roots.
3. Every term can actually be SPELLED by its parts, in order (segment_ok).
   This is the medical equivalent of the Latin paradigm cross-check: it catches
   a wrong root, a wrong order, or a typo on either side.
4. Both halves of every doublet exist, and the two sides disagree about origin
   (a Greek/Latin pair where both are Greek is a data error).
5. Every cloze sentence contains exactly one {braced} span, and the braced text
   matches an entry that exists.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from med_elements import PREFIXES, SUFFIXES, ROOTS, DOUBLETS
from med_terms import (EXTRA_ROOTS, EXTRA_SUFFIXES, TERMS, PLURALS,
                       CONFUSABLES, ANATOMICAL, PRESCRIPTION, CLOZE, CLOZE_ONLY)
from med_examples import (EXAMPLE_GLOSSARY, NOT_TERMS, CLINICAL_GLOSSARY,
                          ORDINARY_WORDS)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vocab_med.json")
VOWELS = "aeiou"
ORIGIN = {"G": "Greek", "L": "Latin", "G/L": "Greek/Latin"}


# ----------------------------------------------------------------- checking

def variants(part):
    """Every spelling this element may contribute inside a built term.

    A root may keep its combining vowel (cardi/o -> cardio), drop it (cardi), or
    additionally lose a final stem vowel where the next element begins with one.
    A prefix may elide its final vowel the same way (hypo- + ox- -> hypoxia).
    Suffixes contribute exactly their letters.
    """
    out = set()
    if part.endswith("-"):                      # prefix
        base = part[:-1]
        out.add(base)
        if len(base) > 1 and base[-1] in VOWELS:
            out.add(base[:-1])
    elif part.startswith("-"):                  # suffix
        out.add(part[1:])
    elif "/" in part:                           # root with combining vowel
        base, cv = part.split("/", 1)
        out.add(base + cv)
        out.add(base)
        if len(base) > 1 and base[-1] in VOWELS:
            out.add(base[:-1])
    else:
        out.add(part)
    return {v for v in out if v}


def segment_ok(term, parts):
    """Can `parts`, in order, spell `term`? Backtracks over each part's variants."""
    t = term.replace(" ", "").replace("-", "").lower()

    def go(i, pos):
        if i == len(parts):
            return pos == len(t)
        for v in sorted(variants(parts[i]), key=len, reverse=True):
            if t.startswith(v, pos) and go(i + 1, pos + len(v)):
                return True
        return False

    return go(0, 0)


# ----------------------------------------------------------------- assembly

def main():
    elements = []          # (form, meaning, origin, lesson, note, kind)
    for form, mean, org, lesson, note in PREFIXES:
        elements.append((form, mean, org, lesson, note, "prefix"))
    for form, mean, org, lesson, note in SUFFIXES + EXTRA_SUFFIXES:
        elements.append((form, mean, org, lesson, note, "suffix"))
    for form, mean, org, lesson, note in ROOTS + EXTRA_ROOTS:
        elements.append((form, mean, org, lesson, note, "root"))

    # 1. unique forms
    seen = {}
    for form, *_ in elements:
        assert form not in seen, (
            f"duplicate element form {form!r} — two entries would make the "
            f"meaning->element drill ambiguous")
        seen[form] = True

    by_form = {e[0]: e for e in elements}
    entries, n = [], 0

    def add(**kw):
        nonlocal n
        n += 1
        kw["id"] = "med%04d" % n
        entries.append(kw)
        return kw["id"]

    id_of_form = {}
    for form, mean, org, lesson, note, kind in elements:
        id_of_form[form] = add(term=form, en=mean, pos=kind, lesson=lesson,
                               origin=ORIGIN[org], note=note)

    # 2 + 3. terms: parts must exist, and must be able to spell the term
    id_of_term = {}
    for term, mean, parts, lesson in TERMS:
        for p in parts:
            assert p in by_form, f"{term}: part {p!r} is not a defined element"
        assert segment_ok(term, parts), (
            f"{term}: parts {parts} cannot spell it — wrong root, wrong order, "
            f"or a typo on one side")
        codes = [by_form[p][2] for p in parts]
        kinds = {c for c in codes if c in ("G", "L")}
        # A term built from Greek and Latin elements is a hybrid, and saying so
        # is a real teaching point: appendicitis is Latin appendic- with a Greek
        # -itis, which is why it looks irregular next to Greek-throughout words.
        if kinds == {"G"}:
            term_origin = "Greek"
        elif kinds == {"L"}:
            term_origin = "Latin"
        elif kinds == {"G", "L"}:
            term_origin = "Hybrid — Greek + Latin"
        else:
            term_origin = "Greek/Latin"
        id_of_term[term] = add(term=term, en=mean, pos="term", lesson=lesson,
                               origin=term_origin, parts=parts,
                               part_glosses=[by_form[p][1] for p in parts],
                               part_origins=[ORIGIN[c] for c in codes])
        # No `note` here on purpose: the extras panel already renders the parts
        # and their glosses as its own row, so a note repeating them just
        # duplicated the same text twice in the same panel.

    for term, mean, lesson, note, term_origin in CLOZE_ONLY:
        id_of_term[term] = add(term=term, en=mean, pos="term", lesson=lesson,
                               origin=term_origin, note=note)

    # 4. doublets, linked both ways
    for gk, la, gloss in DOUBLETS:
        for f in (gk, la):
            assert f in by_form, f"doublet {gk}/{la}: {f!r} is not a defined root"
        assert by_form[gk][2] == "G" and by_form[la][2] == "L", (
            f"doublet {gk}/{la}: expected a Greek form then a Latin one, got "
            f"{by_form[gk][2]}/{by_form[la][2]}")
        g_entry = entries[int(id_of_form[gk][3:]) - 1]
        l_entry = entries[int(id_of_form[la][3:]) - 1]
        g_entry["counterpart"] = la
        g_entry["counterpart_gloss"] = gloss
        l_entry["counterpart"] = gk
        l_entry["counterpart_gloss"] = gloss

    for sing, plur, rule, mean in PLURALS:
        add(term=sing, en=mean, pos="plural", lesson="Plurals & word forms",
            origin="Greek" if "Greek" in rule else "Latin",
            plural=plur, plural_rule=rule,
            note=f"{sing} → {plur}.  Rule: {rule}.")

    for a, ga, b, gb, note, lesson in CONFUSABLES:
        add(term=a, en=ga, pos="confusable", lesson=lesson, origin="Greek/Latin",
            pair_term=b, pair_gloss=gb, note=note)

    for term, mean, org, note in ANATOMICAL:
        add(term=term, en=mean, pos="anatomical",
            lesson="Anatomical position & planes", origin=ORIGIN[org], note=note)

    for abbr, latin, mean in PRESCRIPTION:
        add(term=abbr, en=mean, pos="abbreviation",
            lesson="Prescription Latin & abbreviations", origin="Latin",
            latin=latin, note=f"{abbr} = {latin} — {mean}.")

    # 5. cloze sentences attach to the entry they blank
    by_term = {}
    for e in entries:
        by_term.setdefault(e["term"], e)
    attached = 0
    for target, sentence in CLOZE:
        braces = re.findall(r"\{([^}]*)\}", sentence)
        assert len(braces) == 1, f"cloze for {target!r}: expected one {{...}}, got {braces}"
        assert braces[0] == target, (
            f"cloze for {target!r}: the braced word is {braces[0]!r}")
        assert target in by_term, f"cloze target {target!r} has no entry"
        by_term[target].setdefault("cloze", []).append({"sent": sentence})
        attached += 1

    # 6. notes illustrate an element with real words ("appendectomy,
    # nephrectomy"). Resolve each cited term to a gloss so the panel can show
    # what they mean, and FAIL if one cannot be resolved -- otherwise a future
    # note could quietly cite a term the learner has no way to look up.
    gloss = {}
    def index(key, meaning):
        k = key.lower().strip()
        if k and k not in gloss:
            gloss[k] = meaning
    for e in entries:
        index(e["term"], e["en"])
        if e.get("plural"):
            index(e["plural"], "plural of " + e["term"] + " — " + e["en"])
        if e.get("pair_term"):
            index(e["pair_term"], e.get("pair_gloss", ""))
    for k, v in EXAMPLE_GLOSSARY.items():
        index(k, v)

    def spell(w):
        """The notes use British spelling, the deck American; try both."""
        return {w, w.replace("ae", "e").replace("oe", "e")}

    def look_up(w):
        for base in spell(w):
            for cand in (base, "-" + base, base + "/o", base + "/e", base + "/i"):
                if cand in gloss:
                    return gloss[cand]
        return None

    # A Latin or Greek headword is often cited with its genitive -- "L caput,
    # capitis", "L os, ossis" -- so capture the whole comma- or slash-separated
    # run, not just the first word. Without this, "capitis" looked like an
    # -itis term to the pattern below and was reported as an unexplained
    # citation, which it is not: the sentence around it is the explanation.
    ETYMON = re.compile(
        r"\b(?:Gk|L|Latin|Greek|from)\s+([A-Za-zÀ-ÿ/]+(?:\s*,\s*[A-Za-zÀ-ÿ/]+)*)")
    MEDICAL = re.compile(
        r"(itis|ectomy|ostomy|otomy|plasty|pexy|desis|centesis|scopy|scope|graphy|"
        r"gram|metry|meter|logy|logist|pathy|algia|emia|uria|penia|megaly|malacia|"
        r"sclerosis|stenosis|ectasis|ptosis|rrhea|rrhagia|cele|oma|plegia|paresis|"
        r"phobia|lith|iasis|emesis|pnea|phagia|phasia|plasia|trophy|genesis|cyte|"
        r"blast|clast|poiesis|esthesia|kinesia|osis|ism|ia)$")
    unexplained, cited_total = set(), 0
    for e in entries:
        note = e.get("note") or ""
        if not note:
            continue
        etyma = set()
        for m in ETYMON.finditer(note):
            etyma |= {w for w in re.split(r"[,/\s]+", m.group(1).lower()) if w}
        seen, pairs = set(), []
        for w in re.findall(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'-]{4,}", note):
            lw = w.lower().strip("'-")
            if lw in seen or lw in etyma or lw in NOT_TERMS:
                continue
            if not MEDICAL.search(lw):
                continue
            seen.add(lw)
            g = look_up(lw)
            if g is None:
                unexplained.add(lw)
            elif lw != e["term"].lower():   # don't re-gloss the headword itself
                pairs.append([w.strip("'-"), g])
        if pairs:
            e["note_terms"] = pairs
            cited_total += len(pairs)

    assert not unexplained, (
        "these terms are cited in a note but have no gloss anywhere -- add them "
        "to EXAMPLE_GLOSSARY (or NOT_TERMS if they are ordinary English or an "
        f"etymon), or reword the note: {sorted(unexplained)}")

    # 7. a cloze sentence is real clinical prose, so it uses clinical words the
    # learner may not know either. Attach the ones we can explain to that
    # sentence. Matching is phrase-first ("iliac fossa" beats a bare "fossa")
    # and word-bounded, so "media" does not match inside "immediate".
    clinical = dict(CLINICAL_GLOSSARY)
    for k, v in gloss.items():
        if k.startswith("-") or "/" in k:
            continue                      # elements are not words in a sentence
        clinical.setdefault(k, v)
    keys = sorted(clinical, key=len, reverse=True)
    patterns = [(k, re.compile(r"(?<![A-Za-z])" + re.escape(k) + r"(?![A-Za-z])", re.I))
                for k in keys]

    cloze_terms_total = 0
    for e in entries:
        for c in e.get("cloze") or []:
            answer = re.search(r"\{([^}]*)\}", c["sent"]).group(1).lower()
            plain = re.sub(r"\{[^}]*\}", " ", c["sent"])
            found, used = [], []
            for k, pat in patterns:
                m = pat.search(plain)
                if not m or k == answer:
                    continue
                lo, hi = m.span()
                if any(lo < b and a < hi for a, b in used):
                    continue              # already covered by a longer phrase
                used.append((lo, hi))
                found.append([m.group(0), clinical[k]])
            if found:
                found.sort(key=lambda t: plain.lower().index(t[0].lower()))
                c["terms"] = found
                cloze_terms_total += len(found)

    # 8. closed vocabulary over the cloze sentences. Clinical prose words cannot
    # be spotted by a suffix the way -itis can, so instead of guessing a pattern
    # every word must be CLASSIFIED: glossed, or listed as ordinary English. A
    # new sentence therefore cannot introduce an unexplained clinical term —
    # the build stops until someone decides which of the two it is.
    covered = set(ORDINARY_WORDS)
    for k in clinical:
        covered.add(k)                       # the key as written ("x-ray")
        for w in re.split(r"[\s-]+", k):     # and its parts ("iliac", "fossa")
            if w:
                covered.add(w)
    unclassified = {}
    for e in entries:
        for c in e.get("cloze") or []:
            plain = re.sub(r"\{[^}]*\}", " ", c["sent"])
            for w in re.findall(r"[A-Za-z][A-Za-z'-]*", plain):
                lw = w.lower().strip("'-")
                if lw and lw not in covered:
                    unclassified.setdefault(lw, c["sent"])
    assert not unclassified, (
        "cloze sentences use words that are neither glossed nor marked ordinary. "
        "Add each to CLINICAL_GLOSSARY if a learner would need it explained, or "
        "to ORDINARY_WORDS if it is everyday English:\n  "
        + "\n  ".join(f"{w!r}  in: {sent}" for w, sent in sorted(unclassified.items())))

    lessons = sorted({e["lesson"] for e in entries})
    data = {"entries": entries, "lessons": lessons}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))

    kinds = {}
    for e in entries:
        kinds[e["pos"]] = kinds.get(e["pos"], 0) + 1
    print(f"vocab_med.json: {len(entries)} entries across {len(lessons)} lessons")
    print("  " + " · ".join(f"{k} {v}" for k, v in sorted(kinds.items())))
    origins = {}
    for e in entries:
        if e["pos"] == "term":
            origins[e["origin"]] = origins.get(e["origin"], 0) + 1
    print(f"  {len(DOUBLETS)} Greek/Latin doublets · {attached} cloze sentences")
    print("  term origins: " + " · ".join(f"{k} {v}" for k, v in sorted(origins.items())))
    n_notes = sum(1 for e in entries if e.get("note_terms"))
    print(f"  {cited_total} cited terms glossed across {n_notes} notes")
    n_cl = sum(1 for e in entries for c in (e.get("cloze") or []) if c.get("terms"))
    print(f"  {cloze_terms_total} clinical terms glossed across {n_cl} cloze sentences")


if __name__ == "__main__":
    main()
