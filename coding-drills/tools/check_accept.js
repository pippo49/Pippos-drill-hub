/* Checks on the accept-lists that are NOT tautological.
 *
 * The obvious test — "does each accepted alternative grade exact?" — is
 * worthless, and I wrote it that way first. gradeAny compares the typed answer
 * against every accept entry, so an entry always matches itself; the check
 * passed even after a deliberately nonsensical alternative was inserted. It
 * proved only that gradeAny reads its own argument.
 *
 * These three are real:
 *
 *   1. NOT REDUNDANT — the plain grader must not already accept the entry.
 *      An alternative that differs only in whitespace or quoting is dead
 *      weight: it looks like tolerance while widening nothing, which hides the
 *      absence of the real alternative it was meant to be.
 *
 *   2. NOT TOO LOOSE — obvious nonsense must not grade exact, and the typo
 *      tolerance must not swallow a semantically opposite flag (--soft for
 *      --hard is four characters and a completely different outcome).
 *
 * A third check — "no two questions share an answer" — was tried and removed.
 * It flags normal decks: many different Python snippets legitimately print
 * TypeError, and --all legitimately fills a blank in both git add and git log.
 * The question text is what distinguishes them, so a shared answer is not
 * ambiguity, and the check produced nothing but false positives.
 *
 *     node tools/check_accept.js <file>.html
 */
const { JSDOM } = require('jsdom');
const fs = require('fs');

const file = process.argv[2];
const html = fs.readFileSync(file, 'utf-8');
const dom = new JSDOM(html, { runScripts: 'dangerously', url: 'https://localhost/' });
const pd = dom.window.__pd;

const TEXT_MODES = ['predict', 'fill', 'recall', 'command', 'history', 'rows'];
const bad = [];
const items = [];

pd.DECK_DATA.cards.forEach(card => {
  TEXT_MODES.forEach(mode => {
    (card[mode] || []).forEach((it, i) => {
      items.push({
        qid: `${card.id}:${mode}:${i}`, mode,
        expected: mode === 'predict' ? it.output : it.answer,
        accept: it.accept || [],
        grader: mode === 'predict' ? pd.gradeOutput : pd.gradeText,
      });
    });
  });
});

// 1. no redundant alternatives
let alts = 0;
items.forEach(it => {
  it.accept.forEach(alt => {
    alts++;
    if (it.grader(alt, it.expected) === 'exact') {
      bad.push(`${it.qid}: accept "${alt}" is redundant — the grader already accepts it`);
    }
  });
});

// 2. grading is not too loose
items.forEach(it => {
  if (pd.gradeAny('zzz-definitely-not-this', it.expected, it.accept, it.grader) === 'exact') {
    bad.push(`${it.qid}: nonsense grades exact`);
  }
});
// the flags that mean opposite things must never collide
const OPPOSITES = [
  ['git reset --soft HEAD~1', 'git reset --hard HEAD~1'],
  ['git stash pop', 'git stash apply'],
  ['git push --force-with-lease', 'git push --force'],
  ['git rm --cached f', 'git rm f'],
];
OPPOSITES.forEach(([a, b]) => {
  if (pd.gradeText(b, a) === 'exact') bad.push(`grading collapses "${a}" and "${b}"`);
});

console.log(`${file.padEnd(18)} ${items.length} answers, ${alts} alternatives  ` +
            (bad.length ? 'FAIL' : 'ok'));
if (bad.length) { bad.forEach(b => console.error('  - ' + b)); process.exit(1); }
