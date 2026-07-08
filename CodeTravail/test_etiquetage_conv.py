# -*- coding: utf-8 -*-
"""Vérifie l'étiquetage des chunks après le fix Convention Collective."""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from bot_juridique import init_rag_engine

print("⚙️  Init moteur...")
retriever, llm, hybrid = init_rag_engine()
print("✅ Prêt.\n")

splits = hybrid["splits"]

# 1. Compter les étiquettes par type
from collections import Counter
counts = Counter()
for c in splits:
    tag = c.metadata.get("source_ref", "?")
    # regrouper
    key = ("Décret" if "Décret" in tag else
           "Convention" if "Convention" in tag else
           "Arrêté" if "Arrêté" in tag or "Arrete" in tag else
           "Loi" if "Loi" in tag else "Autre")
    counts[key] += 1
print("Répartition des étiquettes par type :")
for k, v in counts.most_common():
    print(f"  {k}: {v} chunks")

# 2. Vérifier les chunks contenant "âge du départ à la retraite est fixé à 55"
print("\n--- Vérif: âge retraite (55 ans, doit être Convention) ---")
for i, c in enumerate(splits):
    if "55 ans" in c.page_content and "départ" in c.page_content.lower():
        print(f"  chunk#{i}: {c.metadata.get('source_ref')}")
        break

# 3. Vérifier les chunks contenant "montant total ... 25 fois"
print("--- Vérif: plafond indemnité retraite (25 x SMIG, doit être Convention) ---")
for i, c in enumerate(splits):
    if "25 fois" in c.page_content or "ne peut excéder 25" in c.page_content:
        print(f"  chunk#{i}: {c.metadata.get('source_ref')}")
        break

# 4. Vérifier qu'un chunk du Décret 96-203 est toujours bien étiqueté
print("--- Vérif: Décret 96-203 (doit rester Décret) ---")
for i, c in enumerate(splits):
    if "DECRET N° 96-203" in c.page_content or "Décret n° 96-203" in c.page_content:
        print(f"  chunk#{i}: {c.metadata.get('source_ref')}")
        break

# 5. Vérifier prime d'ancienneté
print("--- Vérif: prime d'ancienneté (doit être Convention) ---")
for i, c in enumerate(splits):
    if "prime d'ancienneté" in c.page_content.lower() and "2 %" in c.page_content:
        print(f"  chunk#{i}: {c.metadata.get('source_ref')}")
        break
