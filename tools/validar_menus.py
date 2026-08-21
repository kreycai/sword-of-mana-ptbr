#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""validar_menus.py — audita traducao_menus.json antes de montar a ROM.

Checa tres coisas:
  1) todo caractere e codificavel pela fonte do jogo;
  2) LARGURA: a fonte e de largura FIXA, 6px por caractere (medido casando os
     glifos contra um dump de VRAM do jogo rodando). Entao contar caracteres E
     medir largura. O orcamento de cada sub-tabela e o comprimento da MAIOR
     string original dela — largura que o jogo comprovadamente acomoda;
  3) indices validos e sub-tabela nao-intocavel.
"""
import sys, os, re, json
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import menus

TRAD = os.path.dirname(AQUI)
CJK = re.compile(r'[　-鿿＀-￯]')
FONTE_MAP = {'"': '”', '—': '-', '–': '-', 'º': 'o', 'ª': 'a', 'о': 'o',
             '‘': '’', '\\': '', '“': '”', 'ü': 'u'}

mf, tm, mt = menus.carregar(os.path.join(TRAD, 'Sword of Mana (USA, Australia) - Copia.gba'))
trad = json.load(open(os.path.join(TRAD, 'traducao_menus.json'), encoding='utf8'))

erros, avisos, n = [], [], 0
for tb_s, ents in sorted(trad.items(), key=lambda kv: int(kv[0])):
    tb = int(tb_s)
    if tb in menus.INTOCAVEIS:
        erros.append(f'[{tb}] sub-tabela INTOCAVEL'); continue
    txts = mt.sub_textos(tb)
    orc = max((len(t) for t in txts if t.strip() and not CJK.search(t)
               and re.search(r'[A-Za-z]', t)), default=0)
    for k_s, v in sorted(ents.items(), key=lambda kv: int(kv[0])):
        k = int(k_s); n += 1
        if k >= len(txts):
            erros.append(f'[{tb}:{k}] indice fora da tabela (n={len(txts)})'); continue
        v2 = ''.join(FONTE_MAP.get(c, c) for c in v)
        try:
            mt.encode(v2)
        except ValueError as e:
            erros.append(f'[{tb}:{k}] {e}')
        if len(v2) > orc:
            msg = (f'[{tb}:{k}] {len(v2)} chars > orcamento {orc} '
                   f'(+{len(v2)-orc}) {v!r} <- {txts[k]!r}')
            (avisos if len(v2) - orc <= 1 else erros).append(msg)

print(f'{n} strings verificadas em {len(trad)} sub-tabelas')
if avisos:
    print(f'\n{len(avisos)} AVISO(S) — 1 char (6px) acima do maior original, tolerado:')
    for a in avisos: print('  ' + a)
if erros:
    print(f'\n{len(erros)} ERRO(S):')
    for e in erros: print('  ' + e)
    sys.exit(1)
print('\n[OK] tudo codificavel e dentro da largura.')
