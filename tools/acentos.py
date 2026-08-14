#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Acentos do Sword of Mana (USA/AUS, regiao E).

FONTE DE DIALOGO: glifo(codigo) = 0xD58A64 + codigo*32 (1bpp, bitmap nos 16
primeiros bytes de cada glifo de 32, row-major, LSB=esquerda, 8x16).

DESCOBERTA (testando no mGBA com bloco solido): o char = (a<<8)|b so alcanca a
fonte latina com a=0x00 e b < 0x80. E MAIS: os codigos **0x67-0x6E sao "mortos"**
pra texto (o jogo nao renderiza o glifo deles) — provavelmente a engine remapeia
essa sub-faixa. Codigos que FUNCIONAM (identidade char->glifo confirmada no jogo):
0x00-0x66 e 0x6F-0x7E. Entao os acentuados que caiam em 0x67-0x6E (ou >=0x80)
foram realocados pra slots livres NESSAS faixas boas (chars que o PT nao usa:
È Ù Û Ü ß è ë).
"""

FONT_BASE = 0xD58A64
GLYPH_STRIDE = 32

# char -> codigo. TODOS em faixa que funciona (0x5F-0x66 ou 0x6F-0x7E).
ACENTO_CODE = {
    # maiusculas em faixa boa (originais)
    'À': 0x5F, 'Á': 0x60, 'Â': 0x61, 'Ã': 0x62, 'Ç': 0x63,
    'É': 0x65, 'Ê': 0x66, 'Ô': 0x6F, 'Õ': 0x70, 'Ú': 0x72,
    # maiusculas realocadas (Í e Ó estavam na faixa morta 0x69/0x6E)
    'Í': 0x64,  # slot do È
    'Ó': 0x7E,  # slot do ë
    # minusculas originais em faixa boa
    'à': 0x76, 'á': 0x77, 'â': 0x78, 'ã': 0x79, 'ç': 0x7A, 'é': 0x7C, 'ê': 0x7D,
    # minusculas realocadas (estavam na faixa morta 0x67-0x6D)
    'í': 0x71,  # slot do Ù
    'ó': 0x73,  # slot do Û
    'ô': 0x74,  # slot do Ü
    'õ': 0x75,  # slot do ß
    'ú': 0x7B,  # slot do è
}

# COMPOR glifo novo (nao existia): (alvo, base_letra, doador_til, [(dst,src)...], [limpar])
_COMPOR = [
    (0x79, 0x77, 0x83, [(1, 1), (2, 2)], [0, 1, 2, 3]),  # ã: a + til do ñ
    (0x62, 0x60, 0x6C, [(0, 0), (1, 1)], [0, 1, 2]),     # Ã: A + til do Ñ
    (0x70, 0x6E, 0x6C, [(0, 0), (1, 1)], [0, 1, 2]),     # Õ: O(Ó) + til do Ñ
    (0x75, 0x85, 0x83, [(1, 1), (2, 2)], [0, 1, 2, 3]),  # õ: o(ó) + til do ñ  -> slot 0x75
]

# COPIAR glifo existente pra slot em faixa boa
_COPIAR = [
    (0x71, 0x80),  # í: 0x80 -> 0x71
    (0x73, 0x85),  # ó: 0x85 -> 0x73
    (0x74, 0x86),  # ô: 0x86 -> 0x74
    (0x7B, 0x89),  # ú: 0x89 -> 0x7B
    (0x64, 0x69),  # Í: 0x69 -> 0x64
    (0x7E, 0x6E),  # Ó: 0x6E -> 0x7E
]

def _off(code):
    return FONT_BASE + code * GLYPH_STRIDE

def patch_fonte(mf):
    """COMPOR antes de COPIAR (composicoes leem os originais em 0x6C/0x6E)."""
    for alvo, base, doador, til_rows, clear_rows in _COMPOR:
        g = bytearray(mf[_off(base):_off(base) + 32])
        til = mf[_off(doador):_off(doador) + 32]
        for r in clear_rows:
            g[r] = 0
        for dst, src in til_rows:
            g[dst] = til[src]
        mf[_off(alvo):_off(alvo) + 32] = g
    for alvo, src in _COPIAR:
        mf[_off(alvo):_off(alvo) + 32] = mf[_off(src):_off(src) + 32]
    return mf
