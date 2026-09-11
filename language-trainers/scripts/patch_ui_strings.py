#!/usr/bin/env python3
"""Two small UI-string fixes, requested together.

1. "Cloze" -> "Fill the gap" as the drill-type button label and the on-card
   prompt label, in every app that has it. The internal mode key stays
   `cloze` (it's not user-visible, and every other engine reference to it --
   grading, buildPool filters, MODE_ELIGIBLE -- keys off the string literal
   "cloze", not the label). Medical already calls its cloze-shaped mode
   "Clinical context" and never says "Cloze" anywhere user-visible, so it
   needs nothing here directly; regenerating it still picks up nothing new
   for this fix, since showSummary (fix 2, below) is what medical inherits.

2. The "perfect round" / "review cleared" celebration text was scaffolded
   from Polish into every other app with the Polish word "Świetnie" still in
   it -- the exact "prose string a mechanical rename walks past" class of bug
   this project's CLAUDE.md keeps finding. Polish keeps it (it's the one app
   Świetnie belongs in); every other app gets its own language's word:
   Spanish "¡Genial!", Italian "Ottimo!", French "Excellent !" (French
   typography: a space before "!"), Latin "Optime!".

Applies directly to Spanish/Italian/French/Latin (hand-maintained) and to
Polish for fix 1 only. Medical and the two Portuguese apps are generated:
- medical_trainer.html: showSummary is not among the regions
  make_medical_trainer.py swaps, so it inherits Latin's fixed text on the
  next regeneration -- no generator change needed for either fix.
- portuguese_trainer.html / brazilian_trainer.html: fix 1 flows through
  unchanged (no es/pt field reference in the label strings). Fix 2 needs its
  own generator rule, since Portuguese wants "Ótimo!", not Spanish's
  "¡Genial!" -- added to make_portuguese_trainer.py's existing rename list,
  keyed on Spanish's NEW text so it only fires after this script has run.

Re-runnable: checks whether each fix is already present.

    python3 scripts/patch_ui_strings.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LT = os.path.join(HERE, "..")

CLOZE_LABEL_OLD = '  ["cloze", "Cloze"],'
CLOZE_LABEL_NEW = '  ["cloze", "Fill the gap"],'
CLOZE_PROMPT_OLD = '             promptLabel: "Cloze — fill the gap",'
CLOZE_PROMPT_NEW = '             promptLabel: "Fill the gap",'

PRAISE_OLD = '''      ? "All mistakes cleared — nothing left to re-drill. Świetnie! 🎉"
      : "Perfect round — nothing to review. Świetnie!";'''

PRAISE_WORD = {
    "spanish_trainer.html": "¡Genial!",
    "italian_trainer.html": "Ottimo!",
    "french_trainer.html": "Excellent !",
    "latin_trainer.html": "Optime!",
}


def read(p):
    return open(os.path.join(LT, p), encoding="utf-8").read()


def write(p, s):
    open(os.path.join(LT, p), "w", encoding="utf-8").write(s)


def patch_cloze_label(src, name):
    if "Fill the gap" in src:
        return src, "already present"
    assert src.count(CLOZE_LABEL_OLD) == 1, f"{name}: cloze mode label not found"
    src = src.replace(CLOZE_LABEL_OLD, CLOZE_LABEL_NEW)
    assert src.count(CLOZE_PROMPT_OLD) == 1, f"{name}: cloze promptLabel not found"
    src = src.replace(CLOZE_PROMPT_OLD, CLOZE_PROMPT_NEW)
    return src, "patched"


def patch_praise(src, name, word):
    if "Świetnie" not in src:
        return src, "already present"
    assert src.count(PRAISE_OLD) == 1, f"{name}: praise text not found"
    new = (f'      ? "All mistakes cleared — nothing left to re-drill. {word} 🎉"\n'
           f'      : "Perfect round — nothing to review. {word}";')
    return src.replace(PRAISE_OLD, new), "patched"


def main():
    # Fix 1: every hand-maintained app, Polish included.
    for name in ["polish_trainer.html", "spanish_trainer.html", "italian_trainer.html",
                 "french_trainer.html", "latin_trainer.html"]:
        src = read(name)
        src, note1 = patch_cloze_label(src, name)
        write(name, src)
        print(f"{name}: cloze label {note1}")

    # Fix 2: every hand-maintained app EXCEPT Polish, which keeps Świetnie.
    for name, word in PRAISE_WORD.items():
        src = read(name)
        src, note2 = patch_praise(src, name, word)
        write(name, src)
        print(f"{name}: praise text {note2}")


if __name__ == "__main__":
    main()
