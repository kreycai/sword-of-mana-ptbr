#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sistema.py — o TERCEIRO bloco de texto do Sword of Mana (achado 21/08/2026).

Nem a tabela de dialogo (0x3EB0) nem a master table de menus (0x65D8) contem as
mensagens de sistema: save/load, forja, "A Button:Confirm", criacao de personagem,
NPC, Amigo/link. Elas ficam num bloco solto em **file 0xE7AD1C..0xE7BB62**
(3654 bytes, 124 segmentos separados por **0xFFFF**), logo antes do charmap do
teclado de nomes (0xE7BB62). Mesma codificacao de sempre: 2 bytes big-endian
por char; 0x11FF = quebra de linha; **0x00FD = espacador** (usado pra centralizar,
aqui representado por `·`).

NAO ACHEI o mecanismo de indice: nao existe tabela de offsets u16/u32 com esses
valores, nem ponteiro absoluto alinhado pro inicio do bloco. Provavelmente o codigo
acha a string N contando separadores 0xFFFF a partir de uma base calculada.

Consequencia pratica, e a REGRA deste modulo:
  * o bloco tem **ZERO folga** — termina exatamente onde o charmap comeca, entao o
    tamanho TOTAL nao pode crescer nem 1 byte (senao corrompe o charmap);
  * o numero de segmentos tem que ser exatamente o mesmo;
  * o tamanho de cada string individual PODE variar (isso vale se o indice for por
    contagem de separador — o caso provavel). Se um teste in-game mostrar texto
    embaralhado depois da 1a string alterada, e porque existe tabela de offsets em
    algum lugar: ai e so ligar ESTRITO=True, que forca cada string a caber no
    tamanho exato da original.
"""

INICIO, FIM = 0xE7AD1C, 0xE7BB62
SEP = b'\xff\xff'
SPACER = 0x00FD
NEWLINE = 0x11FF
ESTRITO = False        # True = cada string presa ao tamanho exato da original


class BlocoSistema:
    def __init__(self, mf, mtab):
        self.mf = mf
        self.enc_map = dict(mtab.enc_map)
        self.enc_map['·'] = SPACER
        self.enc_map['\n'] = NEWLINE
        self.cd = mtab.tm.char_dict
        self.segmentos = self._ler()

    def _ler(self):
        # o separador tem que ser lido ALINHADO em 2 bytes: dois chars vizinhos
        # podem formar 00 FF | FF 00, que um find() cru veria como separador.
        segs, ini = [], INICIO
        p = INICIO
        while p < FIM:
            if self.mf[p:p + 2] == SEP:
                segs.append((ini, p))
                ini = p + 2
            p += 2
        segs.append((ini, FIM))
        return segs

    def texto(self, i):
        a, b = self.segmentos[i]
        o = ''
        for r in range(a, b - 1, 2):
            c = (self.mf[r] << 8) | self.mf[r + 1]
            o += '·' if c == SPACER else self.cd.get(c, f'<{c:04X}>')
        return o

    def encode(self, s):
        out = bytearray()
        for c in s:
            code = self.enc_map.get(c)
            if code is None:
                raise ValueError(f'caractere fora da fonte: {c!r} em {s!r}')
            out += code.to_bytes(2, 'big')
        return bytes(out)

    def aplicar(self, trad, verbose=True):
        """trad = {indice_do_segmento: texto}.

        Estrategia de MENOR DANO: cada string traduzida e preenchida com espaco
        ate o tamanho EXATO da original, entao todo segmento seguinte continua no
        offset original. Se uma string nao couber (o unico caso e 'No' -> 'Não'),
        o char extra e descontado da PROXIMA string que tenha espaco sobrando —
        assim o desalinhamento morre no segmento seguinte em vez de arrastar o
        bloco inteiro. Nada cresce: o tamanho total e sempre preservado.
        """
        corpos, delta, remendos = [], 0, []
        for i, (a, b) in enumerate(self.segmentos):
            orig_chars = (b - a) // 2
            if i not in trad:
                corpos.append(bytes(self.mf[a:b]))
                continue
            txt = trad[i]
            if len(txt) < orig_chars:
                sobra = orig_chars - len(txt)
                # primeiro paga a divida acumulada, o resto vira espaco
                corta = min(delta, sobra)
                delta -= corta
                txt = txt + ' ' * (sobra - corta)
                if corta:
                    remendos.append(f'seg {i}: {corta} char(s) de folga usados '
                                    f'pra reequilibrar')
            elif len(txt) > orig_chars:
                if ESTRITO:
                    raise RuntimeError(f'ESTRITO: seg {i} tem {len(txt)} chars, '
                                       f'original {orig_chars}')
                delta += len(txt) - orig_chars
                remendos.append(f'seg {i}: +{len(txt)-orig_chars} char(s) '
                                f'({trad[i]!r}) — desalinha ate o proximo reequilibrio')
            corpos.append(self.encode(txt))

        if delta:
            raise RuntimeError(f'sobraram {delta} chars sem compensacao — '
                               f'encurte alguma string depois do estouro')
        alvo = FIM - INICIO
        blob = SEP.join(corpos)
        if len(blob) != alvo:
            raise RuntimeError(f'bloco de sistema com {len(blob)} bytes, '
                               f'esperado {alvo}')
        self.mf[INICIO:FIM] = blob
        if verbose:
            for r in remendos:
                print(f'   [sistema] {r}')
            iguais = sum(1 for i, (a, b) in enumerate(self.segmentos)
                         if len(corpos[i]) == b - a)
            print(f'   [sistema] {len(trad)} strings | {iguais}/{len(corpos)} '
                  f'segmentos no tamanho original | bloco {alvo} bytes preservado')

    def verificar_identidade(self):
        """Remontar sem traducao tem que dar byte-identico."""
        corpos = [bytes(self.mf[a:b]) for a, b in self.segmentos]
        return SEP.join(corpos) == bytes(self.mf[INICIO:FIM])
