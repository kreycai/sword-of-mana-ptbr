#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exportar_dialogo.py

Reaproveita o "cerebro" do SeiSaboten (o textman.py) pra ler todo o texto
do Sword of Mana e despejar em JSON, SEM abrir a interface grafica.

Como funciona (em JS seria bem parecido):
  - a gente aponta o Python pra pasta do SeiSaboten (como um 'import' de outra pasta);
  - carrega a ROM em memoria;
  - diz que a regiao e 'E' (USA);
  - manda o TextManager fazer o trabalho pesado;
  - salva o resultado em .json.
"""

import sys, os, json

# Caminhos: este script esta em traducao/tools/ ; o SeiSaboten em traducao/SeiSaboten/
AQUI    = os.path.dirname(os.path.abspath(__file__))
TRAD    = os.path.dirname(AQUI)                      # .../traducao
SEISA   = os.path.join(TRAD, 'SeiSaboten')
ROM     = os.path.join(TRAD, 'Sword of Mana (USA, Australia) - Copia.gba')
SAIDA   = os.path.join(TRAD, 'texto_extraido')       # pasta de saida

# Faz o Python enxergar os modulos do SeiSaboten (como adicionar ao "path" de imports)
sys.path.insert(0, SEISA)

import globals          # o "estado global" compartilhado do SeiSaboten
import locations        # tabela de enderecos por regiao

# 1) Carrega a ROM num bytearray (mutavel, tipo um Buffer do Node).
with open(ROM, 'rb') as f:
    globals.my_file = bytearray(f.read())
globals.rom_region = 'E'   # E = USA/ingles (codigo AVSE)

# 2) Agora que globals esta preenchido, importamos e criamos o TextManager.
#    O __init__ dele ja LE todo o texto do jogo.
import textman
print('Lendo o texto da ROM (isso usa a engenharia reversa do SeiSaboten)...')
tm = textman.TextManager()

# 3) Prepara a pasta de saida.
os.makedirs(SAIDA, exist_ok=True)

# --- Dialogo da historia (falas dos personagens) ---
# tm.story_table_list e uma lista de dicts: {id, start, end, actor, string}
dialogo = [
    {'id': d['id'], 'actor': d['actor'], 'texto': d['string']}
    for d in tm.story_table_list
]
with open(os.path.join(SAIDA, 'dialogo.json'), 'w', encoding='utf8') as f:
    json.dump(dialogo, f, ensure_ascii=False, indent=2)

# --- Textos de menu/itens/lugares (a "master table") ---
# tm.master_table_list e uma lista de listas de strings.
with open(os.path.join(SAIDA, 'textos_menu.json'), 'w', encoding='utf8') as f:
    json.dump(tm.master_table_list, f, ensure_ascii=False, indent=2)

# 4) Relatorio na tela.
print(f'\nOK! Exportado para: {SAIDA}')
print(f'  - dialogo.json     : {len(dialogo)} falas')
print(f'  - textos_menu.json : {len(tm.master_table_list)} tabelas de texto')

print('\n=== amostra das primeiras falas com texto ===')
mostradas = 0
for d in dialogo:
    t = d['texto'].strip()
    if t and t != '{BLANK}':
        # repr() mostra as quebras de linha como \n, pra ficar visivel
        print(f"  #{d['id']}: {t[:70]!r}")
        mostradas += 1
    if mostradas >= 12:
        break
