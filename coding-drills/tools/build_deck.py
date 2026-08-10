#!/usr/bin/env python3
"""Shared, assert-guarded deck builder for gitDrill and sqlDrill.

The decks are curated Python (`git_deck.py`, `sql_deck.py`) rather than
hand-edited JSON inside the HTML, for the same reason the Latin and medical
decks are generated: a cross-check that fails the build is the only thing that
reliably keeps authored data honest. Here the checks that earn their keep are

  * every fill card's blank is really blank -- a `fill` whose answer already
    appears in the visible snippet is a giveaway, and one whose code has no `_`
    is unanswerable. Both have bitten other decks.
  * accept-lists cannot contain the answer again, or two spellings that
    normalise to the same string. A redundant alternative looks like tolerance
    but grades nothing new, so it hides a missing real alternative.
  * multiple-choice answers must index a real option, options must be distinct,
    and the danger scale must be exactly the three standard levels -- a
    four-option danger card would mean the scale drifted.
  * every summary must survive renderTeach: no Markdown (it renders literally),
    and code examples indented four spaces or they reflow into the prose.

    python3 tools/build_deck.py            # writes git_deck.json + sql_deck.json
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))

MIN_SUMMARY_WORDS = 45        # matches tools/update_summaries.py
CODE_WIDTH_WARN = 52          # pre.code scrolls, but keep most lines on screen

# The danger scale, written onto every danger card so the three levels stay
# identical everywhere. Order is deliberate: it reads as increasing severity,
# and "recoverable" sits in the middle because that is the distinction most
# people lack -- they think reset --hard on a COMMIT is as final as on an
# uncommitted change, and it is not.
DANGER_OPTIONS = [
    "Safe — nothing is lost",
    "Recoverable — the old state is still in the reflog",
    "Destroys work permanently — no way back",
]
DANGER_SAFE, DANGER_REFLOG, DANGER_GONE = 0, 1, 2

TEXT_MODES = ("predict", "fill", "recall", "command", "history", "rows")
MC_MODES = ("confusable", "danger")
ALL_MODES = TEXT_MODES + MC_MODES


class DeckError(Exception):
    pass


def _norm(s):
    """How gradeText compares: trailing space per line stripped, quotes unified."""
    s = str(s).replace("\r", "")
    s = "\n".join(l.rstrip() for l in s.split("\n")).strip("\n")
    return s.replace("'", '"')


# Every string the app shows is escaped with esc(), so Markdown renders
# literally: a backtick meant as `code` appears on screen as a backtick. The
# teach panels learned this the hard way (tools/strip_backticks.py cleaned up
# 215 of them), so this check covers ANY visible field rather than only
# summaries -- a question prompt is just as visible as a teach panel.
VISIBLE_FIELDS = ("prompt", "explain", "why", "hint", "lbl", "cmd")


def check_no_markup(cid, where, text):
    if "`" in str(text):
        raise DeckError(f"{cid}/{where}: contains a backtick — the app escapes text, "
                        f"so it renders as a literal backtick rather than as code")


def check_visible(cid, mode, it):
    for f in VISIBLE_FIELDS:
        if f in it:
            check_no_markup(cid, f"{mode}.{f}", it[f])
    for i, opt in enumerate(it.get("options") or []):
        check_no_markup(cid, f"{mode}.options[{i}]", opt)


def check_summary(cid, text):
    if not text or not text.strip():
        raise DeckError(f"{cid}: empty summary")
    words = len(text.split())
    if words < MIN_SUMMARY_WORDS:
        raise DeckError(f"{cid}: summary is {words} words, minimum {MIN_SUMMARY_WORDS}")
    check_no_markup(cid, "summary", text)
    # An indented run is a code block to renderTeach; anything indented 1-3
    # spaces is neither prose nor code and renders as ragged prose.
    for line in text.split("\n"):
        if line.strip() and line[:4] != "    " and line[0] == " ":
            raise DeckError(f"{cid}: line indented 1–3 spaces — renderTeach only "
                            f"treats 4+ as code: {line!r}")


def check_text_item(cid, mode, it, ctx, card):
    if "answer" not in it and mode != "predict":
        raise DeckError(f"{cid}/{mode}: no answer")
    expected = it.get("output") if mode == "predict" else it.get("answer")
    if expected is None or str(expected).strip() == "":
        raise DeckError(f"{cid}/{mode}: blank expected answer")

    for alt in it.get("accept", []):
        if _norm(alt) == _norm(expected):
            raise DeckError(f"{cid}/{mode}: accept entry {alt!r} equals the answer")
    seen = set()
    for alt in it.get("accept", []):
        n = _norm(alt)
        if n in seen:
            raise DeckError(f"{cid}/{mode}: duplicate accept entry {alt!r}")
        seen.add(n)

    if mode == "fill":
        if "_" not in it.get("code", ""):
            raise DeckError(f"{cid}/fill: code has no _ blank")
        if "_" in str(it["answer"]):
            raise DeckError(f"{cid}/fill: answer still contains _")
        # the answer must not already be visible in the snippet
        shown = re.sub(r"_+", "\x00", it["code"])
        if len(str(it["answer"])) >= 3 and str(it["answer"]) in shown:
            raise DeckError(f"{cid}/fill: answer {it['answer']!r} is already visible in the code")

    if mode == "rows":
        if not re.fullmatch(r"\d+", str(it["answer"])):
            raise DeckError(f"{cid}/rows: answer must be a plain integer, got {it['answer']!r}")
        if not it.get("code"):
            raise DeckError(f"{cid}/rows: no query")

    if mode == "history":
        if not it.get("cmd"):
            raise DeckError(f"{cid}/history: no command")
        if not (it.get("fixture") or card.get("fixture")):
            raise DeckError(f"{cid}/history: no starting state — the question is unanswerable")
        if not re.fullmatch(r"[A-Za-z0-9′'\- ]+", str(it["answer"])):
            raise DeckError(f"{cid}/history: answer should be a commit-label sequence, "
                            f"got {it['answer']!r}")

    if mode == "command":
        if not it.get("prompt"):
            raise DeckError(f"{cid}/command: no goal prompt")
        prefix = ctx.get("cmd_prefix")
        if prefix:
            for cand in [it["answer"]] + list(it.get("accept", [])):
                if not str(cand).startswith(prefix):
                    raise DeckError(f"{cid}/command: {cand!r} does not start with {prefix!r}")

    if mode == "predict":
        if not it.get("code"):
            raise DeckError(f"{cid}/predict: no query")
        if ctx.get("needs_fixture") and not (it.get("fixture") or card.get("fixture")):
            raise DeckError(f"{cid}/predict: no table fixture — the result is unknowable")


def check_mc_item(cid, mode, it):
    opts = it.get("options")
    if not opts or len(opts) < 2:
        raise DeckError(f"{cid}/{mode}: needs at least two options")
    if len(set(opts)) != len(opts):
        raise DeckError(f"{cid}/{mode}: duplicate options")
    if not isinstance(it.get("answer"), int) or not (0 <= it["answer"] < len(opts)):
        raise DeckError(f"{cid}/{mode}: answer {it.get('answer')!r} is not a valid option index")
    if not it.get("explain"):
        raise DeckError(f"{cid}/{mode}: no explanation")
    if mode == "danger" and opts != DANGER_OPTIONS:
        raise DeckError(f"{cid}/danger: options are not the standard three-level scale")


def build(deck_module, out_name, ctx):
    """deck_module exposes TOPICS (list of (id, label)) and CARDS (list of dict)."""
    topics = [{"id": t, "label": l} for t, l in deck_module.TOPICS]
    topic_ids = {t for t, _ in deck_module.TOPICS}
    cards, seen_ids, wide = [], set(), []
    mode_counts = {m: 0 for m in ALL_MODES}

    for card in deck_module.CARDS:
        cid = card["id"]
        if cid in seen_ids:
            raise DeckError(f"duplicate card id {cid}")
        seen_ids.add(cid)
        if card["topic"] not in topic_ids:
            raise DeckError(f"{cid}: unknown topic {card['topic']}")
        if not cid.startswith(card["topic"] + "-"):
            raise DeckError(f"{cid}: id does not match its topic {card['topic']}")
        check_summary(cid, card.get("summary", ""))

        units = 0
        for mode in ALL_MODES:
            for it in card.get(mode, []):
                if mode == "danger" and not it.get("options"):
                    # cards write `"options": None` to say "use the standard scale"
                    it["options"] = list(DANGER_OPTIONS)
                check_visible(cid, mode, it)
                if mode in MC_MODES:
                    check_mc_item(cid, mode, it)
                else:
                    check_text_item(cid, mode, it, ctx, card)
                for field in ("code", "fixture"):
                    for line in str(it.get(field, "")).split("\n"):
                        if len(line) > CODE_WIDTH_WARN:
                            wide.append(f"{cid}/{mode}: {len(line)} chars")
                mode_counts[mode] += 1
                units += 1
        if units == 0:
            raise DeckError(f"{cid}: no questions of any kind")
        cards.append(card)

    for mode, _lbl in ctx["modes"]:
        if mode_counts[mode] == 0:
            raise DeckError(f"mode {mode!r} is offered but no card uses it")
    for mode, n in mode_counts.items():
        if n and mode not in {m for m, _ in ctx["modes"]}:
            raise DeckError(f"{n} cards use mode {mode!r}, which the app does not offer")

    empty = [t for t in topic_ids if not any(c["topic"] == t for c in cards)]
    if empty:
        raise DeckError(f"topics with no cards: {sorted(empty)}")

    deck = {"meta": {"version": "1.6", "reference_lang": "en",
                     "level": ctx["level"], "created": ctx["created"]},
            "topics": topics, "cards": cards}
    path = os.path.join(HERE, out_name)
    json.dump(deck, open(path, "w", encoding="utf-8"), ensure_ascii=False)

    total = sum(mode_counts.values())
    per = " · ".join(f"{n} {m}" for m, n in mode_counts.items() if n)
    print(f"{out_name}: {len(cards)} cards / {total} questions ({per})")
    if wide:
        print(f"  note: {len(wide)} code lines over {CODE_WIDTH_WARN} chars (they scroll): "
              + ", ".join(wide[:4]) + (" …" if len(wide) > 4 else ""))
    return deck


def main():
    import git_deck, sql_deck
    build(git_deck, "git_deck.json", {
        "modes": __import__("make_drill").GIT_MODES,
        "level": "intermediate", "created": "2026-08-10",
        "cmd_prefix": "git ", "needs_fixture": False,
    })
    build(sql_deck, "sql_deck.json", {
        "modes": __import__("make_drill").SQL_MODES,
        "level": "intermediate", "created": "2026-08-10",
        "needs_fixture": True,
    })


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    main()
