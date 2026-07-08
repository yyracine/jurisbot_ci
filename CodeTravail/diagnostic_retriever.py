# -*- coding: utf-8 -*-
"""Diagnostic : que renvoie réellement le retriever pour chaque sujet sensible ?"""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from bot_juridique import init_rag_engine

QUERIES = {
    "Q3 heures_sup_plafond": "Quel est le nombre maximum d'heures supplémentaires par semaine et par travailleur ?",
    "Q6 essai_cadres": "Quelle est la durée maximale de la période d'essai pour les ingénieurs et cadres ?",
    "Q8 preavis": "Un travailleur payé au mois avec 6 ans d'ancienneté a-t-il droit à quel préavis ?",
    "Q11 licenciement": "Quel est le taux de l'indemnité de licenciement jusqu'à la 5e année de présence ?",
    "Q13 nuit": "Entre quelles heures se situe la période de travail de nuit ?",
}

print("⚙️  Init moteur RAG (re-indexation avec nouveaux libellés)...")
retriever, llm = init_rag_engine()
print("✅ Prêt.\n")

for name, q in QUERIES.items():
    docs = retriever.invoke(q)
    print("=" * 70)
    print(f"🔎 {name}")
    print(f"   Q: {q}")
    tags = []
    for i, d in enumerate(docs, 1):
        tag = d.metadata.get("source_ref", "???")
        tags.append(tag)
        excerpt = d.page_content.replace("\n", " ")[:90]
        print(f"   [{i}] {tag}")
        print(f"       {excerpt}...")
    # détection contamination Convention vs Décret
    has_conv = any("Convention" in t for t in tags)
    has_decret = any("Décret" in t for t in tags)
    if has_conv and has_decret:
        print("   ⚠️ Mixte Convention + Décret -> le LLM peut confondre les sources")
    print()
