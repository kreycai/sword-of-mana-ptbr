export const meta = {
  name: 'qa-fidelidade-som',
  description: 'Revisa a fidelidade da traducao (EN x PT atual) e reescreve fiel, cabendo na caixa',
  phases: [{ title: 'QA', detail: 'um agente Sonnet por lote, compara EN x PT e corrige' }],
}

let a = args
if (typeof a === 'string') { try { a = JSON.parse(a) } catch (e) { a = a.split(',').map(s => s.trim()) } }
const lotes = Array.isArray(a) ? a : (a && Array.isArray(a.lotes) ? a.lotes : [])
const MODEL = (a && a.model) ? a.model : 'sonnet'
log(`QA fidelidade: ${lotes.length} lotes, modelo=${MODEL}`)
if (!lotes.length) { log('nada a revisar'); return [] }

const BASE = '/home/guire/projetos/ps2_video_test/traducao'
const STATUS = {
  type: 'object', additionalProperties: false,
  required: ['lote', 'gravado', 'n_revisadas', 'notas'],
  properties: {
    lote: { type: 'string' }, gravado: { type: 'boolean' },
    n_revisadas: { type: 'integer' }, notas: { type: 'string' },
  },
}

function prompt(l) {
  return `Voce e revisor de traducao EN->PT-BR de Sword of Mana (GBA). Sua missao: deixar a traducao FIEL ao ingles original, corrigindo onde a 1a passada (automatica) encurtou demais, mudou o sentido ou errou — mantendo tudo cabendo na caixa de dialogo.

LEIA OS TRES:
- ${BASE}/parts_src/${l}.json      -> ORIGINAL em ingles: lista de {"id","texto"}
- ${BASE}/parts_out/${l}.json      -> traducao ATUAL pt-BR: {"<id>":"<texto>"}
- ${BASE}/glossario.md             -> nomes/rotulos fixos

PARA CADA FALA, compare a traducao atual com o ingles:
- Se mudou o sentido, OMITIU/encurtou conteudo do original, tem erro/typo, ou ficou estranha -> REESCREVA fiel ao ingles, em pt-BR natural e fluido.
- Se ja esta boa e fiel -> mantenha como esta.

CASO ESPECIAL: as vezes o "original" (parts_src) NAO esta em ingles — vem um RASCUNHO antigo em portugues malformado (typos, espacos quebrados, glifo japones solto, ate palavrao). Nesses casos NAO precisa de ingles: apenas deixe o PORTUGUES LIMPO — corrija typos e acentos, arrume a gramatica, REMOVA palavroes/glifos soltos, mantendo o sentido do rascunho — e encaixe na caixa.

REGRAS INEGOCIAVEIS:
- Preserve EXATAMENTE os codigos {A} {HERO} {HEROINE} {CHOICE} {END_CHOICES} {RED} {END_COLOR} (mesma quantidade que o ingles original tem).
- CABER NA CAIXA: siga a estrutura do INGLES original — mesmo numero de {A} (paginas), e quebre com \\n de forma que cada linha visivel tenha ~<=28 caracteres e cada pagina nao tenha MAIS linhas que a original. Se a traducao fiel nao couber, encurte SO o necessario (fidelidade primeiro, condensar por ultimo).
- ACENTOS: use acentuacao correta do portugues (á à â ã é ê í ó ô õ ú ç e maiusculas À Á Â Ã É Ê Í Ó Ô Õ Ú Ç). A fonte agora suporta acentos. (Evite ü -> use u; evite aspa reta.)
- Rotulos de personagem (o "Nome:" antes da fala) e nomes proprios: siga o glossario a risca.
- NAO invente conteudo que nao esta no ingles. NAO mude ids.

GRAVE ${BASE}/parts_qa/${l}.json como {"<id>":"<texto>"} com TODAS as falas do lote (as revisadas com texto novo + as mantidas iguais). Nao perca nenhum id.

Retorne o status (lote, gravado, n_revisadas = quantas voce mudou, notas com exemplos do que corrigiu). Seu texto final NAO e pra humano.`
}

phase('QA')
const res = await parallel(lotes.map(l => () =>
  agent(prompt(l), { label: `qa:${l}`, phase: 'QA', model: MODEL, schema: STATUS })
))
const ok = res.filter(Boolean)
log(`QA: ${ok.filter(r => r.gravado).length}/${lotes.length} lotes gravados, ${ok.reduce((s, r) => s + (r.n_revisadas || 0), 0)} falas revisadas`)
return res
