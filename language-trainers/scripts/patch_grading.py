#!/usr/bin/env python3
"""Apply the answer-acceptance fixes reported against the French trainer.

Four separate complaints, all of them the app marking a correct answer wrong:

1. English contractions. Glosses are written the way people speak ("it's",
   "what's your name?"), so a learner taught formal written English typed
   "it is" / "what is your name" and was graded wrong. Both spellings are
   correct English, so expand contractions on BOTH sides before comparing.

2. French question forms. A French question has three shapes -- rising
   intonation ("tu veux venir ?"), est-ce que, and inversion ("veux-tu venir ?").
   The deck stores one. All three are correct, and the formal written ones were
   being rejected. Derive the other shapes from the stored answer.

3. Adjective agreement. EN->FR asks for an adjective with no gender or number in
   the prompt ("big"), so "grand", "grande", "grands" and "grandes" are all
   correct answers; only the masculine singular headword was accepted.

4. Synonyms. Where the deck curates a synonym link, accept it too.

5. Filler-stripping emptying an answer. Reflexive/article particles are dropped
   from both sides so "sich entschuldigen" and "entschuldigen" match, but when
   the whole answer IS such a particle the target became the empty string and
   graded anything short as correct -- Polish "sie" (pd0773, glossed "man")
   accepted German "sich" as exact. Fall back to the unstripped string.

Scope: 1 and 3 are the same bug in every English-glossed deck, so they go to
Spanish, Italian and French. 2 is French-only. Latin is deliberately excluded
from 3 -- its `declension` spans cases, not just gender agreement, so accepting
every form would accept a genitive plural for "good".

Polish is glossed in German, so 1 does not apply to it; 3, 4 and 5 do. Its
`declension` holds nominative forms only (m/f/n/non-virile), so like Spanish and
unlike Latin it can accept every stored form for a bare gloss. 5 goes to every
app: Polish is the only deck that can trigger it today (no Spanish entry or
cloze target is built only from its FILLER words), but "me"/"te"/"se"/"nos"/"os"
are ordinary Spanish headwords and one added tomorrow would grade nonsense as
exact with no test to catch it. The two Portuguese apps get it by being
regenerated from the patched Spanish trainer, not by being patched.

Re-runnable: each patch checks whether it is already present.

    python3 scripts/patch_grading.py
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LT = os.path.join(HERE, "..")

CONTRACTIONS_JS = '''
// --- English contractions -------------------------------------------------
// The English glosses are written as people speak them ("it's", "what's your
// name?"). A learner taught formal written English types "it is" / "what is
// your name" -- also correct, and it was being marked wrong. Expand both sides
// before comparing so the two spell the same thing.
// The patterns are English-specific by construction and cannot match French
// elision (j'ai, qu'est-ce, l'hotel, t'appelles): every one of them requires a
// recognised English pronoun/auxiliary before the apostrophe, or the n't ending.
const CONTRACTIONS = [
  [/\\bcan't\\b/g, "can not"], [/\\bcannot\\b/g, "can not"],
  [/\\bwon't\\b/g, "will not"], [/\\bshan't\\b/g, "shall not"],
  [/\\b([a-z]+)n't\\b/g, "$1 not"],
  [/\\blet's\\b/g, "let us"],
  [/\\b(it|that|there|what|who|how|where|here|he|she|one)'s\\b/g, "$1 is"],
  [/\\bi'm\\b/g, "i am"],
  [/\\b(you|we|they)'re\\b/g, "$1 are"],
  [/\\b(i|you|we|they|he|she|it)'ll\\b/g, "$1 will"],
  [/\\b(i|you|we|they)'ve\\b/g, "$1 have"],
  [/\\b(i|you|we|they|he|she|it)'d\\b/g, "$1 would"],
];
const expandContractions = (s) => {
  let out = s;
  for (let i = 0; i < CONTRACTIONS.length; i++) out = out.replace(CONTRACTIONS[i][0], CONTRACTIONS[i][1]);
  return out.replace(/\\s+/g, " ").trim();
};
'''

QUESTION_JS = r'''
// --- French question forms ------------------------------------------------
// French asks a question three ways: rising intonation ("tu veux venir ?"),
// est-ce que ("est-ce que tu veux venir ?") and inversion ("veux-tu venir ?").
// The deck stores whichever is idiomatic; all three are correct, and the formal
// written forms were being marked wrong. Derive the alternatives here.
// Only stored answers that are QUESTIONS are transformed, so the noun
// "rendez-vous" is never mistaken for an inverted verb.
const FR_INTERROGATIVE = /^(comment|où|ou|quand|pourquoi|combien|qui|quel|quelle|quels|quelles|que)\b/i;
function frenchQuestionVariants(s) {
  const out = [s];
  if (!s || s.indexOf("?") < 0) return out;
  const add = function(v) {
    const t = (v || "").replace(/\s+/g, " ").trim();
    if (t && out.indexOf(t) < 0) out.push(t);
  };
  // "qu'est-ce que X" and "est-ce que X" -> plain X
  add(s.replace(/^qu'est-ce\s+qu(?:e\b|')\s*/i, "").replace(/\best-ce\s+qu(?:e\b|')\s*/gi, ""));
  // inversion -> subject first. The character class keeps a leading clitic with
  // its verb, so "comment t'appelles-tu ?" becomes "comment tu t'appelles ?"
  // rather than splitting "t'" off the front.
  add(s.replace(/([A-Za-zÀ-ÖØ-öø-ÿ']+)-t-(il|elle|on)\b/gi, "$2 $1")
       .replace(/([A-Za-zÀ-ÖØ-öø-ÿ']+)-(je|tu|il|elle|on|nous|vous|ils|elles)\b/gi, "$2 $1"));
  // "qu'est-ce que X ?" -> "X quoi ?" — the interrogative left in place, which
  // is how the question is normally spoken.
  const mq = s.match(/^qu'est-ce\s+qu(?:e\b|')\s*(.+?)\s*\?\s*$/i);
  if (mq) add(mq[1] + " quoi ?");
  // plain -> inversion. Which token is the verb cannot be known without
  // parsing, so offer the two shapes that cover ordinary and reflexive verbs:
  // "tu veux venir ?" -> "veux-tu venir ?" and
  // "comment vous vous appelez ?" -> "comment vous appelez-vous ?".
  const SUBJ = "(je|tu|il|elle|on|nous|vous|ils|elles)";
  const CLITIC = "(?:me|te|se|nous|vous|le|la|les|lui|leur|y|en)";
  add(s.replace(new RegExp("\\b" + SUBJ + "\\s+(" + CLITIC + "\\s+[A-Za-zÀ-ÖØ-öø-ÿ']+)", "i"), "$2-$1"));
  add(s.replace(new RegExp("\\b" + SUBJ + "\\s+([A-Za-zÀ-ÖØ-öø-ÿ']+)", "i"), "$2-$1"));
  // plain -> est-ce que, inserted after any leading interrogative word
  out.slice().forEach(function(v) {
    if (/\best-ce\s+qu/i.test(v)) return;
    const m = v.match(FR_INTERROGATIVE);
    add(m ? v.slice(0, m[0].length) + " est-ce que " + v.slice(m[0].length) : "est-ce que " + v);
  });
  return out;
}
'''



FULL_TARGET_JS = """  const alts = [target.trim()].concat(target.split(/[,/]/).map(a => a.trim())).filter(Boolean);"""


def patch_full_target(src, name):
    """A comma in a gloss is usually an alternative ("town, city") but sometimes
    part of the phrase itself ("I'm fine, thanks"). Splitting on it lost the
    second kind entirely, so "I am fine, thanks" could never match. Keep the
    split (it is right most of the time) and add the intact target alongside."""
    if "const alts = [target.trim()]" in src:
        return src, "already present"
    old = "  const alts = target.split(/[,/]/).map(a => a.trim()).filter(Boolean);"
    assert src.count(old) == 1, f"{name}: gradeAnswer alts line not found"
    return src.replace(old, FULL_TARGET_JS), "patched"


def read(p):
    return open(p, encoding="utf-8").read()


def write(p, s):
    open(p, "w", encoding="utf-8").write(s)


def patch_contractions(src, name):
    if "expandContractions" in src:
        return src, "already present"
    anchor = "const gradeOne = (input, target) => {"
    assert src.count(anchor) == 1, f"{name}: gradeOne not found"
    src = src.replace(anchor, CONTRACTIONS_JS.strip() + "\n\n" + anchor)
    # apply it right after the filler strip, so both sides get the same treatment
    old = "  ni = stripFiller(ni);\n  nt = stripFiller(nt);"
    assert src.count(old) == 1, f"{name}: filler-stripping lines not found"
    src = src.replace(old, old + "\n  ni = expandContractions(ni);\n  nt = expandContractions(nt);")
    return src, "patched"


DEFAULT_EXAMPLE = '"big" is grand / grande / grands / grandes'


def patch_adjectives(src, name, lang, example=DEFAULT_EXAMPLE, note=""):
    """Gloss->target: accept every gender/number form of an adjective.

    `example` names the shape in that language's own words, and `note` says why
    the language's `declension` is safe to open up, because those comments are
    the only thing telling the next reader why a Latin genitive is NOT accepted."""
    if "adjective agreement" in src:
        return src, "already present"
    old = f"""    const accept = matches.map(function(x){{ return x.{lang}; }});"""
    assert src.count(old) == 1, f"{name}: {lang} accept list not found"
    new = f"""    let accept = matches.map(function(x){{ return x.{lang}; }});
    // adjective agreement: the prompt carries no gender or number, so every
    // agreeing form answers it -- {example}.{note}
    matches.forEach(function(x) {{
      if (x.pos === "adjective" && x.declension) {{
        Object.keys(x.declension).forEach(function(k) {{
          const f = x.declension[k];
          if (f && accept.indexOf(f) < 0) accept.push(f);
        }});
      }}
      // curated synonyms are interchangeable for this gloss by construction
      (x.synonyms || []).forEach(function(id) {{
        const s = byId[id];
        if (s && s.{lang} && accept.indexOf(s.{lang}) < 0) accept.push(s.{lang});
      }});
    }});"""
    return src.replace(old, new), "patched"


def patch_questions(src, name):
    if "frenchQuestionVariants" in src:
        return src, "already present"
    anchor = "const gradeOne = (input, target) => {"
    src = src.replace(anchor, QUESTION_JS.strip() + "\n\n" + anchor)
    # widen the EN->FR accept list with the derived question shapes
    old = "    return { type: mode, entryId: e.id, prompt: e.en, promptLabel: \"English\",\n" \
          "             answerLabel: \"French\", target: e.fr,"
    assert src.count(old) == 1, f"{name}: en_fr return not found"
    new = ("    let widened = [];\n"
           "    accept.forEach(function(a){ widened = widened.concat(frenchQuestionVariants(a)); });\n"
           "    accept = widened.filter(function(v, i, arr){ return v && arr.indexOf(v) === i; });\n"
           + old)
    return src.replace(old, new), "patched"


def patch_filler_guard(src, name):
    """Filler-stripping must never reduce an answer to nothing.

    stripFiller drops particles from both sides so "sich entschuldigen"
    and "entschuldigen" match. When the entire answer is one of those particles
    the target became "", and gradeOne then compared "" against "" -- so German
    "sich" graded exact for the Polish headword "sie". Falling back to the
    unstripped string keeps the interchangeability and loses the false accept."""
    if "return kept || s" in src:
        return src, "already present"
    m = re.search(r'^const stripFiller = \(s\) => (s\.split\(" "\).*?)\;$',
                  src, re.M)
    assert m, f"{name}: one-line stripFiller not found"
    body = m.group(1)
    new = ('const stripFiller = (s) => {\n'
           f'  const kept = {body};\n'
           '  return kept || s;   // never let filler-stripping empty an answer:\n'
           '                      // the particle can itself be the headword\n'
           '};')
    return src[:m.start()] + new + src[m.end():], "patched"


# Per-language wording for the adjective-agreement comment: (example, note).
ADJECTIVE_COMMENT = {
    "pl": ('"gro\u00df" is du\u017cy / du\u017ca / du\u017ce / duzi',
           "\n    // Safe because Polish `declension` holds nominative forms only; it does\n"
           "    // not span cases the way Latin's does."),
}


def main():
    jobs = [
        ("french_trainer.html", "fr", True),
        ("spanish_trainer.html", "es", False),
        ("italian_trainer.html", "it", False),
        ("latin_trainer.html", "la", False),   # contractions only; see module docstring
        # Polish is glossed in German: no contractions, and it is the one app
        # whose FILLER can swallow a whole answer, so it gets the guard.
        ("polish_trainer.html", "pl", False),
    ]
    for fname, lang, is_french in jobs:
        path = os.path.join(LT, fname)
        src = read(path)
        notes = []
        if lang != "pl":                       # German glosses, no contractions
            src, c = patch_contractions(src, fname)
            notes.append(f"contractions {c}")
        src, ft = patch_full_target(src, fname)
        notes.append(f"whole-phrase targets {ft}")
        if lang not in ("la",):
            example, note = ADJECTIVE_COMMENT.get(lang, (DEFAULT_EXAMPLE, ""))
            src, a = patch_adjectives(src, fname, lang, example, note)
            notes.append(f"adjective+synonym accept {a}")
        src, g = patch_filler_guard(src, fname)
        notes.append(f"filler guard {g}")
        if is_french:
            src, q = patch_questions(src, fname)
            notes.append(f"question forms {q}")
        write(path, src)
        print(f"{fname}: " + " · ".join(notes))


if __name__ == "__main__":
    main()
