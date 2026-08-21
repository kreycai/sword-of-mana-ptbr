# Glossário de tradução — Sword of Mana (pt-BR)

Termos fixos, pra tradução não desandar ao longo das 4.335 falas.
Regra geral: tom natural, frases curtas (cabem em ~26-28 caracteres por linha),
preservar códigos `{HERO}`, `{HEROINE}`, `{A}`, quebras de linha e nº de linhas.

## Nomes próprios (NÃO traduzir)
- Dark Lord  (decisão: mantido em inglês, como o usuário já vinha usando)
- Bogard, Cibba, Willy, Julius, Amanda, Watts, Marley, Devius, Isabella
- Wendel, Topple, Granz (lugares)
- Mana (sempre "Mana")

## Termos-chave (traduzir sempre igual)
| Inglês | pt-BR |
|---|---|
| Sword of Mana | Espada de Mana |
| Mana Clan | Clã Mana |
| Gemma Knight | Cavaleiro Gemma |
| Sage | Sábio |
| Realm / Kingdom | Reino |
| heretic(s) | herege(s) |
| adventurer | aventureiro |
| {HERO} | (é o herói — deixar o código) |

## Rótulos de personagem (o "nome:" antes da fala)
- Topple Grandfather → Vovô de Topple
- Military-type Man → Homem Militar
- Realm Soldier → Soldado do Reino
- Topple Gentleman → Senhor de Topple
- Topple Girl → Garota de Topple

## Acentos
As traduções ficam guardadas COM acento em `traducao_ptbr.json`.
Hoje o build tira os acentos (a fonte do jogo só tem `À`).
Quando editarmos a fonte, é só ligar `ACENTOS_NA_FONTE = True` no `montar_rom.py`.

---

## Menus e itens (master table 0x65D8) — fechado

Reinserção por `tools/menus.py` (+ `montar_rom.py`). Orçamento de largura: a fonte
é de **largura fixa, 6px/char** (medido casando glifos contra dump de VRAM), então
contar caracteres = medir largura. Limite de cada sub-tabela = comprimento da
**maior string original** dela. `tools/validar_menus.py` audita.

| Inglês | pt-BR | nota |
|---|---|---|
| Armor (categoria/peça) | **Couraça** | `Armadura` (8) não cabia nos rótulos de 7 chars |
| Sandals | **Sandália** | singular, pra caber em 17 |
| Status (tela) | Atributos | |
| Knucks | Manoplas | descrição usa "rings" → **Anéis** |
| Mace | Maça | descrição usa "orb" → **Orbe** |
| aerolite | **meteoro** | 1 char menor que "aerólito", cabia onde ele não |
| Trait Coins | Moedas | |
| Seven Wisdoms | Sete Sabedorias | |
| Lucre | **Lucre** | igual ao diálogo (63 falas) |
| Hot House | **Estufa** | igual ao diálogo |
| Temper / Forge | Apurar / Forjar | "Temperar" (8) não cabia em 6 |
| Slash / Bash / Jab | corte / impacto / perfuração | |
| Light Dark Moon Fire Water Wood Wind Earth | Luz Trevas Lua Fogo Água Mata Vento Terra | |
| siglas de elemento (Li Da Mo Fi Wa Wo Wi Ea) | Lz Tr Lu Fg Ag Ma Ve Te | mesmo estilo do original |
| PowerUp / D-Fence / SpeedUp | Força+ / Defesa+ / Rapidez+ | e `S/…` pras imunidades |

**Nomes próprios mantidos em inglês (decisão):** monstros cunhados (Rabite,
Molebear, Mushboom, Poto, Chobin Hood, Sahagin, Chocobo, Kaiser Mimic…),
personagens (Bogard, Watts, Cibba…), os 8 espíritos (Wisp, Shade, Luna,
Salamander, Undine, Dryad, Jinn, Gnome), Dark Lord, e materiais-lugar
(Lorimar, Altena, Maia, Mythril, Pedan, Ankh, Jake, Hal, Vinek, Dion).

**Sub-tabelas 43 e 47 são INTOCÁVEIS** (`menus.INTOCAVEIS`): a 47 tem tamanho
ímpar e estoura o leitor, a 43 tem chars fora do charmap. Nunca reescrever.
