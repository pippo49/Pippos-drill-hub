#!/usr/bin/env python3
"""Validate a trainer build: JS syntax check + runtime probe of every drill mode.
Usage: python scripts/validate.py <trainer.html>
Requires node. Auto-detects modes from MODE_LABELS. Fails (exit 1) on any error."""
import re, sys, subprocess, tempfile, os, json

def main(html_path):
    html = open(html_path, encoding='utf-8').read()
    js = html.split('<script>', 1)[1].rsplit('</script>', 1)[0]
    tmp = tempfile.mkdtemp()
    check = os.path.join(tmp, 'check.js')
    open(check, 'w', encoding='utf-8').write(js)
    subprocess.run(['node', '--check', check], check=True)
    print('syntax OK')

    m = re.search(r'MODE_LABELS\s*=\s*\[(.*?)\]\s*;', js, re.S)
    modes = re.findall(r'\[\s*"([a-z_]+)"', m.group(1))
    print('modes:', ','.join(modes))

    stub = open(os.path.join(os.path.dirname(__file__), 'dom_stub.js'), encoding='utf-8').read()
    probe = stub + js + '''
let bad=0;
// The answer input's placeholder is built from answerLabel, which is EITHER a
// language ("Polish") or the kind of thing wanted ("Antonym", "Form"). Only a
// language takes "in", and only a question that says so with answerIn gets it;
// the shared line used to read "Your answer in synonym..." for four of Polish's
// six labels and for every one of the medical trainer's. Collect what each mode
// would actually show, so a new mode cannot reintroduce it.
const placeholders={},promptLabels={};
for(const mode of %s){
  let ok=0,fail=0;
  for(let i=0;i<400;i++){try{const q=generateQuestion(mode);if(q){ok++;
    promptLabels[q.promptLabel]=true;
    if(!q.choices)placeholders[q.answerIn?'in|'+q.answerLabel:'bare|'+q.answerLabel]=mode;}
  }catch(e){fail++;if(fail===1)console.log(mode,'ERR',e.message);}}
  console.log(mode,'ok='+ok,'fail='+fail);
  if(fail>0||ok===0)bad++;
}
// Which labels are languages is decided by the app's own output, not a list
// here: a translation mode uses the language name as its promptLabel too
// ("Polish" -> "German"), while "Antonym"/"Form"/"Word" never appear as one.
// So an answerLabel that is also somebody's promptLabel names a language and
// must take "in"; one that is not, must not.
let phBad=0;
Object.keys(placeholders).forEach(k=>{
  const bare=k.startsWith('bare|'), label=k.slice(bare?5:3), isLang=!!promptLabels[label];
  if(bare&&isLang){console.log('placeholder: "Your '+label.toLowerCase()+'..." — '+label+' is a language, so it needs "answer in" ('+placeholders[k]+')');phBad++;}
  if(!bare&&!isLang){console.log('placeholder: "Your answer in '+label.toLowerCase()+'..." — '+label+' is not a language ('+placeholders[k]+')');phBad++;}
});
console.log('placeholders:',Object.keys(placeholders).map(k=>k.startsWith('in|')?'"Your answer in '+k.slice(3).toLowerCase()+'..."':'"Your '+k.slice(5).toLowerCase()+'..."').sort().join(' '));
// data hygiene: no blank forms, cloze braces well-formed
let blank=0,braces=0;
// Paradigm groups are {key: form} in the Polish/Spanish decks but nested one
// level deeper in Latin (conjugation = {tense: {person: form}}), so recurse.
const countBlank = (o) => {
  for(const k in o){
    const v=o[k];
    if(v && typeof v === 'object') countBlank(v);
    else if(!v) blank++;
  }
};
for(const e of VOCAB_DATA.entries){
  for(const f of ['noun_decl','conjugation','declension']) if(e[f]) countBlank(e[f]);
  // The target-language key differs per deck (pl/es/la/it/...); it is simply
  // whichever key is not the English gloss, so don't hardcode the list.
  if(e.cloze) for(const s of e.cloze){
    const k=Object.keys(s).find(k=>k!=='en');
    const t=(k&&s[k])||'';
    if((t.match(/\\{/g)||[]).length!==1) braces++;
  }
}
console.log('blank forms:',blank,'| cloze brace errors:',braces);
if(bad||blank||braces||phBad){console.log('VALIDATION FAILED');process.exit(1);}
console.log('VALIDATION PASSED');
''' % json.dumps(modes)
    run = os.path.join(tmp, 'run.js')
    open(run, 'w', encoding='utf-8').write(probe)
    subprocess.run(['node', run], check=True)

if __name__ == '__main__':
    main(sys.argv[1])
