#!/usr/bin/env python3
"""Engine v1.6: accept-lists, fixture blocks, and three new drill modes.

Everything here exists for gitDrill and sqlDrill, but it goes into every app
because the engine JS must stay identical across files (CLAUDE.md hard rule).
py/bash/cpp simply have no cards using the new modes, and MODE_LABELS -- which
is per-app config, not engine -- does not list them there, so nothing changes
on screen for the existing three.

What it adds:

  accept-lists   A typed answer can have several right spellings. Git is the
                 clear case: HEAD~1 and HEAD^ name the same commit, and
                 `git restore --staged f` and `git reset f` unstage the same
                 way. SQL has fewer but real ones (JOIN vs INNER JOIN). Without
                 this the deck would have to pick one spelling and mark the
                 other wrong, which teaches a falsehood.

  fixture        A block of context rendered above the snippet: the repo state
                 for git, the table contents for SQL. Neither drill can ask a
                 meaningful question without it -- "how many rows come back"
                 is unanswerable without seeing the rows.

  command        Goal -> command. The high-value git drill, the counterpart of
                 predict-output: you are told what you want to achieve and you
                 type the command that does it.

  history        Given a commit graph and a command, list the commits after it.
                 Typing an ASCII graph would be unusable on a phone, so commits
                 are letter-labelled and the answer is a newest-first sequence
                 (E' D' C B A), with a prime marking a rewritten commit. That
                 keeps the rebase-vs-merge distinction -- which is the whole
                 point -- while staying typeable.

  danger        Does this command lose work? Routed to the existing
                 multiple-choice renderer rather than a new one, since the
                 options are a fixed three-way scale written by the builder.

  rows          How many rows does this query return? One number to grade, and
                 it is exactly the join intuition people lack (fan-out on a
                 duplicated key, LEFT JOIN with no match, NULL never matching).

Re-runnable: skips a file that already has v1.6.

    python3 tools/patch_engine_v16.py
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CD = os.path.join(HERE, "..")
APPS = ["python-drill.html", "bash-drill.html", "cpp-drill.html"]

FIXTURE_CSS = """  pre.fixture{background:var(--card);border:1px solid var(--line);color:var(--ink);
    font-family:var(--mono);font-size:12.5px;line-height:1.5;padding:11px 12px;border-radius:10px;
    overflow-x:auto;margin:0 0 10px;white-space:pre}
  pre.fixture b{font-weight:700}
"""

# --- unitsForCardMode: three new modes -------------------------------------
UNITS_OLD = """  if(mode==="recall")     return (card.recall||[]).map(function(it){return {kind:"text", item:it};});"""
UNITS_NEW = """  if(mode==="recall")     return (card.recall||[]).map(function(it){return {kind:"text", item:it};});
  if(mode==="command")    return (card.command||[]).map(function(it){return {kind:"text", item:it};});
  if(mode==="history")    return (card.history||[]).map(function(it){return {kind:"text", item:it};});
  if(mode==="rows")       return (card.rows||[]).map(function(it){return {kind:"text", item:it};});
  if(mode==="danger")     return (card.danger||[]).map(function(it){return {kind:"mc", item:it};});"""

# --- grading: try every accepted spelling, keep the best grade --------------
GRADE_ANY = """
/* A typed answer may have several correct spellings -- HEAD~1 and HEAD^ name the
   same commit, JOIN and INNER JOIN the same join. Grade against each and keep
   the best result, so an accepted alternative scores exact rather than close. */
var GRADE_RANK = {wrong:0, close:1, exact:2};
function gradeAny(user, expected, accept, grader){
  var best = grader(user, expected);
  if(best === "exact" || !accept || !accept.length) return best;
  for(var i=0;i<accept.length;i++){
    var g = grader(user, accept[i]);
    if(GRADE_RANK[g] > GRADE_RANK[best]) best = g;
    if(best === "exact") break;
  }
  return best;
}
"""

# --- renderQuestion: fixture + new modes -----------------------------------
MC_ROUTE_OLD = """  if(u.mode==="confusable"){
    renderMC(head, nameLine); return;
  }"""
MC_ROUTE_NEW = """  // danger reuses the multiple-choice renderer: its options are a fixed
  // three-way scale, written onto every card by the deck builder.
  if(u.mode==="confusable" || u.mode==="danger"){
    renderMC(head, nameLine); return;
  }"""

MODES_OLD = """  } else if(u.mode==="complexity"){
    codeHtml='<pre class="code">'+esc(u.card.name)+'  \\u2014  '+esc(u.item.op)+'</pre>';
    lbl="Average-case complexity, e.g. O(1), O(n), O(log n)"; multiline=false;
  }"""
MODES_NEW = """  } else if(u.mode==="complexity"){
    codeHtml='<pre class="code">'+esc(u.card.name)+'  \\u2014  '+esc(u.item.op)+'</pre>';
    lbl="Average-case complexity, e.g. O(1), O(n), O(log n)"; multiline=false;
  } else if(u.mode==="command"){
    codeHtml=''; lbl=u.item.lbl||"Type the command"; multiline=false;
    nameLine='<p class="qname">'+esc(u.item.prompt||u.card.name)+'</p>';
  } else if(u.mode==="history"){
    codeHtml='<pre class="code"><span class="prompt">$ '+esc(u.item.cmd)+'</span></pre>';
    // Apostrophe, not a typographic prime: the answers use ASCII and the label
    // has to show something reachable from a phone keyboard.
    lbl=u.item.lbl||"Commits newest first, e.g. E' D' C B A (' = rewritten)";
    multiline=false;
    nameLine='<p class="qname">'+esc(u.item.prompt||u.card.name)+'</p>';
  } else if(u.mode==="rows"){
    codeHtml='<pre class="code">'+esc(u.item.code)+'</pre>';
    lbl=u.item.lbl||"How many rows does this return?"; multiline=false;
  }"""

FIXTURE_RENDER_OLD = """  var c = el('<div class="card">'+head+nameLine+codeHtml+"""
FIXTURE_RENDER_NEW = """  // Context the question cannot be answered without: the repo state for git,
  // the table contents for SQL. Sits above the snippet, scrolls on its own.
  var fx = (u.item && u.item.fixture) || u.card.fixture || "";
  var fxHtml = fx ? '<pre class="fixture">'+esc(fx)+'</pre>' : "";

  var c = el('<div class="card">'+head+nameLine+fxHtml+codeHtml+"""

DOGRADE_OLD = """    var expected = (u.mode==="predict") ? u.item.output
                 : (u.mode==="fill")    ? u.item.answer
                 : (u.mode==="recall")  ? u.item.answer
                 : (u.mode==="complexity") ? u.item.info.bigO : "";
    var grade = (u.mode==="predict") ? gradeOutput(val, expected)
              : (u.mode==="complexity") ? gradeBigO(val, expected)
              : gradeText(val, expected);
    commit(grade, val, expected);"""
DOGRADE_NEW = """    var expected = (u.mode==="predict") ? u.item.output
                 : (u.mode==="complexity") ? u.item.info.bigO
                 : u.item.answer;
    var grader = (u.mode==="predict") ? gradeOutput
               : (u.mode==="complexity") ? gradeBigO
               : gradeText;
    var grade = gradeAny(val, expected, u.item.accept, grader);
    commit(grade, val, expected);"""

# MC feedback must show the danger explanation the same way confusable does;
# both already store it under `explain`, so nothing to change there.


def read(p):
    return open(os.path.join(CD, p), encoding="utf-8").read()


def write(p, s):
    open(os.path.join(CD, p), "w", encoding="utf-8").write(s)


def sub(src, name, old, new):
    assert src.count(old) == 1, f"{name}: anchor not found exactly once: {old[:70]!r}"
    return src.replace(old, new)


def patch(name):
    src = read(name)
    if "function gradeAny" in src:
        return "already v1.6"

    src = sub(src, name, "  pre.code .blank{", FIXTURE_CSS + "  pre.code .blank{")
    src = sub(src, name, UNITS_OLD, UNITS_NEW)
    src = sub(src, name, "function normBigO(s){", GRADE_ANY.strip() + "\n\nfunction normBigO(s){")
    src = sub(src, name, MC_ROUTE_OLD, MC_ROUTE_NEW)
    src = sub(src, name, MODES_OLD, MODES_NEW)
    src = sub(src, name, FIXTURE_RENDER_OLD, FIXTURE_RENDER_NEW)
    src = sub(src, name, DOGRADE_OLD, DOGRADE_NEW)
    src = sub(src, name, "  gradeText:gradeText,", "  gradeText:gradeText, gradeAny:gradeAny,")

    write(name, src)
    return "patched to v1.6"


def main():
    for name in APPS:
        print(f"{name}: {patch(name)}")


if __name__ == "__main__":
    main()
