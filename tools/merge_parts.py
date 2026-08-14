#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge parts_out/*.json -> traducao_ptbr.json.
As traducoes ja existentes em traducao_ptbr.json (curadas/testadas a mao)
TEM PRECEDENCIA sobre as do parts_out. Faz backup antes de escrever."""
import json, glob, os, shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALVO = os.path.join(BASE, "traducao_ptbr.json")

# 1) junta tudo do parts_out
merged = {}
for f in sorted(glob.glob(os.path.join(BASE, "parts_out", "lote_*.json"))):
    for k, v in json.load(open(f, encoding="utf-8")).items():
        merged[str(k)] = v
print(f"parts_out: {len(merged)} falas em {len(glob.glob(os.path.join(BASE,'parts_out','lote_*.json')))} lotes")

# 2) overlay das curadas existentes (elas vencem)
curadas = {}
if os.path.exists(ALVO):
    curadas = json.load(open(ALVO, encoding="utf-8"))
    shutil.copy(ALVO, ALVO + ".bak")
    print(f"curadas (precedencia): {len(curadas)} falas -> backup em traducao_ptbr.json.bak")
final = {**merged, **{str(k): v for k, v in curadas.items()}}

# ordena por id numerico
final = {k: final[k] for k in sorted(final, key=lambda x: int(x))}
json.dump(final, open(ALVO, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"gravado {ALVO}: {len(final)} falas totais")
