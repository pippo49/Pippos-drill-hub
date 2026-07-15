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
for(const mode of %s){
  let ok=0,fail=0;
  for(let i=0;i<400;i++){try{if(generateQuestion(mode))ok++;}catch(e){fail++;if(fail===1)console.log(mode,'ERR',e.message);}}
  console.log(mode,'ok='+ok,'fail='+fail);
  if(fail>0||ok===0)bad++;
}
// data hygiene: no blank forms, cloze braces well-formed
let blank=0,braces=0;
for(const e of VOCAB_DATA.entries){
  for(const f of ['noun_decl','conjugation','declension']) if(e[f]) for(const k in e[f]) if(!e[f][k]) blank++;
  if(e.cloze) for(const s of e.cloze){const t=s.pl||s.es||''; if((t.match(/\\{/g)||[]).length!==1) braces++;}
}
console.log('blank forms:',blank,'| cloze brace errors:',braces);
if(bad||blank||braces){console.log('VALIDATION FAILED');process.exit(1);}
console.log('VALIDATION PASSED');
''' % json.dumps(modes)
    run = os.path.join(tmp, 'run.js')
    open(run, 'w', encoding='utf-8').write(probe)
    subprocess.run(['node', run], check=True)

if __name__ == '__main__':
    main(sys.argv[1])
