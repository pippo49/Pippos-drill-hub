#!/usr/bin/env python3
"""Splice a vocab JSON into its trainer HTML (single self-contained build).
Usage: python scripts/rebuild.py <trainer.html> <vocab.json>
The vocab JSON is the editable source of truth; this rewrites the inline
`const VOCAB_DATA = {...}` blob in place (compact separators)."""
import json, sys

def main(html_path, vocab_path):
    html = open(html_path, encoding='utf-8').read()
    key = 'const VOCAB_DATA = '
    i = html.index(key) + len(key)
    rest = html[i:]
    _, end = json.JSONDecoder().raw_decode(rest, rest.index('{'))
    data = json.load(open(vocab_path, encoding='utf-8'))
    compact = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    open(html_path, 'w', encoding='utf-8').write(html[:i] + compact + rest[end:])
    print(f'rebuilt {html_path}: {len(data["entries"])} entries')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
