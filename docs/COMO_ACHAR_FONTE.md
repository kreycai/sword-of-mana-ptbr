# Como localizar a fonte (tiles) de um jogo GBA na ROM — via dump de VRAM

Técnica geral e reutilizável pra qualquer ROM de GBA (ou similar) onde a fonte
NÃO está comprimida. Foi assim que achamos a fonte do Sword of Mana depois de
muita tentativa cega falhar.

## A ideia central
Buscar a fonte "às cegas" na ROM (renderizar regiões e olhar) é ruim: a ROM tem
dezenas de folhas de tiles com textinho embutido (ícones, HP/MP, logos) que
parecem fonte. **Melhor: capturar os bytes reais dos glifos da VRAM enquanto o
texto está na tela, e procurar esses bytes EXATOS na ROM.** Se a fonte é
descomprimida, os tiles vão pra VRAM iguais aos da ROM → match byte-a-byte crava
o offset, sem achismo de formato.

## Passo a passo
1. **No mGBA**, chegue numa tela com o texto/fonte de interesse na tela.
2. **Tools → Visualizar memória** (Memory viewer) → botão **"Salvar Alcance"**.
   - Endereço inicial: `0x6000000` (VRAM do GBA). Contagem: `0x18000` (96 KB).
   - Salva como `vram.bin`.
3. **Procurar os tiles na ROM** (script Python, sem libs externas):
   - Trata a VRAM como tiles 4bpp de 8×8 = **32 bytes/tile** (2 px/byte, nibble
     baixo = pixel esquerdo). Se a fonte for 2bpp, tile = 16 bytes; 1bpp = 8 bytes.
   - Pega os tiles "glifo-like" (preenchimento moderado, ≥2 valores distintos).
   - Pra cada um, `rom.find(tile)` — acha ocorrências EXATAS.
   - **Filtra os DISTINTIVOS** (aparecem só 1–6× na ROM); tiles genéricos
     aparecem milhares de vezes e são lixo.
   - **Agrupa por região**: onde muitos glifos DISTINTOS caem juntos = tabela.
   - Confirma vendo o **delta entre offsets**: `32` = tabela de tiles 8×8 4bpp
     em sequência (64 se glifos forem 8×16).
4. **Renderizar** o offset achado pra confirmar (cuidado com a FASE: se os
   matches caem em `...10`, os tiles estão alinhados a 0x10, não a 0).
5. Glifos altos (8×16) = 2 tiles empilhados; renderize combinando o par.

Scripts usados ficaram no scratchpad da sessão (pngtool.py = ler/escrever PNG em
zlib puro, já que não há PIL/imagemagick no WSL; + os de busca/render).

## O que descobrimos no Sword of Mana (USA/AUS, região 'E')
- **Fonte é 4bpp, DESCOMPRIMIDA.** (Confirmado: no CrystalTile2, modo
  "4 color... GBA 4bpp", os glifos aparecem crus.)
- **Charmap** (mapa código→caractere da tela de digitar nome) em `0xE7BB62`,
  len `0xD6`. Só tem `À` (0x5F) entre acentos + as MARCAS de acento soltas.
- **Códigos das letras** (sequenciais): dígitos `0-9`=0x1D–0x26, `A-Z`=0x27–0x40,
  `a-z`=0x41–0x5A, `À`=0x5F. Slots livres 0x5B–0x5E e 0x60+ (candidatos a
  acentos pré-compostos EU não-mapeados).
- **Blocos de fonte achados por dump de VRAM (match exato):**
  - `~0xD87410`: fonte de status/batalha (MP, "Miss!", "Lv up!", dígitos) 8×8.
  - `~0xD88010`: fonte de NÚMEROS grandes (dano) 8×16.
  - Outras regiões candidatas do mesmo banco: 0xDAB000, 0xD87000, 0xDAE000,
    0xDB4000 — **a fonte de DIÁLOGO (minúsculas + À) deve estar numa delas**
    (a investigar).
- Fonte de menu/uppercase que o usuário achou visualmente: `~0x370600`.

## Próximos passos (acentos)
1. Achar a fonte de DIÁLOGO exata (a que tem minúsculas) entre as regiões acima.
2. Amarrar índice código→glifo (base + code*tamanho) usando um glifo conhecido.
3. Renderizar slots 0x5B–0x5E / 0x60+ → ver quais acentos já existem.
4. Existentes → só mapear no encoder (char_dict / montar_rom.py).
   Faltantes → gerar o glifo por script (compor letra + marca) e escrever os
   bytes na ROM; ligar `ACENTOS_NA_FONTE=True`.
