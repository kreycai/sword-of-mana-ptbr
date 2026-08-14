#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reimport.py  (PASSO 1: verificacao do codificador)

O caminho de VOLTA: transformar texto -> bytes da ROM (inverso do decode_string).

Antes de escrever qualquer coisa na ROM, este script faz um teste de ROUND-TRIP:
pega cada fala original, RE-CODIFICA, e compara com os bytes originais.
Se a taxa de acerto for alta, sabemos que nosso codificador esta correto e
podemos confiar nele pra inserir traducoes.
"""

import sys, os

AQUI  = os.path.dirname(os.path.abspath(__file__))
TRAD  = os.path.dirname(AQUI)
SEISA = os.path.join(TRAD, 'SeiSaboten')
ROM   = os.path.join(TRAD, 'Sword of Mana (USA, Australia) - Copia.gba')
sys.path.insert(0, SEISA)

import globals, locations
with open(ROM, 'rb') as f:
    globals.my_file = bytearray(f.read())
globals.rom_region = 'E'
import textman
tm = textman.TextManager()

# --- Mapa dos codigos de controle (o inverso da funcao decode_string) ---
# Ex: no decode, o byte 0x80 vira '\n'. Aqui, '\n' volta a ser 0x80.
TOKEN_TO_BYTES = {
    '{A}':           b'\x82',
    '{CHOICE}':      b'\x83',
    '{END_CHOICES}': b'\x84',
    '{RED}':         b'\x8e',
    '{END_COLOR}':   b'\x8d',
    '{HERO}':        b'\x86\x00',
    '{HEROINE}':     b'\x86\x01',
}

class TokenNaoSuportado(Exception):
    pass

def encode_string(s):
    """Texto (com tokens {..} e \\n) -> bytes da ROM. Inverso do decode_string."""
    out = bytearray()
    i = 0
    while i < len(s):
        c = s[i]
        if c == '\n':
            out += b'\x80'            # quebra de linha
            i += 1
        elif c == '{':
            j = s.find('}', i)
            if j == -1:
                raise TokenNaoSuportado("chave { sem fechar")
            tok = s[i:j+1]
            if tok in TOKEN_TO_BYTES:
                out += TOKEN_TO_BYTES[tok]
            else:
                raise TokenNaoSuportado(tok)   # ex: {RED}, ACTORx, POS_L... raros
            i = j + 1
        else:
            code = tm.inv_char_dict.get(c)
            if code is None:
                raise TokenNaoSuportado(f"char {c!r}")   # ex: acentos que a fonte nao tem
            out += code.to_bytes(2, byteorder='big')      # letras = 2 bytes, big-endian
            i += 1
    return bytes(out)

# --- Round-trip: re-codifica cada fala e compara com o original ---
iguais = 0
diferentes = 0
com_token_raro = 0
amostras_erro = []

for d in tm.story_table_list:
    s = d['string']
    if s == '{BLANK}' or not s:
        continue
    start, end = d['start'], d['end']
    body_start = start + 3 if d['actor'] else start   # pula os 3 bytes do "ator"
    original = bytes(globals.my_file[body_start:end])
    try:
        recodificado = encode_string(s)
    except TokenNaoSuportado as e:
        com_token_raro += 1
        continue
    if recodificado == original:
        iguais += 1
    else:
        diferentes += 1
        if len(amostras_erro) < 5:
            amostras_erro.append((d['id'], s[:40], original[:16].hex(), recodificado[:16].hex()))

total_testado = iguais + diferentes
print("=== VERIFICACAO DO CODIFICADOR (round-trip) ===")
print(f"Falas testadas (codificaveis) : {total_testado}")
print(f"  IGUAIS ao original (perfeito): {iguais}")
print(f"  diferentes                   : {diferentes}")
print(f"Puladas (tokens raros/acentos) : {com_token_raro}")
if total_testado:
    print(f"\nTaxa de acerto: {100*iguais/total_testado:.2f}%")

if amostras_erro:
    print("\n-- exemplos de divergencia --")
    for id_, txt, orig, novo in amostras_erro:
        print(f"  #{id_}: {txt!r}\n     orig: {orig}\n     novo: {novo}")
