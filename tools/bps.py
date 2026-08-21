#!/usr/bin/env python3
"""Gerador e aplicador de patch BPS.

BPS e o formato padrao da cena de romhacking atual: carrega CRC32 da origem, do
destino e do proprio patch, entao o usuario descobre na hora se pegou a ROM
errada -- ao contrario do IPS, que aplica em cima de qualquer coisa e produz
lixo em silencio. Tambem nao tem o limite de 16 MB do IPS, o que importa aqui
porque a ROM do Sword of Mana foi expandida pra 32 MB.

uso:
  bps.py criar  <origem> <destino> <saida.bps>
  bps.py aplicar <origem> <patch.bps> <saida>
  bps.py testar  <origem> <destino> <patch.bps>     (gera, aplica e compara)
"""
import sys
import zlib


def _num(n):
    """Numero variavel do BPS: 7 bits por byte, o ultimo marcado com 0x80,
    e cada byte seguinte decrementado de 1."""
    out = bytearray()
    while True:
        x = n & 0x7F
        n >>= 7
        if n == 0:
            out.append(0x80 | x)
            break
        out.append(x)
        n -= 1
    return bytes(out)


def _read_num(d, p):
    n, shift = 0, 0
    while True:
        x = d[p]; p += 1
        n += (x & 0x7F) << shift
        if x & 0x80:
            return n, p
        shift += 7
        n += 1 << shift


def create(src, dst, rle_min=24):
    """Gera o patch.

    Usa SourceRead (trecho igual a origem na mesma posicao), TargetRead (dados
    literais) e **TargetCopy pra sequencias repetidas**. O TargetCopy le do que
    ja foi escrito na SAIDA e pode se sobrepor, o que da RLE de graca: escreve 1
    byte literal e copia N-1 a partir dele.

    Isso importa muito pra ROM EXPANDIDA (ex: Sword of Mana, 16 MB -> 32 MB): a
    area nova e quase toda padding zerado. Sem RLE, esses megabytes entram como
    literal e o patch fica do tamanho da propria expansao.
    """
    out = bytearray(b'BPS1')
    out += _num(len(src)) + _num(len(dst)) + _num(0)

    n = len(dst)
    i = 0
    trel = 0
    while i < n:
        # 1) trecho igual a origem, na mesma posicao -> SourceRead (custa ~nada)
        j = i
        while j < n and j < len(src) and dst[j] == src[j]:
            j += 1
        if j > i:
            out += _num(((j - i - 1) << 2) | 0)
            i = j
            continue

        # 2) sequencia longa do mesmo byte -> 1 literal + TargetCopy sobreposto
        k = i
        while k < n and dst[k] == dst[i] and not (k < len(src) and dst[k] == src[k]):
            k += 1
        if k - i >= rle_min:
            out += _num((0 << 2) | 1) + dst[i:i + 1]          # TargetRead de 1 byte
            length = k - i - 1
            delta = i - trel                                   # aponta pro byte escrito
            out += _num(((length - 1) << 2) | 3)               # TargetCopy
            out += _num((abs(delta) << 1) | (1 if delta < 0 else 0))
            trel = i + length
            i = k
            continue

        # 3) resto -> TargetRead literal, ate voltar a bater com a origem
        #    (parando tambem numa sequencia longa, que o passo 2 aproveita)
        j = i
        while j < n and not (j < len(src) and dst[j] == src[j]):
            m = j
            while m < n and dst[m] == dst[j] and not (m < len(src) and dst[m] == src[m]):
                m += 1
            if m - j >= rle_min and m > i:
                break
            j = m if m > j else j + 1
        out += _num(((j - i - 1) << 2) | 1)
        out += dst[i:j]
        i = j

    out += zlib.crc32(src).to_bytes(4, 'little')
    out += zlib.crc32(dst).to_bytes(4, 'little')
    out += zlib.crc32(bytes(out)).to_bytes(4, 'little')
    return bytes(out)


def apply(src, patch):
    if patch[:4] != b'BPS1':
        raise ValueError('nao e um patch BPS')
    if zlib.crc32(patch[:-4]) != int.from_bytes(patch[-4:], 'little'):
        raise ValueError('o patch esta corrompido (CRC do patch nao bate)')
    want_src = int.from_bytes(patch[-12:-8], 'little')
    if zlib.crc32(src) != want_src:
        raise ValueError(f'ROM de origem errada: esperado CRC32 {want_src:08X}, '
                         f'recebido {zlib.crc32(src):08X}')
    p = 4
    ssize, p = _read_num(patch, p)
    tsize, p = _read_num(patch, p)
    msize, p = _read_num(patch, p)
    p += msize
    out = bytearray()
    srel = trel = 0
    end = len(patch) - 12
    while p < end:
        v, p = _read_num(patch, p)
        action, length = v & 3, (v >> 2) + 1
        if action == 0:
            o = len(out)
            out += src[o:o + length]
        elif action == 1:
            out += patch[p:p + length]; p += length
        elif action == 2:
            d, p = _read_num(patch, p)
            srel += (-1 if d & 1 else 1) * (d >> 1)
            out += src[srel:srel + length]; srel += length
        else:
            d, p = _read_num(patch, p)
            trel += (-1 if d & 1 else 1) * (d >> 1)
            for _ in range(length):
                out.append(out[trel]); trel += 1
    if len(out) != tsize:
        raise ValueError('tamanho final nao bate')
    if zlib.crc32(bytes(out)) != int.from_bytes(patch[-8:-4], 'little'):
        raise ValueError('CRC do resultado nao bate')
    return bytes(out)


def main():
    cmd = sys.argv[1]
    if cmd == 'criar':
        src = open(sys.argv[2], 'rb').read()
        dst = open(sys.argv[3], 'rb').read()
        pt = create(src, dst)
        open(sys.argv[4], 'wb').write(pt)
        print(f'patch: {len(pt):,} bytes  ({100*len(pt)/len(dst):.2f}% do destino)'
              .replace(',', '.'))
        print(f'CRC32 origem  {zlib.crc32(src):08X}   destino {zlib.crc32(dst):08X}')
    elif cmd == 'aplicar':
        src = open(sys.argv[2], 'rb').read()
        pt = open(sys.argv[3], 'rb').read()
        open(sys.argv[4], 'wb').write(apply(src, pt))
        print('aplicado, CRC conferido')
    elif cmd == 'testar':
        src = open(sys.argv[2], 'rb').read()
        dst = open(sys.argv[3], 'rb').read()
        pt = create(src, dst)
        open(sys.argv[4], 'wb').write(pt)
        got = apply(src, pt)
        print(f'patch {len(pt):,} bytes -- round-trip: {"IDENTICO" if got == dst else "FALHOU"}'
              .replace(',', '.'))
        return 0 if got == dst else 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
