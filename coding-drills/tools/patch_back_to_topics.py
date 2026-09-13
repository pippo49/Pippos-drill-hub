#!/usr/bin/env python3
"""Add a way to leave a round early and change the topic/mode selection.

Reported: unlike the language trainers, where toggling a filter takes effect
immediately mid-round, a coding-drill round is a fixed queue built once by
startRound(); render() shows renderQuestion() whenever `session` is truthy and
renderHome() (the topic/mode pills) only when it is null, and the ONLY place
in the whole file that ever sets `session = null` again is the "Done" button
on the round-complete summary. There is no quit button on the question screen
itself -- the only way to change topics before finishing every queued question
was to answer them all, or reload the page and lose the round's own tally
(though not your saved per-question stats, which recordResult writes on every
answer, not at round end).

Fix: header() -- rendered once per render() call, before the home/question
branch, so it already runs in both states -- appends a small "Back to topics"
link into the existing stat line when a round is active. render() wires its
click handler after appending the header: session = null; render() is exactly
what "Done" already does, just reachable one screen earlier and without
finishing the queue.

Placed inside the existing `.stat` text (not a new flex child of <header>,
which has exactly two children and `justify-content:space-between`) so no CSS
changes are needed and the header's two-column layout is untouched.

Engine changes apply identically to all three hand-maintained apps (CLAUDE.md
HARD RULE); git-drill/sql-drill pick it up via tools/make_drill.py.

Re-runnable: skips a file that already has it.

    python3 tools/patch_back_to_topics.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CD = os.path.join(HERE, "..")

# name -> the brand markup already inside its header()'s <div class="logo">
APPS = {
    "python-drill.html": "py<b>Drill</b>",
    "bash-drill.html": "bash<b>Drill</b>",
    "cpp-drill.html": "cpp<b>Drill</b>",
}


def old_header(logo):
    return (
        "function header(){\n"
        "  var units = askableUnits();\n"
        "  var cards = new Set(units.map(function(u){return u.card.id;})).size;\n"
        f"  return '<header><div class=\"logo\">{logo}</div>'+\n"
        "    '<div class=\"stat\">'+cards+' cards \\u00b7 '+units.length+' questions</div></header>';\n"
        "}"
    )


def new_header(logo):
    return (
        "function header(){\n"
        "  var units = askableUnits();\n"
        "  var cards = new Set(units.map(function(u){return u.card.id;})).size;\n"
        "  var backLink = session ? ' \\u00b7 <button class=\"hintlink\" id=\"backBtn\">Back to topics</button>' : '';\n"
        f"  return '<header><div class=\"logo\">{logo}</div>'+\n"
        "    '<div class=\"stat\">'+cards+' cards \\u00b7 '+units.length+' questions'+backLink+'</div></header>';\n"
        "}"
    )


OLD_RENDER = '''function render(){
  app.innerHTML = "";
  app.appendChild(el(header()));
  if(session){ renderQuestion(); } else { renderHome(); }
}'''
NEW_RENDER = '''function render(){
  app.innerHTML = "";
  var h = el(header());
  app.appendChild(h);
  if(session){
    var back = h.querySelector("#backBtn");
    if(back) back.onclick = function(){ session = null; render(); };
    renderQuestion();
  } else {
    renderHome();
  }
}'''


def read(p):
    return open(os.path.join(CD, p), encoding="utf-8").read()


def write(p, s):
    open(os.path.join(CD, p), "w", encoding="utf-8").write(s)


def patch(name, logo):
    src = read(name)
    if "backBtn" in src:
        return "already present"

    old_h, new_h = old_header(logo), new_header(logo)
    assert src.count(old_h) == 1, f"{name}: header() not found verbatim"
    src = src.replace(old_h, new_h)

    assert src.count(OLD_RENDER) == 1, f"{name}: render() not found"
    src = src.replace(OLD_RENDER, NEW_RENDER)

    write(name, src)
    return "patched"


def main():
    for name, logo in APPS.items():
        print(f"{name}: {patch(name, logo)}")


if __name__ == "__main__":
    main()
