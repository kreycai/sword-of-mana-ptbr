export const meta = {
  name: 'encaixar-caixas-som',
  description: 'Reescreve falas que transbordam a caixa pra caberem no esqueleto do original',
  phases: [{ title: 'Encaixar', detail: 'um agente Sonnet por lote, so as falas marcadas' }],
}

let a = args
if (typeof a === 'string') { try { a = JSON.parse(a) } catch (e) { a = a.split(',').map(s => s.trim()) } }
const lotes = Array.isArray(a) ? a : (a && Array.isArray(a.lotes) ? a.lotes : [])
const MODEL = (a && a.model) ? a.model : 'sonnet'
log(`encaixe: ${lotes.length} lotes, modelo=${MODEL}`)
if (!lotes.length) { log('nada a encaixar'); return [] }

const BASE = '/home/guire/projetos/ps2_video_test/traducao'
const STATUS = {
  type: 'object', additionalProperties: false,
  required: ['lote', 'gravado', 'n_corrigidas', 'notas'],
  properties: {
    lote: { type: 'string' }, gravado: { type: 'boolean' },
    n_corrigidas: { type: 'integer' }, notas: { type: 'string' },
  },
}

function prompt(l) {
  return `Voce ajusta a QUEBRA DE LINHA de falas ja traduzidas de Sword of Mana (pt-BR) pra elas caberem na caixa de dialogo, SEM estragar a traducao.

ARQUIVOS (leia os tres):
- ${BASE}/parts_src/${l}.json        -> original em ingles: lista de {"id","texto"}
- ${BASE}/parts_out/${l}.json        -> traducao atual pt-BR: {"<id>":"<texto>"}  (JA EXISTE, voce vai reescrever)
- ${BASE}/parts_fix/${l}.json        -> falas que transbordam: {"<id>": {"n_paginas","max_linha","linhas_por_pagina"}}

TAREFA: para CADA id listado em parts_fix/${l}.json, pegue a traducao atual daquela fala e reescreva pra caber no esqueleto do ORIGINAL:
- MESMO numero de {A} que o original (n_paginas-1 marcadores {A}). Cada trecho entre {A} e uma "pagina".
- Em cada pagina, no MAXIMO o numero de linhas que "linhas_por_pagina" indica pra aquela pagina (pode ter menos, NUNCA mais).
- Cada linha visivel com NO MAXIMO "max_linha" caracteres.
- Se a traducao em pt-BR nao couber nesse espaco, ENCURTE o texto (seja mais conciso, corte palavras redundantes, use sinonimos curtos) ate caber. Preferir encurtar a estourar a caixa.
- Preserve os codigos {A} {HERO} {HEROINE} {CHOICE} {END_CHOICES} {RED} {END_COLOR} (mesma quantidade do original) e o sentido da fala. {HERO}/{HEROINE} ocupam ~5 caracteres visiveis, conte isso.
- NAO use aspas retas ("), travessao (—), nem caracteres estranhos: a fonte so tem ' ' , . ! ? : ; ( ) aspas curvas “ ” ’ e reticencias …  Acentos podem (sao removidos depois).

DEPOIS: grave ${BASE}/parts_out/${l}.json de volta como {"<id>":"<texto>"} com TODAS as falas do lote — as que voce corrigiu com o texto novo e as demais EXATAMENTE como estavam. Nao perca nenhum id.

Retorne o status (lote, gravado, n_corrigidas = quantas voce reescreveu, notas). Texto final NAO e pra humano.`
}

phase('Encaixar')
const res = await parallel(lotes.map(l => () =>
  agent(prompt(l), { label: `encaixa:${l}`, phase: 'Encaixar', model: MODEL, schema: STATUS })
))
const ok = res.filter(Boolean)
log(`encaixe: ${ok.filter(r => r.gravado).length}/${lotes.length} lotes regravados, ${ok.reduce((s, r) => s + (r.n_corrigidas || 0), 0)} falas corrigidas`)
return res
