#!/usr/bin/env python3
"""Add a "hardest questions" round to pyDrill / bashDrill / cppDrill.

The counterpart of scripts/patch_hardest.py in language-trainers, but against a
different engine: here a round is the whole selection queued up, not an endless
stream, so the round is a queue built from the hardest units instead of a pool
the picker draws from.

Why it is needed. weightFor already prefers questions you get wrong, but only
softly: an always-wrong unit scores 5 against 1 for a mastered one, and an
UNSEEN unit outranks both at 12. Since buildQueue only reorders the selection,
that buys a hard question a slightly earlier slot in a 381-question round -- it
never lets you drill the hard ones on their own.

Owner's design choices, matching the language trainers:
  ranking  -- raw wrong count. recordResult books "close" as a correct answer,
              never a wrong, so this counts outright misses only.
  scope    -- global. It IGNORES the topic and drill-mode pills, so it is always
              the hardest questions overall, not the hardest inside whatever
              happens to be selected.
  shape    -- a separate round button on the home screen, beside "Start round",
              reusing the existing round machinery.

Engine changes must be applied identically to all three files (CLAUDE.md HARD
RULE); this patches all three by exact-match replacement and asserts each anchor
appears exactly once.

Re-runnable: skips a file that already has the round.

    python3 tools/patch_hardest.py
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CD = os.path.join(HERE, "..")
APPS = ["python-drill.html", "bash-drill.html", "cpp-drill.html"]

CORE_JS = r'''
/* ============================== HARDEST QUESTIONS ============================== */
/* weightFor prefers questions you get wrong, but only softly (5 against 1 for a
   mastered unit, and 12 for an unseen one), and buildQueue only reorders the
   selection -- so a hard question never gets drilled on its own. This round
   queues ONLY the questions with the most wrong answers.
   Deliberately global: it ignores the topic and drill-mode pills, so it is the
   hardest questions overall rather than the hardest in the current selection. */
var HARDEST_SHARE = 0.10;     // top 10% of everything attempted
var HARDEST_MIN_POOL = 8;     // below this there is too little history to be useful

/* every unit in the deck, filters ignored -- askableUnits() honours the pills */
function everyUnit(){
  var out = [];
  DECK_DATA.cards.forEach(function(card){
    MODE_LABELS.forEach(function(m){
      unitsForCardMode(card, m[0]).forEach(function(u, i){
        out.push({card:card, mode:m[0], i:i, kind:u.kind, item:u.item, qid:qidFor(card,m[0],i)});
      });
    });
  });
  return out;
}

/* Ranked by raw wrong count. recordResult books a near-miss ("close") as a
   correct answer and never increments wrong, so this is outright misses only. */
function hardestUnits(){
  var attempted = 0, rows = [];
  everyUnit().forEach(function(u){
    var p = progress[u.qid];
    if(!p || !p.seen) return;                  // unseen is not hard, just unmet
    attempted++;
    if(p.wrong > 0) rows.push({u:u, wrong:p.wrong, rate:p.wrong/p.seen});
  });
  rows.sort(function(a,b){
    if(b.wrong !== a.wrong) return b.wrong - a.wrong;
    return b.rate - a.rate;                    // tie-break on the worse rate
  });
  var target = Math.max(HARDEST_MIN_POOL, Math.ceil(attempted * HARDEST_SHARE));
  return rows.slice(0, Math.min(target, rows.length)).map(function(r){ return r.u; });
}
'''

HOME_CARD_JS = r'''
  // Hardest-questions round: an alternative to "Start round", not a filter.
  var hard = hardestUnits();
  var hardReady = hard.length >= HARDEST_MIN_POOL;
  var hardCard = el('<div class="card center"><button id="hardestBtn"'+
    (hardReady?"":" disabled")+'>Drill my hardest questions'+
    (hardReady?' · '+hard.length:'')+'</button>'+
    '<div class="small" style="margin-top:8px">'+
    (hardReady
      ? 'The '+hard.length+' you get wrong most often, across the whole deck — '+
        'ignores the topic and drill-mode selections above.'
      : 'Unlocks once '+HARDEST_MIN_POOL+' different questions have been missed ('+
        hard.length+' so far).')+
    '</div></div>');
  if(hardReady){
    hardCard.querySelector("#hardestBtn").onclick = function(){ startRound(hard, "hardest"); };
  }
'''


def read(p):
    return open(os.path.join(CD, p), encoding="utf-8").read()


def write(p, s):
    open(os.path.join(CD, p), "w", encoding="utf-8").write(s)


def sub(src, name, old, new, count=1):
    assert src.count(old) == count, f"{name}: anchor not found exactly {count}x: {old[:60]!r}"
    return src.replace(old, new)


def patch(name):
    src = read(name)
    if "hardestUnits" in src:
        return "already present"

    # 1. core, just above the queue builder it feeds
    src = sub(src, name, "/* weighted ordering: higher weight tends earlier, with variety */",
              CORE_JS.strip() + "\n\n/* weighted ordering: higher weight tends earlier, with variety */")

    # 2. startRound learns a round kind. A review round keeps the caller's order
    #    (you re-drill exactly what you missed); a hardest round is shuffled by
    #    weight like an ordinary one.
    src = sub(src, name, """function startRound(reviewUnits){
  var review = Array.isArray(reviewUnits);
  var units = review ? reviewUnits : askableUnits();
  if(!units.length) return;
  session = { queue: review ? units.slice() : buildQueue(units),
              idx:0, results:[], review: review, total: units.length };
  nextQuestion();
}""", """function startRound(givenUnits, kind){
  var given = Array.isArray(givenUnits);
  var hardest = given && kind === "hardest";
  var review = given && !hardest;
  var units = given ? givenUnits : askableUnits();
  if(!units.length) return;
  session = { queue: review ? units.slice() : buildQueue(units),
              idx:0, results:[], review: review, hardest: hardest, total: units.length };
  nextQuestion();
}""")

    # 3. label the round in the per-question eyebrow
    src = sub(src, name, "(session.review?' \\u00b7 review':'')+",
              "(session.review?' \\u00b7 review':session.hardest?' \\u00b7 hardest':'')+")

    # 4. the home screen button, above "Start round"
    src = sub(src, name, """  var units = askableUnits();
  var startCard = el('<div class="card center"><button class="primary" id="startBtn" '+""",
              """  var units = askableUnits();""" + HOME_CARD_JS.rstrip() + """
  var startCard = el('<div class="card center"><button class="primary" id="startBtn" '+""")
    src = sub(src, name,
              "app.appendChild(c1); app.appendChild(c2); app.appendChild(renderProgressCard()); app.appendChild(startCard);",
              "app.appendChild(c1); app.appendChild(c2); app.appendChild(renderProgressCard());\n"
              "  app.appendChild(hardCard); app.appendChild(startCard);")

    # 5. name the round in the summary heading
    src = sub(src, name, '(session.review?"Review complete":"Round complete")',
              '(session.review?"Review complete":session.hardest?"Hardest questions complete":"Round complete")')

    # 6. and offer it from the summary, so a round can lead straight into one
    src = sub(src, name, """  c.querySelector("#homeBtn").onclick = function(){ session=null; render(); };""",
              """  var hardNext = hardestUnits();
  if(hardNext.length >= HARDEST_MIN_POOL && !session.hardest){
    var hb = el('<button id="hardestNextBtn">Hardest '+hardNext.length+'</button>');
    c.querySelector(".row").insertBefore(hb, c.querySelector("#homeBtn"));
    hb.onclick = function(){ startRound(hardNext, "hardest"); };
  }
  c.querySelector("#homeBtn").onclick = function(){ session=null; render(); };""")

    # 7. expose for the validator probe
    src = sub(src, name, "weightFor:weightFor, unitsForCardMode:unitsForCardMode };",
              "weightFor:weightFor, unitsForCardMode:unitsForCardMode,\n"
              "  everyUnit:everyUnit, hardestUnits:hardestUnits, HARDEST_MIN_POOL:HARDEST_MIN_POOL,\n"
              "  currentUnit:function(){ return currentU; } };")

    write(name, src)
    return "patched"


def main():
    for name in APPS:
        print(f"{name}: {patch(name)}")


if __name__ == "__main__":
    main()
