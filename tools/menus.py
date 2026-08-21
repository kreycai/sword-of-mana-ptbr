#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
menus.py — leitura e REINSERCAO da "master table" (menus, itens, magias, lugares).

Formato (descoberto lendo o SeiSaboten + confirmado byte a byte):

  ponteiro em 0x65D8  ->  endereco GBA da MASTER TABLE (file 0xD434D4)

  MASTER TABLE:
    [0x00:0x08]  cabecalho ("ANG0" + 08000000)
    [0x08:0x0C]  num_sub_tabelas (u32 LE) = 57
    [0x0C:0xF0]  57 offsets u32 LE, RELATIVOS ao inicio da master table
    (depois)     as 57 sub-tabelas, contiguas

  SUB-TABELA:
    [0x00:0x04]  num_entradas (u32 LE)
    [0x04:...]   (num_entradas+1) offsets u16 LE, RELATIVOS ao inicio da SUB-tabela
    (depois)     os textos, 2 bytes big-endian por caractere, SEM terminador

!! POR QUE NAO RELOCAMOS A MASTER TABLE INTEIRA (como fizemos com o dialogo) !!
Uma varredura da ROM achou 66 ponteiros de codigo apontando DIRETO pra dentro do
array de offsets (0xD434E0 = slot 0, 0xD43570 = slot 36, ...). Mover a tabela
deixaria esses caminhos lendo o ingles velho. Entao:

  * o cabecalho e o array de 57 offsets FICAM no lugar original;
  * so a sub-tabela que a gente traduz e reconstruida, na area expandida da ROM;
  * o slot u32 dela e reapontado (offset relativo a master, que nao se moveu);
  * sub-tabela nao traduzida = slot intocado, dado original intocado.

Blast radius minimo: quem nao e traduzido nao muda nem um byte.
"""

import os, sys

AQUI  = os.path.dirname(os.path.abspath(__file__))
TRAD  = os.path.dirname(AQUI)
SEISA = os.path.join(TRAD, 'SeiSaboten')

MASTER_PTR = 0x65D8          # ponteiro-mestre dos menus (regiao 'E')
U16_MAX    = 0xFFFF          # limite dos offsets internos de cada sub-tabela

# Sub-tabelas que NAO devem ser tocadas de jeito nenhum:
#   43 e 47 — o proprio SeiSaboten marca "Unavailable for editing"; a 47 tem
#   tamanho impar (0x45) e estoura o leitor, a 43 tem chars fora do charmap.
INTOCAVEIS = {43, 47}


class MasterTable:
    def __init__(self, mf, tm):
        self.mf = mf
        self.tm = tm
        self.start = int.from_bytes(mf[MASTER_PTR:MASTER_PTR + 4], 'little') - 0x08000000
        self.n = int.from_bytes(mf[self.start + 8:self.start + 12], 'little')
        self.enc_map = self._montar_codificador()

    # ---------- navegacao ----------
    def slot_addr(self, i):
        return self.start + 12 + i * 4

    def sub_addr(self, i):
        return self.start + int.from_bytes(self.mf[self.slot_addr(i):self.slot_addr(i) + 4], 'little')

    def sub_raw(self, i):
        """(num_entradas, offsets, [bytes de cada string])"""
        a = self.sub_addr(i)
        ne = int.from_bytes(self.mf[a:a + 4], 'little')
        offs = [int.from_bytes(self.mf[a + 4 + k * 2:a + 4 + k * 2 + 2], 'little')
                for k in range(ne + 1)]
        return ne, offs, [bytes(self.mf[a + offs[k]:a + offs[k + 1]]) for k in range(ne)]

    def sub_textos(self, i):
        if i in INTOCAVEIS:
            return None
        return self.tm.all_entries_text_table(self.sub_addr(i))

    # ---------- codificador ----------
    def _montar_codificador(self):
        """char -> codigo de 2 bytes.

        O charmap do jogo tem CODIGOS DUPLICADOS pro mesmo caractere (ex: '.' e
        0x04A1 no dialogo mas 0x0056 nos menus; '?' e 0x0119 e 0x0005). Em vez de
        adivinhar, a gente DEDUZ do proprio ingles dos menus: pra cada caractere,
        usa o codigo que o jogo mais usa NOS MENUS. O que nao aparece nos menus
        cai no inverso do charmap; acentos vem do acentos.py.
        """
        freq = {}
        for i in range(self.n):
            if i in INTOCAVEIS:
                continue
            a = self.sub_addr(i)
            _, _, raws = self.sub_raw(i)
            for raw in raws:
                for p in range(0, len(raw) - 1, 2):
                    code = (raw[p] << 8) | raw[p + 1]
                    ch = self.tm.char_dict.get(code)
                    if ch is not None:
                        freq.setdefault(ch, {})
                        freq[ch][code] = freq[ch].get(code, 0) + 1

        m = {ch: max(cs.items(), key=lambda kv: kv[1])[0] for ch, cs in freq.items()}

        # fallback: qualquer char do charmap que nao apareceu nos menus
        for code, ch in self.tm.char_dict.items():
            m.setdefault(ch, code)
        m[' '] = 0x0000
        m['\n'] = 0x11FF          # nos menus a quebra de linha e 2 bytes, nao 0x80

        sys.path.insert(0, AQUI)
        import acentos
        for ch, code in acentos.ACENTO_CODE.items():
            m[ch] = code
        return m

    def encode(self, s):
        out = bytearray()
        for c in s:
            code = self.enc_map.get(c)
            if code is None:
                raise ValueError(f'caractere fora da fonte do jogo: {c!r} (em {s!r})')
            out += code.to_bytes(2, 'big')
        return bytes(out)

    # ---------- montagem ----------
    def montar_sub(self, i, traducoes=None):
        """Bytes de uma sub-tabela inteira. traducoes = {indice: texto}.

        Entrada nao traduzida = bytes ORIGINAIS copiados crus. Isso mata de vez o
        risco de codigo duplicado/char exotico em texto que a gente nem mexeu.
        """
        traducoes = traducoes or {}
        a = self.sub_addr(i)
        ne, offs, raws = self.sub_raw(i)
        head4 = bytes(self.mf[a:a + 4])

        corpos = [self.encode(traducoes[k]) if k in traducoes else raws[k]
                  for k in range(ne)]

        data_start = 4 + 2 * (ne + 1)
        if offs[0] != data_start:
            raise RuntimeError(f'sub-tabela {i}: data_start inesperado '
                               f'{offs[0]:#x} != {data_start:#x}')
        novos, pos = [], data_start
        for b in corpos:
            novos.append(pos)
            pos += len(b)
        novos.append(pos)
        if pos > U16_MAX:
            raise RuntimeError(f'sub-tabela {i} passou de 64KB ({pos:#x}) — '
                               f'os offsets internos sao u16')

        blob = bytearray(head4)
        blob += b''.join(o.to_bytes(2, 'little') for o in novos)
        blob += b''.join(corpos)
        return bytes(blob)

    def verificar_identidade(self):
        """Remonta TODAS as sub-tabelas sem traducao e exige byte-identidade.
        E a prova de que o montador entendeu o formato. Devolve lista de erros."""
        erros = []
        for i in range(self.n):
            if i in INTOCAVEIS:
                continue
            a = self.sub_addr(i)
            ne, offs, _ = self.sub_raw(i)
            original = bytes(self.mf[a:a + offs[-1]])
            try:
                remontado = self.montar_sub(i)
            except Exception as e:
                erros.append((i, f'excecao: {e}')); continue
            if remontado != original:
                j = next((x for x in range(min(len(original), len(remontado)))
                          if original[x] != remontado[x]), -1)
                erros.append((i, f'difere no byte {j} '
                                 f'(len {len(original)}/{len(remontado)})'))
        return erros

    def aplicar(self, traducoes, base_off, verbose=True):
        """traducoes = {indice_da_sub_tabela: {indice_da_entrada: texto}}.

        Escreve as sub-tabelas reconstruidas a partir de base_off (que precisa
        estar na area expandida da ROM) e reaponta os slots. Devolve o proximo
        offset livre.
        """
        pos = base_off
        for i in sorted(traducoes):
            if i in INTOCAVEIS:
                raise RuntimeError(f'sub-tabela {i} esta na lista INTOCAVEIS')
            trad = {k: v for k, v in traducoes[i].items() if v is not None}
            if not trad:
                continue
            blob = self.montar_sub(i, trad)
            if pos + len(blob) > len(self.mf):
                raise RuntimeError('a area nova nao cabe na ROM')
            self.mf[pos:pos + len(blob)] = blob
            novo_off = pos - self.start
            antigo = int.from_bytes(self.mf[self.slot_addr(i):self.slot_addr(i) + 4], 'little')
            self.mf[self.slot_addr(i):self.slot_addr(i) + 4] = novo_off.to_bytes(4, 'little')
            if verbose:
                ne, offs, _ = self.sub_raw(i)
                print(f'   [{i:2d}] {len(trad):4d} strings | {offs[-1]:#7x} bytes '
                      f'| slot {antigo:#08x} -> {novo_off:#08x} @ file {pos:#09x}')
            pos = (pos + len(blob) + 3) & ~3        # alinha em 4
        return pos


def carregar(rom_path):
    """Carrega a ROM e devolve (mf, tm, MasterTable). Silencia o ruido do SeiSaboten.

    ATENCAO: o TextManager do SeiSaboten guarda master_table_table_addresses e
    master_table_list como atributos de CLASSE, entao chamar isto DUAS VEZES no
    mesmo processo acumula lixo e a segunda leitura sai errada. Pra comparar duas
    ROMs, rode um processo por ROM.
    """
    sys.path.insert(0, SEISA)
    import globals
    mf = bytearray(open(rom_path, 'rb').read())
    globals.my_file = mf
    globals.rom_region = 'E'
    import io, contextlib
    import textman
    with contextlib.redirect_stdout(io.StringIO()):
        tm = textman.TextManager()
    return mf, tm, MasterTable(mf, tm)
