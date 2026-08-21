#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""merge_menus.py < lote.json — funde um lote {tabela: {indice: texto}} no traducao_menus.json."""
import sys, os, json
TRAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(TRAD, 'traducao_menus.json')
base = json.load(open(P, encoding='utf8')) if os.path.exists(P) else {}
novo = json.load(sys.stdin)
add = 0
for tb, ents in novo.items():
    d = base.setdefault(tb, {})
    for k, v in ents.items():
        if d.get(k) != v: add += 1
        d[k] = v
with open(P, 'w', encoding='utf8') as f:
    json.dump({k: base[k] for k in sorted(base, key=int)}, f, ensure_ascii=False, indent=2)
    f.write('\n')
print(f'{add} strings gravadas | total agora: {sum(len(v) for v in base.values())} em {len(base)} sub-tabelas')
