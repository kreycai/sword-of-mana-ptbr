# Sword of Mana (GBA) — Tradução PT-BR

Tradução para português do Brasil de **Sword of Mana** (Square Enix / Brownie Brown,
Game Boy Advance).

**Todo o diálogo está traduzido** — 4.335 falas, 320.602 caracteres. A história inteira,
do começo ao fim, está em português.

> **Menus, itens e equipamentos continuam em inglês.** São 2.909 strings ainda não
> traduzidas. Você joga a história completa em português, mas vai ver `Rusty Sword` no
> inventário. Isso está sendo trabalhado.

---

## Baixar

**[>> Baixar o patch na página de Releases <<](../../releases/latest)**

**O patch não contém o jogo** — só a diferença entre a ROM original e a traduzida. Você
precisa ter a sua própria cópia.

| | |
|---|---|
| Aplicar em | **Sword of Mana (USA, Australia)** |
| Tamanho | 16.777.216 bytes |
| CRC32 | `FACBDF03` |
| SHA-1 | `veja COMO_APLICAR.txt` |

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
| **Menus, itens, equipamentos** | 2.909 | 0 | **0%** |

As 37 entradas de diálogo restantes são todas `{BLANK}` ou vazias — foram conferidas uma a
uma. Não existe uma única linha de diálogo real sem tradução.

---

## Como foi feito

O jogo guarda texto em **2 bytes por caractere**, com códigos de controle no meio, e uma
tabela de ponteiros que precisa ser reescrita quando o tamanho do texto muda.

As ferramentas estão em [`tools/`](tools/):

| ferramenta | o que faz |
|---|---|
| `exportar_dialogo.py` | extrai o script e a tabela de ponteiros |
| `relsearch.py` | busca relativa, para achar a tabela de caracteres |
| `acentos.py` | insere os glifos acentuados na fonte |
| `rewrap_mecanico.py` | reflui o texto respeitando a largura da caixa de diálogo |
| `merge_parts.py`, `reimport.py` | junta os lotes e reinsere |
| `montar_rom.py` | expande a ROM e remonta |
| `validar_parts_out.py`, `diff_traducao.py` | QA antes de montar |
| `bps.py` | gera e aplica o patch BPS |

Como a fonte foi localizada está em [`docs/COMO_ACHAR_FONTE.md`](docs/COMO_ACHAR_FONTE.md).
O [`docs/glossario.md`](docs/glossario.md) tem as decisões de tradução de nomes recorrentes.

### O problema central

Português é mais longo que inglês, quase sempre. Em ROM de GBA o texto fica num espaço
fixo, então texto maior **sobrescreve o vizinho**. Duas saídas: cortar a tradução para caber,
ou reescrever os ponteiros e expandir a ROM. Aqui foi a segunda — o texto não foi mutilado.

---

## O que falta

- **Menus, itens e equipamentos** (2.909 strings). Strings curtas, mas com limite de espaço
  bem mais apertado que o diálogo — o oposto do problema anterior.
- Testar do início ao fim. O diálogo foi revisado, mas o jogo não foi zerado nessa versão.

Contribuições e reportes são bem-vindos. Erro de tradução ou texto cortado: abra uma issue
com **print** e onde aconteceu.

## Licença e escopo

As **ferramentas** em `tools/` são livres — use como quiser.

A **tradução** é trabalho derivado do jogo original, feita sem fins lucrativos e distribuída
como patch justamente para não distribuir o jogo. Não vendo, não peça ROM, e não use isso
comercialmente.

Sword of Mana é propriedade da Square Enix.
