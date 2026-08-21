#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dump_menu.py TAB [TAB...] — mostra as entradas traduziveis de sub-tabelas da master table."""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import menus
TRAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mf, tm, mt = menus.carregar(os.path.join(TRAD, 'Sword of Mana (USA, Australia) - Copia.gba'))
CJK = re.compile(r'[　-鿿＀-￯]')
feito = {}
p = os.path.join(TRAD, 'traducao_menus.json')
if os.path.exists(p): feito = json.load(open(p, encoding='utf8'))
for arg in sys.argv[1:]:
    i = int(arg)
    txts = mt.sub_textos(i)
    alvo = [(k, t) for k, t in enumerate(txts) if t.strip() and not CJK.search(t) and re.search(r'[A-Za-z]', t)]
    orc = max((len(t) for _, t in alvo), default=0)
    ja = feito.get(str(i), {})
    print(f'### tabela {i} — {len(alvo)} traduziveis de {len(txts)} | orcamento {orc} chars')
    for k, t in alvo:
        mark = ' -> ' + repr(ja[str(k)]) if str(k) in ja else ''
        print(f'  {k}: {t!r}{mark}')
