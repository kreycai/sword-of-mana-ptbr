#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
relsearch.py - Busca Relativa (Relative Search)

Acha uma palavra numa ROM mesmo sem saber a codificacao das letras,
usando o padrao de ESPACAMENTOS entre letras consecutivas.

Se acharmos varias palavras, descobrimos o alfabeto do jogo.
Se nao acharmos NADA, o texto provavelmente esta comprimido.
"""

import sys

def diffs(palavra):
    """Espacamentos entre letras consecutivas. Ex: 'sword' -> [4,-8,3,-14]."""
    return [ord(palavra[i+1]) - ord(palavra[i]) for i in range(len(palavra) - 1)]

def diff_da_rom(rom):
    """Espacamentos entre TODOS os bytes vizinhos da ROM, calculado uma vez.
    (& 0xFF trata o 'vai-um' de 8 bits, tipo -14 virar 242.)"""
    return bytes((b - a) & 0xFF for a, b in zip(rom, rom[1:]))

def busca_relativa(rom, diff, palavra):
    """Acha a 'palavra' procurando seu padrao de espacamentos dentro do
    diff da ROM. Usa bytes.find() -> velocidade de C."""
    padrao = bytes(d & 0xFF for d in diffs(palavra))
    achados = []
    pos = diff.find(padrao)
    while pos != -1:
        achados.append((pos, rom[pos]))   # offset e byte da 1a letra
        pos = diff.find(padrao, pos + 1)
    return achados

def main():
    caminho = sys.argv[1]
    with open(caminho, "rb") as f:
        rom = f.read()
    print(f"ROM: {caminho}  ({len(rom)} bytes)\n")
    diff = diff_da_rom(rom)   # calcula os espacamentos da ROM inteira 1x

    # Palavras minusculas comuns num RPG de fantasia. So minusculas porque
    # maiusculas costumam ficar numa faixa separada da codificacao.
    palavras = [
        "sword", "shield", "potion", "magic", "monster", "village",
        "weapon", "armor", "healing", "warrior", "castle", "treasure",
        "please", "father", "mother", "little", "power", "welcome",
        "attack", "defense", "kingdom", "princess", "dragon", "flame",
    ]

    base_por_letra = {}  # candidatos pro valor da letra 'a'
    total = 0
    for w in palavras:
        hits = busca_relativa(rom, diff, w)
        if hits:
            total += len(hits)
            # Do byte da 1a letra, deduz quanto valeria o 'a'.
            off, b0 = hits[0]
            base_a = (b0 - (ord(w[0]) - ord('a'))) & 0xFF
            base_por_letra[w] = base_a
            print(f"  ACHOU '{w}': {len(hits)} vez(es). "
                  f"1o em 0x{off:06X}, byte={b0:#04x} -> 'a' seria {base_a:#04x}")
        else:
            print(f"  ....  '{w}': nada")

    print()
    if total == 0:
        print(">> Nenhuma palavra achada em ASCII/codificacao simples.")
        print(">> Forte indicio de que o texto esta COMPRIMIDO.")
    else:
        print(f">> {total} acerto(s)! O texto NAO esta comprimido (ou nem tudo).")
        vals = list(base_por_letra.values())
        if len(set(vals)) == 1:
            print(f">> Todas as palavras concordam: 'a' = {vals[0]:#04x}. "
                  f"TABELA CRACKEADA! :)")
        else:
            print(f">> Valores de 'a' divergentes: {set(v for v in vals)} "
                  f"(pode ter falsos positivos ou +de uma fonte).")

if __name__ == "__main__":
    main()
