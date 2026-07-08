# -*- coding: utf-8 -*-
"""Vérifie que la recherche hybride récupère les Décrets manquants (Q8, Q10)."""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from bot_juridique import init_rag_engine, ask_legal_bot

print("⚙️  Init moteur hybride...")
retriever, llm, hybrid = init_rag_engine()
print("✅ Prêt.\n")

QUERIES = {
    "Q8 preavis (attendu: Décret 96-200)": "Un travailleur payé au mois (catégories 1 à 5) avec 6 ans d'ancienneté a-t-il droit à quel préavis en cas de rupture ?",
    "Q10 cession (attendu: Décret 2014-370 Art.4)": "Quel est le taux de quotité cessible pour un salaire compris entre le SMIG et 200 000 FCFA ?",
}

# On simule juste la récupération hybride sans appeler Mistral
import re
for name, q in QUERIES.items():
    print("=" * 60)
    print(name)
    docs = list(retriever.invoke(q))
    # ajout BM25
    tokens = re.findall(r'\w+', q.lower())
    scores = hybrid["bm25"].get_scores(tokens)
    top = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:5]
    existing = {id(d) for d in docs}
    for idx in top:
        if id(hybrid["splits"][idx]) not in existing and scores[idx] > 0:
            docs.append(hybrid["splits"][idx])
    docs = docs[:8]
    decret_found = False
    for i, d in enumerate(docs, 1):
        src = d.metadata.get("source_ref", "?")
        marker = " <-- DÉCRET" if "Décret" in src else ""
        if "Décret" in src:
            decret_found = True
        print(f"  [{i}] {src}{marker}")
    print(f"  -> Décret présent dans le contexte : {'OUI ✅' if decret_found else 'NON ❌'}\n")
