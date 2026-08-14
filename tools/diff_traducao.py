#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diff_traducao.py - mostra EXATAMENTE quais falas mudaram entre a ROM original
e uma ROM traduzida (compara o texto decodificado, fala por fala).

Uso:
    python3 tools/diff_traducao.py                       # compara com a "pt-BR teste"
    python3 tools/diff_traducao.py "outra_rom.gba"       # compara com outra ROM
"""

import sys, os, json

AQUI  = os.path.dirname(os.path.abspath(__file__))
TRAD  = os.path.dirname(AQUI)
SEISA = os.path.join(TRAD, 'SeiSaboten')
ORIG_JSON = os.path.join(TRAD, 'texto_extraido', 'dialogo.json')   # export da ROM original
ROM_TRAD  = sys.argv[1] if len(sys.argv) > 1 else os.path.join(TRAD, 'Sword of Mana (pt-BR teste).gba')
sys.path.insert(0, SEISA)

# 1) texto ORIGINAL (do JSON que ja exportamos)
original = {d['id']: d['texto'] for d in json.load(open(ORIG_JSON, encoding='utf8'))}

# 2) texto da ROM TRADUZIDA (lendo direto dela)
import globals, locations
globals.my_file = bytearray(open(ROM_TRAD, 'rb').read())
globals.rom_region = 'E'
import textman
tm = textman.TextManager()

# 3) compara fala por fala
mudou = []
for e in tm.story_table_list:
    novo  = e['string']
    velho = original.get(e['id'])
    if velho != novo:
        mudou.append((e['id'], velho, novo))

print(f"ROM traduzida: {os.path.basename(ROM_TRAD)}")
print(f"Falas alteradas: {len(mudou)}\n")
for id_, velho, novo in mudou:
    print(f"========== #{id_} ==========")
    print("--- ORIGINAL (EN) ---")
    print(velho)
    print("--- TRADUZIDO (pt-BR) ---")
    print(novo)
    print()
