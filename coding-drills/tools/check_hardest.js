/* Regression test for the hardest-questions round (see tools/patch_hardest.py).
 *
 * Seeds a synthetic history, then asserts the behaviour that was asked for:
 *
 *   * the set is ranked by RAW wrong count and is the top 10% of everything
 *     attempted, with a floor so a round is never two questions;
 *   * a question never got wrong never appears, however often it was seen;
 *   * the round queues ONLY that set;
 *   * it IGNORES the topic and drill-mode pills -- the "global" choice;
 *   * the button is disabled, and says why, with no history;
 *   * an ordinary round afterwards still queues the full selection.
 *
 *     node tools/check_hardest.js <file>.html      # exits 1 on any failure
 */
const { JSDOM } = require('jsdom');
const fs = require('fs');

const file = process.argv[2];
const html = fs.readFileSync(file, 'utf-8');
const PROG_KEY = html.match(/PROG_KEY = "([^"]+)"/)[1];

function open(seed) {
  return new JSDOM(html, {
    runScripts: 'dangerously', pretendToBeVisual: true, url: 'https://localhost/',
    beforeParse(win) {
      if (seed) win.localStorage.setItem(PROG_KEY, JSON.stringify(seed));
    },
  });
}

const fails = [];
const check = (name, ok, detail) => {
  if (!ok) fails.push(name + (detail ? ' — ' + detail : ''));
};

/* ---- 1. no history: the button is there, disabled, and explains itself ---- */
const fresh = open(null);
const units = fresh.window.__pd.everyUnit();
{
  const btn = fresh.window.document.querySelector('#hardestBtn');
  check('button rendered on a fresh app', !!btn);
  if (btn) {
    check('button disabled with no history', btn.disabled);
    const note = btn.parentNode.querySelector('.small').textContent;
    check('fresh note names the threshold',
      /Unlocks once 8 different questions have been missed \(0 so far\)/.test(note), note);
  }
}
fresh.window.close();

/* ---- 2. seeded history: 120 attempted, 30 with mistakes (wrong 30..1), plus
        one question seen a great deal and never missed. ---- */
const seed = { __history: [] };
for (let i = 0; i < 120 && i < units.length; i++) {
  const wrong = i < 30 ? 30 - i : 0;
  seed[units[i].qid] = { seen: 5 + wrong, correct: 5, wrong: wrong, streak: 0 };
}
const masteredQid = units[119].qid;
seed[masteredQid] = { seen: 80, correct: 80, wrong: 0, streak: 9 };

const dom = open(seed);
const w = dom.window, d = w.document, pd = w.__pd;
check('seeded progress was loaded', Object.keys(pd.hardestUnits()).length > 0);

const hard = pd.hardestUnits();
const wrongs = hard.map(u => seed[u.qid].wrong);
check('pool is 10% of 120 attempted', hard.length === 12, 'got ' + hard.length);
check('ranked by raw wrong count',
  wrongs.every((v, i) => i === 0 || v <= wrongs[i - 1]), wrongs.join(','));
check('worst question is first', wrongs[0] === 30, String(wrongs[0]));
check('mastered question excluded', !hard.some(u => u.qid === masteredQid));
check('nothing unseen slipped in', hard.every(u => seed[u.qid] && seed[u.qid].seen));

/* ---- 3. the button, and a round that ignores the pills ---- */
const btn = d.querySelector('#hardestBtn');
check('button enabled once the pool is ready', btn && !btn.disabled);
check('button names the count', btn && /12/.test(btn.textContent), btn && btn.textContent);
check('note says it ignores the selections',
  btn && /ignores the topic and drill-mode selections/.test(
    btn.parentNode.querySelector('.small').textContent));

// narrow the selection hard: the round must ignore it
d.querySelector('[data-sel="topics-none"]').click();
[...d.querySelectorAll('[data-topic]')].find(p => !p.classList.contains('empty')).click();
const narrowed = pd.askableUnits().length;
check('selection really was narrowed', narrowed > 0 && narrowed < units.length,
  narrowed + ' of ' + units.length);

d.querySelector('#hardestBtn').click();
const eyebrow = d.querySelector('.eyebrow').textContent;
check('round labelled hardest', /hardest/.test(eyebrow), eyebrow);
check('round is 12 long, not the selection', /1\/12/.test(eyebrow), eyebrow);

const hardNames = new Set(hard.map(u => u.card.name));
const askedNames = new Set();
let guard = 500, asked = 0;
while (guard-- > 0) {
  if (d.querySelector('.card.summary')) break;
  const name = d.querySelector('.qname');
  if (name) { askedNames.add(name.textContent); asked++; }
  const next = [...d.querySelectorAll('button')].find(b => /^(next|finish)$/i.test(b.textContent.trim()));
  if (next) { next.click(); continue; }
  const choice = [...d.querySelectorAll('button.choice')].filter(b => !b.disabled)[0];
  if (choice) { choice.click(); continue; }
  const ans = d.querySelector('#ans'), submit = d.querySelector('#submit');
  if (ans && submit && !submit.disabled) { ans.value = 'zzz'; submit.click(); continue; }
  break;
}
const outside = [...askedNames].filter(n => !hardNames.has(n));
check('round terminated', !!d.querySelector('.card.summary'));
check('only hardest questions asked', outside.length === 0, outside.slice(0, 3).join(', '));
check('summary names the round', !!d.querySelector('.card.summary') &&
  /Hardest questions complete/.test(d.querySelector('.card.summary').textContent));

/* ---- 4. an ordinary round afterwards still queues the full selection ---- */
d.querySelector('#homeBtn').click();
const nSel = pd.askableUnits().length;
d.querySelector('#startBtn').click();
const eb2 = d.querySelector('.eyebrow').textContent;
check('ordinary round back to the selection',
  eb2.indexOf('/' + nSel) !== -1 && !/hardest/.test(eb2), eb2 + ' (selection ' + nSel + ')');

console.log(file.padEnd(20), 'pool=' + hard.length, 'asked=' + asked,
  'distinct=' + askedNames.size, 'outside=' + outside.length,
  fails.length ? 'FAIL' : 'ok');
if (fails.length) { fails.forEach(f => console.error('  - ' + f)); process.exit(1); }
