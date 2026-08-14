export const meta = {
  name: 'traduzir-onda-som',
  description: 'Traduz uma onda de lotes do Sword of Mana pra pt-BR (um agente por lote)',
  phases: [{ title: 'Traduzir', detail: 'um agente Sonnet por lote, grava parts_out/lote_XXX.json' }],
}

// args = ["lote_000",...]  ou  {lotes:[...], model:"haiku"}
let a = args
if (typeof a === 'string') { try { a = JSON.parse(a) } catch (e) { a = a.split(',').map(s => s.trim()) } }
let lotes = Array.isArray(a) ? a : (a && Array.isArray(a.lotes) ? a.lotes : [])
const MODEL = (a && a.model) ? a.model : 'haiku'
log(`onda: ${lotes.length} lotes, modelo=${MODEL}`)
if (!lotes.length) { log('Onda vazia — nada a traduzir.'); return [] }

const BASE = '/home/guire/projetos/ps2_video_test/traducao'

const STATUS = {
  type: 'object',
  additionalProperties: false,
  required: ['lote', 'gravado', 'n_falas', 'notas'],
  properties: {
    lote: { type: 'string' },
    gravado: { type: 'boolean', description: 'true se escreveu o arquivo de saida' },
    n_falas: { type: 'integer' },
    notas: { type: 'string', description: 'avisos, termos duvidosos, ou vazio' },
  },
}

function prompt(lote) {
  return `Voce e tradutor de videogame EN->PT-BR trabalhando no romhack de Sword of Mana (GBA).

TAREFA: traduzir o lote de dialogo em ${BASE}/parts_src/${lote}.json para portugues do Brasil e gravar o resultado.

PASSOS:
1. Leia ${BASE}/glossario.md (termos fixos, nomes proprios, rotulos de personagem) — SIGA a risca.
2. Leia ${BASE}/parts_src/${lote}.json — e uma lista de objetos {"id": N, "texto": "..."}.
3. Traduza cada "texto". Depois grave ${BASE}/parts_out/${lote}.json como um objeto JSON {"<id>": "<traducao>", ...} (chaves = id como string, na MESMA ordem).

REGRAS INEGOCIAVEIS (o build valida isso; se quebrar, a onda falha):
- Preserve EXATAMENTE, sem traduzir nem alterar, todos os codigos entre chaves: {A} {HERO} {HEROINE} {CHOICE} {END_CHOICES} {RED} {END_COLOR}. Mesmos codigos, mesma quantidade, nas posicoes equivalentes.
- Preserve a MESMA quantidade de quebras de linha \\n de cada fala (o texto ja vem quebrado pra caber na caixa; mantenha o numero de linhas igual ao original).
- Cada linha visivel deve caber em ~26-28 caracteres. Reescreva a quebra do jeito natural em pt-BR mas SEM mudar o total de \\n.
- O rotulo de personagem no comeco (ex: "Topple Grandfather:\\n") vira o rotulo do glossario (ex: "Vovô de Topple:\\n"). Nomes proprios de pessoas/lugares NAO mudam.
- Acentos SAO permitidos (o build remove depois) — escreva portugues correto com acento.
- Tom natural de RPG, fiel ao sentido. Nada de inventar conteudo.
- Nao mexa nos ids.

Depois de gravar, retorne o status (lote, gravado, n_falas, notas). Em "notas" liste termos que voce ficou em duvida ou deixou em ingles; senao string vazia. Seu texto final NAO e pra humano — e so o status estruturado.`
}

phase('Traduzir')
const res = await parallel(lotes.map(l => () =>
  agent(prompt(l), { label: `traduz:${l}`, phase: 'Traduzir', model: MODEL, schema: STATUS })
))

const ok = res.filter(Boolean)
log(`Onda concluida: ${ok.filter(r => r.gravado).length}/${lotes.length} lotes gravados.`)
return res
