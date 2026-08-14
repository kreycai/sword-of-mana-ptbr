#!/usr/bin/env python3
"""Valida parts_out/*.json contra parts_src: mesmo conjunto de ids,
mesmos codigos de controle {..} (multiconjunto) e mesmo numero de \\n por fala."""
import json, glob, os, re, sys, collections

BASE = os.path.join(os.path.dirname(__file__), "..")
CODE = re.compile(r"\{[^}]*\}")

def codes(t): return collections.Counter(CODE.findall(t))

problemas = 0
lotes = sorted(glob.glob(os.path.join(BASE, "parts_src", "lote_*.json")))
so = sys.argv[1:]  # opcional: nomes de lote pra checar so eles
for src_path in lotes:
    nome = os.path.splitext(os.path.basename(src_path))[0]
    if so and nome not in so:
        continue
    out_path = os.path.join(BASE, "parts_out", nome + ".json")
    if not os.path.exists(out_path):
        print(f"[FALTA] {nome}: sem parts_out")
        problemas += 1
        continue
    src = {str(e["id"]): e["texto"] for e in json.load(open(src_path))}
    out = json.load(open(out_path))
    if set(src) != set(out):
        faltam = set(src) - set(out); sobram = set(out) - set(src)
        print(f"[IDS]   {nome}: faltam={sorted(faltam)[:5]} sobram={sorted(sobram)[:5]}")
        problemas += 1
    for i in src:
        if i not in out:
            continue
        if codes(src[i]) != codes(out[i]):
            print(f"[CODIGO] {nome}#{i}: src={dict(codes(src[i]))} out={dict(codes(out[i]))}")
            problemas += 1
        ns, no = src[i].count("\n"), out[i].count("\n")
        if ns != no:
            print(f"[LINHAS] {nome}#{i}: src={ns} out={no} quebras")
            problemas += 1

print(f"\n== {problemas} problema(s) ==")
sys.exit(1 if problemas else 0)
