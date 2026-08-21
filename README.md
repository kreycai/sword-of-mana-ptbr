# Sword of Mana (GBA) — Tradução PT-BR

Tradução para português do Brasil de **Sword of Mana** (Square Enix / Brownie Brown,
Game Boy Advance).

**Diálogo e menus traduzidos.** 4.335 falas, 1.748 strings de menu e as 81 mensagens de
sistema. A história inteira, os nomes e descrições de item, arma, armadura, magia,
classe, monstro e lugar, e a interface de salvar, forjar e criar personagem.

---

## Baixar

**[>> Baixar o patch na página de Releases <<](../../releases/latest)**

São dois patches. O `completa` é o recomendado; o `so-dialogo` existe para quem prefere a
interface em inglês, e é idêntico ao lançamento de agosto de 2026.

| patch | resultado | CRC32 |
|---|---|---|
| `SwordOfMana-ptBR-completa.bps` | diálogo + menus + sistema | `E2C5B55F` |
| `SwordOfMana-ptBR-so-dialogo.bps` | menus em inglês | `14EC7BB2` |

**O patch não contém o jogo** — só a diferença entre a ROM original e a traduzida. Você
precisa ter a sua própria cópia.

| | |
|---|---|
| Aplicar em | **Sword of Mana (USA, Australia)** — dump No-Intro |
| Tamanho | 16.777.216 bytes |
| CRC32 | `7F1EAC75` |
| SHA-1 | `a7ff0b4482c7c3b19467af37c3e277321cd9f1cd` |

### Não tem certeza se a sua ROM é a certa?

```
python3 tools/verificar_rom.py "Sword of Mana (USA, Australia).gba"
```

Ele diz se é a certa e, se não for, **qual você tem** — o erro mais comum é ter a versão
europeia (`AVSP`) ou a japonesa (`AVSJ`), que têm nome parecido e não servem. O flips só diz
que o checksum não bate, sem explicar o motivo.

Passo a passo em **[COMO_APLICAR.txt](COMO_APLICAR.txt)**.

Resumo: baixe o [Floating IPS](https://www.romhacking.net/utilities/1040/), clique em
*Apply Patch*, escolha o `.bps` e depois a sua ROM.

### Atenção: a ROM resultante tem 32 MB

O dobro da original. **A ROM foi expandida de propósito** — texto em português ocupa mais
espaço que em inglês, e sem expandir não caberia.

Funciona em **mGBA**, **VBA-M** e no **Everdrive GBA**. Emuladores e flashcarts muito
antigos podem implicar com ROM expandida.

---

## Estado da tradução

| frente | strings | traduzido | % |
|---|---|---|---|
| **Diálogo** | 4.372 | 4.335 | **99,15%** |
| **Menus, itens, equipamentos** | 1.840 | 1.748 | **95,0%** |
| **Mensagens de sistema** | 81 | 81 | **100%** |

As 37 entradas de diálogo restantes são todas `{BLANK}` ou vazias — foram conferidas uma a
uma. Não existe uma única linha de diálogo real sem tradução.

As 92 strings de menu em inglês são **nome próprio por decisão**: monstros cunhados
(Rabite, Molebear, Poto, Chobin Hood, Kaiser Mimic), personagens, os oito espíritos
(Wisp, Shade, Luna, Salamander, Undine, Dryad, Jinn, Gnome) e o Dark Lord — mais `OK`,
`HP` e `MP`, iguais em português.

O contador de 2.909 que aparecia aqui antes contava a master table inteira, incluindo
placeholders em japonês que a build americana nunca mostra. O número honesto de strings
que o jogador vê é 1.840.

---

## Como foi feito

O jogo guarda texto em **2 bytes por caractere**, big-endian, com códigos de controle no
meio, e tabelas de ponteiros que precisam ser reescritas quando o tamanho do texto muda.
O texto está em **três lugares diferentes**, com estruturas diferentes:

| onde | o que tem | como é indexado |
|---|---|---|
| tabela de história (ponteiro em `0x3EB0`) | as 4.372 falas | offsets u16 com *wrap* a cada `0x10000` |
| *master table* (ponteiro em `0x65D8`) | 57 sub-tabelas: item, arma, armadura, magia, classe, monstro, lugar | offsets u32 para as sub-tabelas, u16 dentro de cada uma |
| bloco solto em `0xE7AD1C` | 81 mensagens de sistema | segmentos separados por `0xFFFF` |

O terceiro bloco não estava documentado em lugar nenhum e não é alcançável pelos outros
dois — foi encontrado procurando os bytes codificados de `Confirm` na ROM.

### Três problemas que definiram a solução

**A master table não pode ser realocada.** Com o diálogo, a saída foi mover a tabela para
o fim da ROM expandida e reapontar. Com os menus isso quebra: uma varredura achou **66
ponteiros de código apontando direto para dentro do array de offsets**. A solução foi
manter o cabeçalho e o array no lugar original e mover só as sub-tabelas traduzidas —
quem não é traduzido não muda um byte.

**A fonte é de largura fixa, 6 pixels por caractere.** Isso foi medido, não presumido:
os glifos da fonte foram casados contra um dump de VRAM do jogo rodando, e só o passo de
6px reproduziu palavras legíveis. A consequência prática é que **contar caractere é medir
largura** — não adianta trocar `W` por `i`. O orçamento de cada tabela passou a ser o
comprimento da maior string original dela, que é uma largura que o jogo comprovadamente
acomoda, e nenhuma tradução passou disso.

**O bloco de sistema não tem folga.** Ele termina exatamente onde começa o charmap do
teclado de nomes, e o mecanismo de índice não foi localizado. A escrita é in-place com
preenchimento até o tamanho exato de cada string original, então 123 dos 125 segmentos
continuam no offset original.

### As ferramentas

Tudo em Python, em [`tools/`](tools/):

| ferramenta | o que faz |
|---|---|
| `exportar_dialogo.py` | extrai o script e a tabela de ponteiros |
| `relsearch.py` | busca relativa, para achar a tabela de caracteres |
| `acentos.py` | insere os glifos acentuados na fonte |
| `rewrap_mecanico.py` | reflui o texto respeitando a largura da caixa de diálogo |
| `merge_parts.py`, `reimport.py` | junta os lotes e reinsere |
| **`menus.py`** | lê e remonta a master table dos menus |
| **`sistema.py`** | lê e remonta o bloco de mensagens de sistema |
| **`dump_menu.py`, `merge_menus.py`** | inspeciona uma sub-tabela e funde lotes traduzidos |
| **`validar_menus.py`** | audita largura e codificabilidade antes de montar |
| `validar_parts_out.py`, `diff_traducao.py` | QA do diálogo |
| `montar_rom.py` | expande a ROM e remonta os três blocos num passe |
| `bps.py` | gera e aplica o patch BPS |
| **`patch_nointro.py`** | gera o patch mirando o dump No-Intro |
| `verificar_rom.py` | diz qual ROM a pessoa tem |

Cada montador roda uma **verificação de identidade** antes de escrever: remonta a
estrutura sem tradução nenhuma e exige que saia byte a byte igual à original. Se não sair,
aborta sem salvar. É o que garante que o formato foi entendido, e não adivinhado.

Como a fonte foi localizada está em [`docs/COMO_ACHAR_FONTE.md`](docs/COMO_ACHAR_FONTE.md).
O [`docs/glossario.md`](docs/glossario.md) tem as decisões de tradução, inclusive por que
`Armor` virou *Couraça* e `Temper` virou *Apurar* em vez de abreviação.

---

## O que falta

- **A introdução em texto-imagem.** O `"In the beginning, the world was void."` é gráfico
  pré-renderizado numa fonte itálica decorativa, não é fonte de texto. Traduzir significa
  redesenhar imagem na ROM — fase separada.
- **Testar do início ao fim.** O texto foi revisado e validado por ferramenta, mas o jogo
  não foi zerado nesta versão.

Contribuições e reportes são bem-vindos. Erro de tradução ou texto cortado: abra uma issue
com **print** e onde aconteceu. Sugestão de nome para item é onde ajuda de fora rende mais.

## Apoiar

A tradução é gratuita e continua sendo. Se ela te serviu e você quiser contribuir com algo,
aceito Pix:

```
031ce91d-e33b-48b6-84c5-1930edd381c5
```

Sem obrigação nenhuma. Sugerir nome pra item ou reportar texto cortado ajuda tanto quanto.

## Licença e escopo

As **ferramentas** em `tools/` são livres — use como quiser.

A **tradução** é trabalho derivado do jogo original, feita sem fins lucrativos e distribuída
como patch justamente para não distribuir o jogo. Não vendo, não peça ROM, e não use isso
comercialmente.

Sword of Mana é propriedade da Square Enix.
