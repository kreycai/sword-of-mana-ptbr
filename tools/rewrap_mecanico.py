#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-wrap mecanico: reempacota as palavras das falas que estouram por lpp,
preservando \\n inicial de pagina, linha de nome e codigos. DRY-RUN por padrao;
passe --apply pra gravar."""
import json, glob, re, os, sys, collections

APPLY = '--apply' in sys.argv
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

def vis(s):  # largura visivel: {HERO}/{HEROINE} ~5, cores 0
    s = re.sub(r'\{(HERO|HEROINE)\}', 'XXXXX', s)
    s = re.sub(r'\{(RED|END_COLOR|CHOICE|END_CHOICES)\}', '', s)
    return len(s)

def norm(t): return re.sub(r'\{(HERO|HEROINE|RED|END_COLOR)\}', 'XXXXX', t)
def pages_env(t):
    t = norm(t)
    return [re.sub(r'\{(CHOICE|END_CHOICES)\}', '', pg).split('\n') for pg in re.split(r'\{A\}', t)]
def env(t):
    pg = pages_env(t)
    return len(pg), max((len(l) for p in pg for l in p), default=0), [len(p) for p in pg]

def greedy(words, maxw):
    lines, cur = [], ''
    for w in words:
        if not cur:
            cur = w
        elif vis(cur) + 1 + vis(w) <= maxw:
            cur += ' ' + w
        else:
            lines.append(cur); cur = w
        if vis(w) > maxw:      # palavra sozinha estoura -> impossivel
            return None
    if cur:
        lines.append(cur)
    return lines

def rewrap(out_text, tgt_lpp, maxw):
    out_pages = out_text.split('{A}')
    if len(out_pages) != len(tgt_lpp):
        return None
    new = []
    for pi, pg in enumerate(out_pages):
        target = tgt_lpp[pi]
        lead = '\n' if pg.startswith('\n') else ''
        rest = pg[len(lead):]
        rlines = rest.split('\n')
        label = ''
        if rlines and rlines[0].endswith(':'):
            label = rlines[0]; rlines = rlines[1:]
        words = ' '.join(rlines).split()
        budget = target - (1 if lead else 0) - (1 if label else 0)
        packed = greedy(words, maxw)
        if packed is None or len(packed) > budget or budget < 1:
            return None
        newpg = lead + (label + '\n' if label else '') + '\n'.join(packed)
        new.append(newpg)
    return '{A}'.join(new)

# carrega src (envelope alvo) e out
src = {}
for f in glob.glob(os.path.join(BASE, 'parts_src', 'lote_*.json')):
    for e in json.load(open(f)): src[str(e['id'])] = e['texto']
lote_files = {}
out = {}
for f in glob.glob(os.path.join(BASE, 'parts_out', 'lote_*.json')):
    d = json.load(open(f)); out.update({k: (v, f) for k, v in d.items()})

# acha os que estouram por lpp
alvo = []
for i in src:
    if i not in out: continue
    sp, sw, sl = env(src[i]); op, ow, ol = env(out[i][0])
    if sp == op and any(b > a and b > 3 for a, b in zip(sl, ol)):
        alvo.append(i)

fixed, failed = [], []
mudancas = collections.defaultdict(dict)  # file -> {id: novo}
for i in alvo:
    sp, sw, sl = env(src[i])
    maxw = max(sw, 28)
    novo = rewrap(out[i][0], sl, maxw)
    if novo is None:
        failed.append(i); continue
    # confere que agora cabe
    _, ow2, ol2 = env(novo)
    ok = all(not (b > a and b > 3) for a, b in zip(sl, ol2)) and ow2 <= max(sw, 30) + 2
    if ok:
        fixed.append(i); mudancas[out[i][1]][i] = novo
    else:
        failed.append(i)

print(f'alvo (lpp): {len(alvo)} | consertaveis mecanicamente: {len(fixed)} | nao: {len(failed)} {failed}')
if APPLY and fixed:
    for f, upd in mudancas.items():
        d = json.load(open(f))
        d.update(upd)
        json.dump(d, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'APLICADO em {len(mudancas)} arquivos, {len(fixed)} falas reescritas.')
else:
    print('(dry-run; use --apply pra gravar)')
