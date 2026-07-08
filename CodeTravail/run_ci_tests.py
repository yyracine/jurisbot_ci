# -*- coding: utf-8 -*-
"""
Runner de tests pour l'intégration continue (CI).

Exécute les DEUX jeux de tests anti-hallucination (26 questions au total)
et renvoie un code de sortie non nul si :
  - une hallucination est détectée (numéro/date inventé, mauvaise source), OU
  - une valeur attendue est absente, OU
  - une erreur d'exécution survient.

Usage :
    python run_ci_tests.py            # exécute les 2 jeux
    python run_ci_tests.py --jeu1     # jeu 1 seulement
    python run_ci_tests.py --jeu2     # jeu 2 seulement

Conçu pour GitHub Actions : échec du job = code != 0.
"""
import sys
import time
import traceback

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from bot_juridique import init_rag_engine, ask_legal_bot
from test_hallucination import TESTS as JEU1
from test_hallucination_jeu2 import TESTS as JEU2


def normalize(text):
    import re as _re
    t = text.lower()
    t = _re.sub(r'\s*%\s*', '%', t)
    t = _re.sub(r'\s+', ' ', t)
    return t


def evaluer_une_reponse(test, answer):
    """Retourne (ok: bool, raisons: list[str])."""
    raisons = []
    ans_low = normalize(answer)

    must_ok = [s for s in test["must_contain"] if normalize(s) in ans_low]
    must_ko = [s for s in test["must_not_contain"] if normalize(s) in ans_low]

    if not must_ok:  # aucune valeur attendue trouvée
        raisons.append(f"valeur attendue absente (cherchée: {test['must_contain']})")
    if must_ko:
        raisons.append(f"HALLUCINATION détectée: {must_ko}")
    return (len(raisons) == 0), raisons


def jouer_jeu(nom_jeu, tests, retriever, llm, hybrid):
    print("\n" + "=" * 70)
    print(f"  {nom_jeu} ({len(tests)} questions)")
    print("=" * 70)

    echecs = 0
    for i, test in enumerate(tests, 1):
        print(f"\n[{i}/{len(tests)}] {test['id']} — {test['query'][:60]}...")

        answer = ""
        error = None
        for attempt in range(5):
            try:
                result = ask_legal_bot(
                    query=test["query"], retriever=retriever, llm=llm, hybrid=hybrid
                )
                answer = result.get("answer", "")
                error = None
                break
            except Exception as e:
                error = repr(e)
                if "429" in error:
                    wait = 20 * (attempt + 1)
                    print(f"   ⏳ Rate limité (429), attente {wait}s...")
                    time.sleep(wait)
                else:
                    traceback.print_exc()
                    break
            time.sleep(8)

        if error:
            print(f"   ❌ ERREUR: {error}")
            echecs += 1
            continue

        ok, raisons = evaluer_une_reponse(test, answer)
        if ok:
            print(f"   ✅ PASS")
        else:
            print(f"   ❌ FAIL: {'; '.join(raisons)}")
            print(f"      Réf. attendue : {test['reference']}")
            print(f"      Vérité terrain : {test['ground_truth']}")
            print(f"      Réponse bot : {answer[:200]}...")
            echecs += 1
        time.sleep(10)  # éviter le rate-limit Mistral

    return echecs


def main():
    args = set(sys.argv[1:])
    lancer_jeu1 = "--jeu2" not in args
    lancer_jeu2 = "--jeu1" not in args

    print("⚙️  Initialisation du moteur RAG hybride (peut prendre ~1 min)...")
    retriever, llm, hybrid = init_rag_engine()
    print("✅ Moteur prêt.\n")

    total_echecs = 0
    if lancer_jeu1:
        total_echecs += jouer_jeu("JEU 1 — Sujets fondamentaux", JEU1, retriever, llm, hybrid)
    if lancer_jeu2:
        total_echecs += jouer_jeu("JEU 2 — Sujets nouveaux", JEU2, retriever, llm, hybrid)

    print("\n\n" + "=" * 70)
    if total_echecs == 0:
        print("  ✅✅✅  SUCCÈS : tous les tests anti-hallucination sont passés.")
        print("=" * 70)
        sys.exit(0)
    else:
        print(f"  ❌❌❌  ÉCHEC : {total_echecs} test(s) en échec (hallucination ou valeur absente).")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
