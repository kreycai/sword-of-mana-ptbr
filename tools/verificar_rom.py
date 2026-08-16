#!/usr/bin/env python3
"""Diz se a sua ROM e a certa pra aplicar o patch -- e, se nao for, qual voce tem.

O flips so avisa que o checksum nao bate. Isso vira "nao funciona" sem ninguem
descobrir o motivo, que quase sempre e ter a versao europeia ou um dump trimado.

uso:
  python3 verificar_rom.py "Sword of Mana (USA, Australia).gba"
"""
import hashlib
import sys
import zlib

ESPERADO = {
    'tamanho': 16_777_216,
    'crc32': 0x7F1EAC75,
    'sha1': 'a7ff0b4482c7c3b19467af37c3e277321cd9f1cd',
    'code': 'AVSE',
    'versao': 0,
}

# Outros dumps que a pessoa provavelmente tem em maos. O game code fica no
# offset 0xAC do cabecalho GBA e nao depende de o arquivo estar intacto, entao
# funciona pra identificar ate copia modificada.
CONHECIDOS = {
    'AVSP': 'Sword of Mana (Europe) -- o patch NAO serve. Precisa da USA/Australia.',
    'AVSJ': 'Shinyaku Seiken Densetsu (Japan) -- versao japonesa, o patch NAO serve.',
    'AVSE': 'Sword of Mana (USA, Australia) -- e esta.',
}


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)

    caminho = sys.argv[1]
    try:
        d = open(caminho, 'rb').read()
    except OSError as e:
        sys.exit(f'erro ao abrir: {e}')

    crc = zlib.crc32(d)
    sha1 = hashlib.sha1(d).hexdigest()
    code = d[0xAC:0xB0].decode('ascii', 'replace') if len(d) > 0xB0 else '????'
    versao = d[0xBC] if len(d) > 0xBC else -1
    titulo = d[0xA0:0xAC].decode('ascii', 'replace').strip('\0') if len(d) > 0xAC else '?'

    print(f'arquivo   {caminho}')
    print(f'tamanho   {len(d):,} bytes'.replace(',', '.'))
    print(f'CRC32     {crc:08X}')
    print(f'SHA-1     {sha1}')
    print(f'titulo    {titulo}')
    print(f'game code {code}   versao {versao}')
    print()

    if crc == ESPERADO['crc32'] and len(d) == ESPERADO['tamanho']:
        print('>>> E A ROM CERTA. Pode aplicar o patch.')
        return 0

    print('>>> NAO e a ROM esperada pelo patch.')
    print()

    if code in CONHECIDOS:
        print(f'    {CONHECIDOS[code]}')
        if code == 'AVSE':
            print()
            print('    O game code confere, mas o conteudo nao. Isso quer dizer que a')
            print('    sua copia foi modificada -- ROM ja patcheada, save embutido,')
            print('    trim, ou header alterado por algum programa. Use uma copia limpa.')
    else:
        print(f'    Game code "{code}" nao reconhecido. Isso nem parece Sword of Mana.')

    print()
    print('    A ROM que o patch espera:')
    print(f"      Sword of Mana (USA, Australia)")
    print(f"      {ESPERADO['tamanho']:,} bytes".replace(',', '.'))
    print(f"      CRC32 {ESPERADO['crc32']:08X}")
    print(f"      SHA-1 {ESPERADO['sha1']}")
    print(f"      game code {ESPERADO['code']}, versao {ESPERADO['versao']}")
    print()
    print('    Nao distribuo o jogo, e nao adianta pedir. Verifique a sua copia.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
