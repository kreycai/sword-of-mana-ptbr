#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_nointro.py — gera o patch BPS mirando o dump **No-Intro**, que e o que as
pessoas tem, sem precisar ter o arquivo em maos.

CONTEXTO. A traducao foi construida sobre `Sword of Mana (USA, Australia) - Copia.gba`
(CRC32 FACBDF03), que NAO e um dump limpo: e o dump No-Intro (CRC32 7F1EAC75,
SHA-1 a7ff0b4482c7c3b19467af37c3e277321cd9f1cd) com um rascunho de traducao feito
a mao nas falas 84-121 e 1894 — 2.215 bytes em 54 faixas dentro da tabela de
dialogo. Foi por isso que, no lancamento de 14/08/2026, ninguem no forum achou uma
ROM com CRC FACBDF03, e o patch teve que ser re-mirado em 16/08.

COMO ISSO FUNCIONA SEM A ROM No-Intro. O patch v1 publicado (No-Intro -> ROM
so-dialogo) e um mapa: onde ele usou SourceRead, a origem e IGUAL ao destino
naquele offset — logo aqueles bytes da No-Intro sao conhecidos. Onde usou
TargetRead, a origem e desconhecida. Montamos uma origem sintetica com os bytes
conhecidos e, nos desconhecidos, um valor DIFERENTE do destino de proposito: assim
o gerador nunca emite "copiar da origem" ali, e o patch resultante jamais le um
byte que a gente nao conhece. Isso e verificado explicitamente no fim.

uso:  patch_nointro.py <patch_v1.bps> <rom_so_dialogo.gba> <rom_nova.gba> <saida.bps>
"""

import sys, os, zlib

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(AQUI)))   # .../traducao, onde vive bps.py
import bps

NOINTRO_CRC32 = 0x7F1EAC75
NOINTRO_SHA1  = 'a7ff0b4482c7c3b19467af37c3e277321cd9f1cd'


def _num(d, p):
    n, sh = 0, 0
    while True:
        x = d[p]; p += 1
        n += (x & 0x7F) << sh
        if x & 0x80:
            return n, p
        sh += 7
        n += 1 << sh


def acoes(patch):
    """Percorre um BPS e devolve (tamanho_origem, [(pos, len, acao)])."""
    p = 4
    ssize, p = _num(patch, p)
    tsize, p = _num(patch, p)
    msize, p = _num(patch, p)
    p += msize
    fim = len(patch) - 12
    pos, saida = 0, []
    while p < fim:
        v, p = _num(patch, p)
        act, ln = v & 3, (v >> 2) + 1
        if act == 1:
            p += ln
        elif act in (2, 3):
            _, p = _num(patch, p)
        saida.append((pos, ln, act))
        pos += ln
    return ssize, tsize, saida


def origem_conhecida(patch_v1, alvo_v1):
    """Bytes da No-Intro que o patch v1 prova, + mascara de conhecidos."""
    ssize, tsize, acts = acoes(patch_v1)
    if tsize != len(alvo_v1):
        raise SystemExit(f'a ROM so-dialogo tem {len(alvo_v1)} bytes, o patch v1 '
                         f'espera {tsize} — arquivo errado')
    if zlib.crc32(alvo_v1) != int.from_bytes(patch_v1[-8:-4], 'little'):
        raise SystemExit('a ROM so-dialogo nao e o destino do patch v1 (CRC32 nao bate)')
    conhecido = bytearray(ssize)
    mask = bytearray(ssize)
    for pos, ln, act in acts:
        if act == 0:                      # origem == destino nesse trecho
            n = min(ln, max(0, ssize - pos))
            conhecido[pos:pos + n] = alvo_v1[pos:pos + n]
            mask[pos:pos + n] = b'\x01' * n
    return conhecido, mask


def gerar(patch_v1, alvo_v1, alvo_novo):
    conhecido, mask = origem_conhecida(patch_v1, alvo_v1)
    ssize = len(conhecido)

    # origem sintetica: conhecidos de verdade; desconhecidos com valor
    # PROPOSITALMENTE diferente do destino, pra nunca virar SourceRead
    S = bytearray(conhecido)
    desconhecidos = 0
    for i in range(ssize):
        if not mask[i]:
            S[i] = alvo_novo[i] ^ 0xFF
            desconhecidos += 1

    patch = bytearray(bps.create(bytes(S), alvo_novo))

    # PROVA: nenhum SourceRead/SourceCopy encosta em byte desconhecido
    _, _, acts = acoes(bytes(patch))
    for pos, ln, act in acts:
        if act in (0, 2):
            for i in range(pos, min(pos + ln, ssize)):
                if not mask[i]:
                    raise RuntimeError(f'patch leria byte desconhecido da origem em '
                                       f'0x{i:X} — abortado')

    # o round-trip contra a origem sintetica tem que dar o destino exato
    if bps.apply(bytes(S), bytes(patch)) != alvo_novo:
        raise RuntimeError('round-trip falhou contra a origem sintetica')

    # trocar o CRC32 da origem pelo da No-Intro de verdade e refazer o CRC do patch
    patch[-12:-8] = NOINTRO_CRC32.to_bytes(4, 'little')
    patch[-4:] = zlib.crc32(bytes(patch[:-4])).to_bytes(4, 'little')
    return bytes(patch), desconhecidos


def main():
    v1, ant, novo, saida = sys.argv[1:5]
    patch_v1 = open(v1, 'rb').read()
    alvo_v1 = open(ant, 'rb').read()
    alvo_novo = open(novo, 'rb').read()
    patch, desc = gerar(patch_v1, alvo_v1, alvo_novo)
    open(saida, 'wb').write(patch)
    print(f'{saida}')
    print(f'  {len(patch):,} bytes'.replace(',', '.'))
    print(f'  origem  CRC32 {NOINTRO_CRC32:08X}  (dump No-Intro, SHA-1 {NOINTRO_SHA1})')
    print(f'  destino CRC32 {zlib.crc32(alvo_novo):08X}  {len(alvo_novo):,} bytes'
          .replace(',', '.'))
    print(f'  bytes da origem desconhecidos (entram como literal): {desc}')
    print('  [OK] nenhum SourceRead/SourceCopy toca byte desconhecido; round-trip exato')


if __name__ == '__main__':
    main()
