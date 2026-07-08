# -*- coding: utf-8 -*-
"""
Relance UNIQUEMENT les tests échoués par rate-limit (Q8 à Q13).
Réutilise les questions du module de test principal.
"""
import sys
import io
import time
import traceback
import re as _re
# Ne pas re-wraper stdout : test_hallucination le fait déjà à l'import.
# On force juste l'encodage de la console si nécessaire.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from bot_juridique import init_rag_engine, ask_legal_bot
from test_hallucination import TESTS

# On ne garde que les tests Q8 à Q13
RETRY_IDS = {"Q3_heures_sup_plafond", "Q6_essai_cadres", "Q7_essai_mensuel",
             "Q8_preavis_mensuel_6ans", "Q9_saisie_33", "Q10_cession_smig_200k",
             "Q11_licenciement_taux", "Q12_duree_legale", "Q13_nuit_definition"}
# On re-teste les questions qui avaient posé problème + les sujets sensibles
# pour mesurer l'effet des corrections.
TESTS_RETRY = [t for t in TESTS if t["id"] in RETRY_IDS]


def normalize(text):
    # Normalise : minuscules + supprime espaces autour de % et des nombres
    # pour que "35 %" == "35%" et "30 %" == "30%"
    t = text.lower()
    t = _re.sub(r'\s*%\s*', '%', t)
    t = _re.sub(r'\s+', ' ', t)
    return t


def main():
    print("⚙️  Init moteur RAG...")
    retriever, llm, hybrid = init_rag_engine()
    print("✅ Prêt.\n")

    results = []
    for i, test in enumerate(TESTS_RETRY, 1):
        print("\n" + "─" * 70)
        print(f"[{i}/{len(TESTS_RETRY)}] {test['id']}")
        print(f"   ❓ {test['query']}")
        print(f"   📖 {test['reference']} | Vérité: {test['ground_truth']}")

        answer = ""
        error = None
        for attempt in range(5):
            try:
                t0 = time.time()
                result = ask_legal_bot(query=test["query"], retriever=retriever, llm=llm, hybrid=hybrid)
                answer = result.get("answer", "")
                elapsed = time.time() - t0
                error = None
                break
            except Exception as e:
                error = repr(e)
                if "429" in error:
                    wait = 25 * (attempt + 1)
                    print(f"   ⏳ 429, attente {wait}s...")
                    time.sleep(wait)
                else:
                    traceback.print_exc()
                    break
            time.sleep(10)

        if error:
            status = "ERREUR"
            details = [f"Exception: {error}"]
        else:
            ans_low = normalize(answer)
            must_ok = [s for s in test["must_contain"] if normalize(s) in ans_low]
            must_ko = [s for s in test["must_not_contain"] if normalize(s) in ans_low]
            must_pass = len(must_ok) >= 1
            no_hallu = len(must_ko) == 0
            if must_pass and no_hallu:
                status = "PASS ✅"
            elif not must_pass and not no_hallu:
                status = "HALLUCINATION 🚨"
            elif not must_pass:
                status = "FAIL ❌ (valeur absente)"
            else:
                status = "HALLUCINATION 🚨"
            details = []
            if must_ok:
                details.append(f"trouvé: {must_ok}")
            if must_ko:
                details.append(f"HALLUCINATION: {must_ko}")

        preview = answer.replace("\n", " ")[:400]
        print(f"   🤖 ({elapsed:.1f}s) : {preview}")
        print(f"   🔎 {status}")
        for d in details:
            print(f"      • {d}")

        results.append({"id": test["id"], "status": status, "answer": answer,
                        "query": test["query"], "reference": test["reference"],
                        "ground_truth": test["ground_truth"], "details": details})
        time.sleep(12)  # délai entre questions

    # Sauvegarde
    with open("rapport_hallucination_retry.md", "w", encoding="utf-8") as f:
        f.write("# Rapport complémentaire (tests Q8-Q13)\n\n")
        for r in results:
            emoji = "✅" if r["status"].startswith("PASS") else ("🚨" if "HALLUCINATION" in r["status"] else "❌")
            f.write(f"## {emoji} {r['id']} — {r['status']}\n\n")
            f.write(f"**Question** : {r['query']}\n\n")
            f.write(f"**Référence attendue** : {r['reference']}\n\n")
            f.write(f"**Vérité terrain** : {r['ground_truth']}\n\n")
            f.write(f"**Réponse du bot** :\n\n> {r['answer']}\n\n")
            f.write(f"**Analyse** : {'; '.join(r['details'])}\n\n---\n\n")
    print("\n📄 Sauvegardé dans rapport_hallucination_retry.md")


if __name__ == "__main__":
    main()
