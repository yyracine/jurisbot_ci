#!/usr/bin/env python3
"""
🧪 TEST COMPLET - 15 QUESTIONS ANTI-HALLUCINATIONS
Objectif: Vérifier 0 hallucination sur 15 questions différentes
Répartition: 10 questions valides + 5 questions hors-sujet
"""

import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from bot_juridique import init_rag_engine, ask_legal_bot

load_dotenv()

# ==========================================
# CONFIGURATION
# ==========================================
TEST_RESULTS = []
HALLUCINATION_COUNT = 0
VALID_TEST_COUNT = 0
FALLBACK_TEST_COUNT = 0

print("=" * 90)
print("🧪 TEST DE 15 QUESTIONS - JURISBOT CI")
print("=" * 90)
print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Initialiser le moteur RAG
print("🚀 Initialisation du moteur RAG...")
try:
    retriever, llm = init_rag_engine()
    print("✅ Moteur RAG initialisé avec succès\n")
except Exception as e:
    print(f"❌ Erreur lors de l'initialisation: {e}")
    exit(1)

# ==========================================
# DÉFINITION DES 15 TESTS
# ==========================================

TESTS = [
    # ========== QUESTIONS VALIDES (10) ==========
    {
        "num": 1,
        "type": "VALIDE",
        "question": "Quels sont les droits des travailleurs en matière de congés annuels?",
        "expected_patterns": ["congé", "annuel", "article"],
        "forbidden_patterns": ["pizza", "bitcoin", "restaurant"],
        "description": "Droits aux congés annuels"
    },
    {
        "num": 2,
        "type": "VALIDE",
        "question": "Quel est le délai de préavis pour un licenciement?",
        "expected_patterns": ["préavis", "jour", "licenciement"],
        "forbidden_patterns": ["horoscope", "crypto"],
        "description": "Délai de préavis"
    },
    {
        "num": 3,
        "type": "VALIDE",
        "question": "Qu'est-ce qu'une convention collective?",
        "expected_patterns": ["convention", "collectif", "accord"],
        "forbidden_patterns": ["pizza"],
        "description": "Convention collective"
    },
    {
        "num": 4,
        "type": "VALIDE",
        "question": "Comment sont calculées les heures supplémentaires?",
        "expected_patterns": ["heure", "supplément"],
        "forbidden_patterns": ["horoscope"],
        "description": "Calcul des heures supplémentaires"
    },
    {
        "num": 5,
        "type": "VALIDE",
        "question": "Quelles sont les principales obligations de l'employeur?",
        "expected_patterns": ["employeur", "obligation", "article"],
        "forbidden_patterns": ["bitcoin"],
        "description": "Obligations de l'employeur"
    },
    {
        "num": 6,
        "type": "VALIDE",
        "question": "Qu'est-ce que le télétravail en Côte d'Ivoire?",
        "expected_patterns": ["télétravail", "travail", "accord"],
        "forbidden_patterns": ["pizza"],
        "description": "Télétravail"
    },
    {
        "num": 7,
        "type": "VALIDE",
        "question": "Quels sont les motifs de licenciement valide?",
        "expected_patterns": ["licenciement", "motif", "article"],
        "forbidden_patterns": ["horoscope"],
        "description": "Motifs de licenciement"
    },
    {
        "num": 8,
        "type": "VALIDE",
        "question": "Comment fonctionne la suspension du contrat de travail?",
        "expected_patterns": ["suspension", "contrat", "travail"],
        "forbidden_patterns": ["crypto"],
        "description": "Suspension du contrat"
    },
    {
        "num": 9,
        "type": "VALIDE",
        "question": "Quelles sont les indemnités de licenciement?",
        "expected_patterns": ["indemnité", "licenciement"],
        "forbidden_patterns": ["pizza"],
        "description": "Indemnités de licenciement"
    },
    {
        "num": 10,
        "type": "VALIDE",
        "question": "Quels sont les droits syndicaux des travailleurs?",
        "expected_patterns": ["syndicat", "droit", "article"],
        "forbidden_patterns": ["horoscope"],
        "description": "Droits syndicaux"
    },

    # ========== QUESTIONS HORS-SUJET (5) ==========
    {
        "num": 11,
        "type": "HORS-SUJET",
        "question": "Quel est le meilleur restaurant de Yamoussoukro?",
        "expected_patterns": ["Aucune disposition", "inspecteur du travail"],
        "forbidden_patterns": ["pizza", "restaurant", "manger"],
        "description": "Question non-légale (restaurant)"
    },
    {
        "num": 12,
        "type": "HORS-SUJET",
        "question": "Comment programmer en Python efficacement?",
        "expected_patterns": ["Aucune disposition", "inspecteur du travail"],
        "forbidden_patterns": ["code", "fonction", "python"],
        "description": "Question technique (programmation)"
    },
    {
        "num": 13,
        "type": "HORS-SUJET",
        "question": "Quels conseils pour devenir riche?",
        "expected_patterns": ["Aucune disposition", "inspecteur du travail"],
        "forbidden_patterns": ["riche", "argent", "bitcoin"],
        "description": "Question personnelle (richesse)"
    },
    {
        "num": 14,
        "type": "HORS-SUJET",
        "question": "Qu'est-ce que la relativité générale selon Einstein?",
        "expected_patterns": ["Aucune disposition", "inspecteur du travail"],
        "forbidden_patterns": ["einstein", "physique", "relativité"],
        "description": "Question scientifique (physique)"
    },
    {
        "num": 15,
        "type": "HORS-SUJET",
        "question": "Quel est le plus haut sommet d'Afrique?",
        "expected_patterns": ["Aucune disposition", "inspecteur du travail"],
        "forbidden_patterns": ["kilimandjazo", "everest", "montagne"],
        "description": "Question géographique"
    },
]

# ==========================================
# FONCTION DE TEST
# ==========================================

def run_test(test_config):
    """Exécute un test unique"""
    global HALLUCINATION_COUNT, VALID_TEST_COUNT, FALLBACK_TEST_COUNT

    test_num = test_config["num"]
    test_type = test_config["type"]
    question = test_config["question"]
    expected = test_config["expected_patterns"]
    forbidden = test_config["forbidden_patterns"]
    description = test_config["description"]

    print(f"\n{'='*90}")
    print(f"🧪 TEST {test_num:02d} | {test_type:10} | {description}")
    print(f"{'='*90}")
    print(f"❓ QUESTION: {question}\n")

    result_obj = {
        "test_num": test_num,
        "type": test_type,
        "question": question,
        "description": description,
        "passed": False,
        "hallucinations": [],
        "answer": None,
        "sources_count": 0
    }

    try:
        # Appeler le bot
        result = ask_legal_bot(question, retriever, llm)
        answer = result["answer"]
        sources = result.get("sources", [])

        result_obj["answer"] = answer
        result_obj["sources_count"] = len(sources)

        print(f"✅ RÉPONSE:\n{answer}\n")

        if sources:
            print(f"📚 SOURCES ({len(sources)}):")
            for i, src in enumerate(sources, 1):
                ref = src.get('source_ref', 'N/A')
                snippet = src.get('snippet', 'N/A')[:60]
                print(f"  {i}. {ref} → {snippet}...")
        else:
            print(f"📚 Aucune source utilisée")

        # ============ VÉRIFICATIONS ============
        passed = True
        hallucinations = []

        # --- Vérification 1: Patterns obligatoires ---
        print(f"\n📋 VÉRIFICATION 1 - Patterns OBLIGATOIRES:")
        for pattern in expected:
            if pattern.lower() in answer.lower():
                print(f"  ✅ '{pattern}'")
            else:
                print(f"  ❌ MANQUANT: '{pattern}'")
                passed = False
                hallucinations.append(f"Pattern attendu manquant: {pattern}")

        # --- Vérification 2: Patterns INTERDITS (hallucinations) ---
        print(f"\n🚫 VÉRIFICATION 2 - Patterns INTERDITS (Hallucinations):")
        for pattern in forbidden:
            if pattern.lower() in answer.lower():
                print(f"  🚨 DÉTECTÉ (hallucination!): '{pattern}'")
                passed = False
                HALLUCINATION_COUNT += 1
                hallucinations.append(f"Hallucination détectée: {pattern}")
            else:
                print(f"  ✅ Absent: '{pattern}'")

        # --- Vérification 3: Citations ---
        print(f"\n🔗 VÉRIFICATION 3 - Citations:")
        has_citation = any(x in answer for x in ["Article", "Décret", "Loi", "article", "décret", "loi"])
        if test_type == "VALIDE":
            if has_citation:
                print(f"  ✅ Citée dans la réponse")
            else:
                print(f"  ⚠️  Pas de citation trouvée")
        else:
            if not has_citation:
                print(f"  ✅ Pas de citation (fallback correct)")
            else:
                print(f"  ⚠️  Citation trouvée dans le fallback")

        # Résultat final
        result_obj["passed"] = passed
        result_obj["hallucinations"] = hallucinations

        if passed:
            print(f"\n✅ TEST RÉUSSI")
            if test_type == "VALIDE":
                VALID_TEST_COUNT += 1
            else:
                FALLBACK_TEST_COUNT += 1
        else:
            print(f"\n❌ TEST ÉCHOUÉ - Hallucinations: {len(hallucinations)}")

    except Exception as e:
        print(f"❌ ERREUR: {str(e)}")
        result_obj["error"] = str(e)
        result_obj["passed"] = False

    TEST_RESULTS.append(result_obj)

    # Rate limiting (Mistral API)
    time.sleep(2)


# ==========================================
# EXÉCUTION DES TESTS
# ==========================================

print("\n🚀 DÉMARRAGE DES TESTS...\n")

for test_config in TESTS:
    run_test(test_config)

# ==========================================
# RAPPORT FINAL
# ==========================================

print("\n\n" + "="*90)
print("📊 RAPPORT FINAL - 15 QUESTIONS")
print("="*90)

total_tests = len(TESTS)
passed_tests = sum(1 for t in TEST_RESULTS if t["passed"])
failed_tests = total_tests - passed_tests

print(f"\n📈 STATISTIQUES GLOBALES:")
print(f"  • Total de tests: {total_tests}")
print(f"  • Tests réussis: {passed_tests} ✅")
print(f"  • Tests échoués: {failed_tests} ❌")
print(f"  • Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")

print(f"\n🧪 RÉPARTITION PAR TYPE:")
print(f"  • Questions VALIDES: {VALID_TEST_COUNT}/10 réussis")
print(f"  • Questions HORS-SUJET: {FALLBACK_TEST_COUNT}/5 réussis")

print(f"\n🚨 DÉTECTION DES HALLUCINATIONS:")
print(f"  • Hallucinations détectées: {HALLUCINATION_COUNT}")
if HALLUCINATION_COUNT == 0:
    print(f"  • ✅ OBJECTIF ATTEINT: 0 hallucination!")
else:
    print(f"  • ❌ {HALLUCINATION_COUNT} hallucination(s) trouvée(s)")

# Détails par test
print(f"\n📋 DÉTAILS DES TESTS:")
print(f"\n{'Num':<4} {'Type':<12} {'Résultat':<8} {'Desc':<30}")
print("-" * 60)
for t in TEST_RESULTS:
    status = "✅ PASS" if t["passed"] else "❌ FAIL"
    num = f"{t['test_num']:02d}"
    test_type = t['type'][:11]
    desc = t['description'][:28]
    print(f"{num:<4} {test_type:<12} {status:<8} {desc:<30}")

# Sauvegarder les résultats JSON
output_file = "test_15_questions_results.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "success_rate": (passed_tests/total_tests)*100,
        "hallucination_count": HALLUCINATION_COUNT,
        "valid_tests_passed": VALID_TEST_COUNT,
        "fallback_tests_passed": FALLBACK_TEST_COUNT,
        "results": TEST_RESULTS
    }, f, ensure_ascii=False, indent=2)

print(f"\n💾 Résultats sauvegardés dans: {output_file}")

# Résumé final
print(f"\n{'='*90}")
if HALLUCINATION_COUNT == 0 and passed_tests == total_tests:
    print("🎉 SUCCESS! 15/15 tests réussis - 0 hallucination détectée!")
elif HALLUCINATION_COUNT == 0:
    print(f"⚠️  {passed_tests}/15 tests réussis - 0 hallucination (but {failed_tests} tests failed)")
else:
    print(f"❌ {HALLUCINATION_COUNT} hallucination(s) détectée(s)")
print(f"{'='*90}\n")
