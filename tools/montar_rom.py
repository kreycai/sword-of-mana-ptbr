#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
montar_rom.py - o REINSERTOR (caminho de volta: texto -> ROM).

Passos:
  1) Verificacao: reconstroi a tabela SEM traducao e confere que sai identica
     a original (prova que o montador esta correto). Aborta se falhar.
  2) Aplica as traducoes, recalcula os offsets (tabela de ponteiros), realoca
     a tabela pro fim da ROM e reaponta o ponteiro-mestre.
  3) Salva a ROM traduzida.
"""

import sys, os, json, unicodedata

AQUI  = os.path.dirname(os.path.abspath(__file__))
TRAD  = os.path.dirname(AQUI)
SEISA = os.path.join(TRAD, 'SeiSaboten')
ROM   = os.path.join(TRAD, 'Sword of Mana (USA, Australia) - Copia.gba')
SAIDA = os.path.join(TRAD, 'Sword of Mana (pt-BR).gba')
sys.path.insert(0, SEISA)

import globals, locations
with open(ROM, 'rb') as f:
    globals.my_file = bytearray(f.read())
globals.rom_region = 'E'
import textman
tm = textman.TextManager()
mf = globals.my_file
import acentos

# ---------- codificador (texto -> bytes), verificado a 100% ----------
TOKEN_TO_BYTES = {
    '{A}': b'\x82', '{CHOICE}': b'\x83', '{END_CHOICES}': b'\x84',
    '{RED}': b'\x8e', '{END_COLOR}': b'\x8d',
    '{HERO}': b'\x86\x00', '{HEROINE}': b'\x86\x01',
}
def encode_string(s):
    out = bytearray(); i = 0
    while i < len(s):
        c = s[i]
        if c == '\n':
            out += b'\x80'; i += 1
        elif c == '{':
            j = s.find('}', i); tok = s[i:j+1]
            if tok.startswith('{X:'):                      # DIAG: {X:HH} -> emite byte cru 0x00 0xHH
                out += b'\x00' + bytes([int(tok[3:-1], 16)]); i = j + 1
            elif tok not in TOKEN_TO_BYTES:
                raise ValueError(f'token nao suportado: {tok}')
            else:
                out += TOKEN_TO_BYTES[tok]; i = j + 1
        else:
            if c in acentos.ACENTO_CODE:            # acentuados (codigo achado via trace)
                out += acentos.ACENTO_CODE[c].to_bytes(2, 'big'); i += 1
            elif c in tm.inv_char_dict:
                out += tm.inv_char_dict[c].to_bytes(2, 'big'); i += 1
            else:
                raise ValueError(f'caractere fora da fonte do jogo: {c!r}')
    return bytes(out)

# ---------- montador da tabela de historia ----------
TABLE_START = tm.story_table_address
entries     = tm.story_table_list
num_entries = len(entries)
head2       = bytes(mf[TABLE_START:TABLE_START + 2])          # 2 bytes de cabecalho (preservar)
data_start_rel = entries[0]['start'] - TABLE_START            # onde os textos comecam (relativo)
orig_end    = entries[-1]['end']                             # fim da tabela original

def corpo(entry, traducao=None):
    """Bytes de uma fala: original verbatim, ou prefixo-do-ator + texto traduzido."""
    start, end = entry['start'], entry['end']
    if traducao is None:
        return bytes(mf[start:end])                          # nao mexida: copia crua
    prefixo = bytes(mf[start:start + 3]) if entry['actor'] else b''
    return prefixo + encode_string(traducao)

def montar(traducoes):
    corpos = [corpo(e, traducoes.get(e['id'])) for e in entries]
    # recalcula offsets (relativos a TABLE_START), a partir de onde os textos comecam
    offsets = []
    pos = data_start_rel
    for b in corpos:
        offsets.append(pos)
        pos += len(b)
    offsets.append(pos)                                      # offset final (num_entries+1 no total)
    offbytes = b''.join((o & 0xFFFF).to_bytes(2, 'little') for o in offsets)
    header_size = 4 + len(offbytes)
    blob = bytearray()
    blob += head2
    blob += num_entries.to_bytes(2, 'little')
    blob += offbytes
    if data_start_rel > header_size:                         # preserva um eventual "buraco"
        blob += bytes(mf[TABLE_START + header_size:TABLE_START + data_start_rel])
    elif data_start_rel < header_size:
        raise RuntimeError('cabecalho maior que o esperado')
    blob += b''.join(corpos)
    return bytes(blob)

# ---------- 1) VERIFICACAO: identidade sem traducao ----------
identidade = montar({})
original   = bytes(mf[TABLE_START:orig_end])
if identidade != original:
    print('!! FALHOU a verificacao de identidade -- NAO vou salvar nada.')
    n = min(len(identidade), len(original)); i = 0
    while i < n and identidade[i] == original[i]:
        i += 1
    print(f'   len original={len(original)} montado={len(identidade)} 1a difbyte={i}')
    sys.exit(1)
print(f'[OK] Verificacao de identidade passou ({len(original)} bytes identicos).')

# ---------- 2) traducoes (lidas do JSON) ----------
# Acentos LIGADOS: a fonte de dialogo (0xD58A64 + code*32) tem os acentuados,
# e a gente compos os que faltavam (ã õ Ã Õ) via acentos.patch_fonte. Encoder
# emite os codigos em acentos.ACENTO_CODE. So por False pra voltar a tirar acento.
ACENTOS_NA_FONTE = True

def tira_acento(s):
    # NFD separa a letra do acento; removemos so as marcas (categoria 'Mn').
    # Usamos NFD (nao NFKD) pra nao estragar o '…'.
    nfd = unicodedata.normalize('NFD', s)
    return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')

# A fonte nao tem aspa reta ("), travessao (—) nem alguns simbolos; mapeamos
# pros equivalentes que existem na fonte (aspas curvas, hifen, etc.).
FONTE_MAP = {
    '"': '”', '—': '-', '–': '-', 'º': 'o', 'ª': 'a',
    'о': 'o',   # 'o' cirilico (typo de traducao) -> 'o' latino
    '‘': '’', '\\': '',
    '“': '”',   # aspa de abertura tem codigo 0x9D (>=0x80, inalcancavel) -> usa a de fechar
    'ü': 'u',   # trema-u raro no PT; sem slot bom sobrando -> vira u
}
def normaliza_fonte(s):
    return ''.join(FONTE_MAP.get(c, c) for c in s)

with open(os.path.join(TRAD, 'traducao_ptbr.json'), encoding='utf8') as f:
    _raw = json.load(f)
TRADUCOES = {}
for k, v in _raw.items():
    v = normaliza_fonte(v)
    TRADUCOES[int(k)] = v if ACENTOS_NA_FONTE else tira_acento(v)
print(f'[i] {len(TRADUCOES)} falas no JSON de traducao (acentos={"ON" if ACENTOS_NA_FONTE else "OFF"})')

# patch da fonte: compoe ã õ Ã Õ (que nao existiam) nos slots de trema
if ACENTOS_NA_FONTE:
    acentos.patch_fonte(mf)
    print('[i] Fonte patcheada: ã õ Ã Õ compostos (til do ñ/Ñ + base a/o/A/O).')

# valida que tudo e codificavel ANTES de montar
for id_, txt in TRADUCOES.items():
    encode_string(txt)

# >>> DIAGNOSTICO TEMPORARIO (remover depois): carimbo de versao + teste de acentos
_diag = "V3 teste:\naa ii oo uu\naá ií oó uú\naã oõ ç"
# poe bloco solido nos slots 0x68 (ó) e 0x79 (ã=funciona) pra teste inequivoco
pass  # diagnostico removido
# <<< fim diagnostico

blob = montar(TRADUCOES)
print(f'[i] Tabela original: {len(original)} bytes | traduzida: {len(blob)} bytes '
      f'(+{len(blob)-len(original)})')

# ---------- 3) realocar + reapontar + salvar ----------
NEW_OFF = 0x01000000                       # inicio da area nova (a ROM tem exatamente 16MB)
mf += bytearray(0x01000000)                # estende a ROM em 16MB (fica com 32MB, max do GBA)
mf[NEW_OFF:NEW_OFF + len(blob)] = blob      # escreve a tabela nova na area livre

ptr_loc = int(locations.locations['E']['story_text_location'], 16)  # 0x3EB0
novo_ponteiro = (NEW_OFF + 0x08000000).to_bytes(4, 'little')        # enderecos do GBA = 0x08000000 + offset
antigo = bytes(mf[ptr_loc:ptr_loc + 4])
mf[ptr_loc:ptr_loc + 4] = novo_ponteiro
print(f'[i] Ponteiro-mestre em 0x{ptr_loc:X}: {antigo.hex()} -> {novo_ponteiro.hex()}')

with open(SAIDA, 'wb') as f:
    f.write(mf)
print(f'\n[OK] ROM traduzida salva:\n  {SAIDA}\n  ({len(mf):,} bytes)')
print('Traduzidas as falas de abertura (#1 a #6). Teste no mGBA!')
