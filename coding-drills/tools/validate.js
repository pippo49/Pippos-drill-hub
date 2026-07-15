const { JSDOM } = require('jsdom');
const fs = require('fs');

const file = process.argv[2];
const html = fs.readFileSync(file, 'utf-8');

const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true, url: 'https://localhost/' });
const w = dom.window, d = w.document;
const pd = w.__pd;
if (!pd) { console.error('no __pd export'); process.exit(1); }

function q(sel){ return d.querySelector(sel); }
function text(sel){ const n=q(sel); return n ? n.textContent : null; }

// 1. Home screen: progress card should exist with the empty-state message
const panelheads = [...d.querySelectorAll('.panelhead')].map(n=>n.textContent.trim());
if(!panelheads.some(t=>t.startsWith('Progress'))) { console.error('FAIL: no Progress card'); process.exit(1); }
const progCard0 = [...d.querySelectorAll('.card')].find(c => (c.querySelector('.panelhead')||{}).textContent === 'Progress');
console.log('home: Progress card present (empty state:',
  /No answers recorded yet/.test(progCard0.textContent), ')');

// 2. Start a round
q('#startBtn').click();
let answered = 0, guard = 20000;
const modesSeen = new Set();

while (guard-- > 0) {
  // summary reached?
  if (d.querySelector('.card.summary')) break;

  const nextBtn = [...d.querySelectorAll('button')].find(b => /^(next|finish)$/i.test(b.textContent.trim()));
  if (nextBtn) { nextBtn.click(); continue; }
  const choices = [...d.querySelectorAll('button.choice')].filter(b => !b.disabled);
  if (choices.length) { choices[0].click(); answered++; modesSeen.add('mc'); continue; }
  const ans = q('#ans'), submit = q('#submit');
  if (ans && submit && !submit.disabled) {
    ans.value = 'zzz-wrong-answer';
    submit.click(); answered++; modesSeen.add('text');
    continue;
  }
  console.error('FAIL: stuck, no actionable control'); process.exit(1);
}
if (guard <= 0) { console.error('FAIL: round did not terminate'); process.exit(1); }
console.log('round: completed after', answered, 'answers; input kinds:', [...modesSeen].join('+'));

// 3. Summary sanity + re-drill button (all answers were wrong)
const hasRedrill = [...d.querySelectorAll('button')].some(b => /re-drill/i.test(b.textContent));
console.log('summary: re-drill button present:', hasRedrill);

// 4. Progress persisted: wrong counts + history
const prog = JSON.parse(w.localStorage.getItem(
  html.match(/PROG_KEY = "([^"]+)"/)[1]));
const hist = prog.__history || [];
const qids = Object.keys(prog).filter(k => k !== '__history');
const withWrong = qids.filter(k => (prog[k].wrong||0) > 0).length;
console.log('storage:', qids.length, 'qids,', withWrong, 'with wrong>0, history length', hist.length,
  '(capped<=200:', hist.length <= 200, ')');
if (!hist.length || !withWrong) { console.error('FAIL: history or wrong counts missing'); process.exit(1); }

// 5. Back home: progress card should now show stats + topic bars
const doneBtn = [...d.querySelectorAll('button')].find(b => /done/i.test(b.textContent));
doneBtn.click();
const progCard = [...d.querySelectorAll('.card')].find(c => (c.querySelector('.panelhead')||{}).textContent === 'Progress');
const hasStats = /questions attempted/.test(progCard.textContent) && /% correct/.test(progCard.textContent);
const barCount = progCard.querySelectorAll('.bars .bar').length;
console.log('home after round: stats line:', hasStats, '· topic bars:', barCount);
if (!hasStats || !barCount) { console.error('FAIL: progress card not populated'); process.exit(1); }

console.log('PASS:', file);
