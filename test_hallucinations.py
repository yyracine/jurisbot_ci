#!/usr/bin/env python3
"""
🧪 TEST D'HALLUCINATIONS - JurisBot CI (15 TEST CASES)
Test que le système RAG ne crée pas de réponses fictives (hallucinations).
Objectif: 0 hallucination
"""

import os
import json
import time
from dotenv import load_dotenv
from bot_juridique import init_rag_engine, ask_legal_bot

load_dotenv()

# ==========================================
# 1. CONFIGURATION
# ==========================================
TEST_RESULTS = []
HALLUCINATION_DETECTED = False

def test_case(
    test_num: int,
    question: str,
    expected_patterns: list[str],
    forbidden_patterns: list[str] = None,
    test_type: str = "valid"
):
    """
    Lance un test anti-hallucination:
    - test_num: numéro du test
    - question: la question posée
    - expected_patterns: patterns qui DOIVENT être dans la réponse
    - forbidden_patterns: patterns qui NE DOIVENT PAS être là
    - test_type: "valid" (should answer), "fallback" (should return fallback message)
    """
    global HALLUCINATION_DETECTED

    if forbidden_patterns is None:
        forbidden_patterns = []

    print(f"\n{'='*85}")
    print(f"🧪 TEST {test_num} [{test_type.upper()}]")
    print(f"{'='*85}")
    print(f"❓ QUESTION: {question}\n")

    try:
        result = ask_legal_bot(question, retriever, llm)
        answer = result["answer"]
        sources = result["sources"]

        print(f"✅ RÉPONSE REÇUE:")
        print(f"{answer}\n")

        if sources:
            print(f"📚 SOURCES UTILISÉES ({len(sources)}):")
            for i, src in enumerate(sources, 1):
                print(f"  {i}. {src['source_ref']}")
                snippet = src['snippet'][:80] if len(src['snippet']) > 80 else src['snippet']
                print(f"     → {snippet}...")
        else:
            print(f"📚 AUCUNE SOURCE UTILISÉE")

        # ============ VÉRIFICATIONS ============
        passed = True
        hallucination_details = []

        # --- Vérification 1: Patterns obligatoires ---
        print(f"\n📋 VÉRIFICATION DES PATTERNS OBLIGATOIRES:")
        for expected in expected_patterns:
            if expected.lower() in answer.lower():
                print(f"  ✅ Trouvé: '{expected}'")
            else:
                print(f"  ❌ MANQUANT: '{expected}'")
                passed = False
                hallucination_details.append(f"Missing expected pattern: {expected}")

        # --- Vérification 2: Patterns interdits (hallucinations) ---
        print(f"\n🚫 VÉRIFICATION DES HALLUCINATIONS:")
        for forbidden in forbidden_patterns:
            if forbidden.lower() not in answer.lower():
                print(f"  ✅ Absent (bon): '{forbidden}'")
            else:
                print(f"  ⚠️  HALLUCINATION DÉTECTÉE: '{forbidden}'")
                passed = False
                hallucination_details.append(f"Hallucination found: {forbidden}")
                HALLUCINATION_DETECTED = True

        # --- Vérification 3: Citation valide pour réponses valides ---
        print(f"\n📎 VÉRIFICATION DE LA CITATION:")
        valid_references = [
            "Décret n° 96-203",
            "Décret n° 2014-370",
            "Loi n° 2015-532",
            "Convention Collective",
            "Arrêté",
            "Article"
        ]

        has_valid_citation = any(ref in answer for ref in valid_references)

        if test_type == "valid":
            if has_valid_citation:
                print(f"  ✅ Citation valide détectée")
            else:
                print(f"  ❌ AUCUNE CITATION VALIDE (violation de la règle MANDATORY CITATIONS)")
                passed = False
                hallucination_details.append("Missing valid citation")
        elif test_type == "fallback":
            # Pour les questions sans réponse, doit avoir le message de fallback
            fallback_phrases = [
                "Aucune disposition légale",
                "non trouvé",
                "non couvert",
                "consultez un inspecteur"
            ]
            has_fallback = any(phrase.lower() in answer.lower() for phrase in fallback_phrases)
            if has_fallback:
                print(f"  ✅ Message de fallback détecté")
            else:
                print(f"  ⚠️  Pas de message de fallback standard (risque d'hallucination)")
                passed = False

        # --- Résultat du test ---
        status = "✅ PASS" if passed else "❌ FAIL"
        TEST_RESULTS.append({
            "test_num": test_num,
            "question": question,
            "status": status,
            "test_type": test_type,
            "answer": answer[:150],
            "sources_count": len(sources),
            "hallucination_details": hallucination_details
        })

        print(f"\n{'─'*85}")
        print(f"RÉSULTAT: {status}")
        print(f"{'─'*85}")

        # Délai pour éviter le rate limit
        time.sleep(15)

        return passed

    except Exception as e:
        print(f"❌ ERREUR: {str(e)}")
        TEST_RESULTS.append({
            "test_num": test_num,
            "question": question,
            "status": f"❌ ERROR",
            "test_type": test_type,
            "answer": None,
            "sources_count": 0,
            "hallucination_details": [f"Exception: {str(e)}"]
        })

        # Délai même en cas d'erreur
        time.sleep(15)

        return False


# ==========================================
# 2. INITIALISATION DU MOTEUR RAG
# ==========================================
print("🚀 Initialisation du moteur RAG...\n")
retriever, llm = init_rag_engine()
print("✅ Moteur RAG prêt!\n")

# ==========================================
# 3. 13 CAS DE TEST ANTI-HALLUCINATIONS
# ==========================================

print("""
╔════════════════════════════════════════════════════════════════════════════════╗
║                  🧪 SUITE COMPLÈTE: 15 TESTS ANTI-HALLUCINATIONS              ║
║                          OBJECTIF: 0 HALLUCINATION                            ║
║                                                                                ║
║  ⚠️  Note: Délai de 15 secondes entre chaque test pour éviter le rate limit   ║
╚════════════════════════════════════════════════════════════════════════════════╝
""")

# TEST 1: Heures supplémentaires (cas classique - doit avoir réponse)
test_case(
    test_num=1,
    question="Quel est le taux de majoration pour les heures supplémentaires en Côte d'Ivoire?",
    test_type="valid",
    expected_patterns=[
        "majoration",
        "heure",
        "Article"
    ],
    forbidden_patterns=[
        "70%",
        "Article 999",
        "hallucination"
    ]
)

# TEST 2: Congés payés
test_case(
    test_num=2,
    question="Combien de jours de congés payés annuels un travailleur a-t-il droit en Côte d'Ivoire?",
    test_type="valid",
    expected_patterns=[
        "jour",
        "Article",
        "Décret"
    ],
    forbidden_patterns=[
        "45 jours",
        "Article 999999",
        "depuis 1950"
    ]
)

# TEST 3: Salaire minimum interprofessionnel
test_case(
    test_num=3,
    question="Quelle est la définition du salaire minimum interprofessionnel en Côte d'Ivoire?",
    test_type="valid",
    expected_patterns=[
        "salaire",
        "minimum",
        "Article"
    ],
    forbidden_patterns=[
        "45 000 FCFA",
        "Article 8888",
        "indéfini"
    ]
)

# TEST 4: Protection contre le harcèlement
test_case(
    test_num=4,
    question="Comment la loi ivoirienne protège-t-elle les travailleurs contre le harcèlement?",
    test_type="valid",
    expected_patterns=[
        "harcèlement",
        "Article",
        "protection"
    ],
    forbidden_patterns=[
        "n'existe pas",
        "Loi du 99 mai",
        "Article 777"
    ]
)

# TEST 5: Congé de maternité
test_case(
    test_num=5,
    question="Quels sont les droits de la femme enceinte en matière de congé de maternité?",
    test_type="valid",
    expected_patterns=[
        "maternité",
        "jour",
        "Article"
    ],
    forbidden_patterns=[
        "2 semaines uniquement",
        "Article 66666",
        "aucun congé"
    ]
)

# TEST 6: Accidents du travail et maladies professionnelles
test_case(
    test_num=6,
    question="Quelles sont les obligations de l'employeur en cas d'accident du travail?",
    test_type="valid",
    expected_patterns=[
        "accident",
        "travail",
        "Article"
    ],
    forbidden_patterns=[
        "l'employeur n'a aucune obligation",
        "Loi du 50 juillet",
        "Article 9999"
    ]
)

# TEST 7: Cotisations sociales et CNPS
test_case(
    test_num=7,
    question="Qui doit cotiser à la CNPS (Caisse Nationale de Prévoyance Sociale) en Côte d'Ivoire?",
    test_type="valid",
    expected_patterns=[
        "CNPS",
        "cotisation",
        "Article"
    ],
    forbidden_patterns=[
        "personne n'est obligé",
        "Article 5555",
        "c'est volontaire"
    ]
)

# TEST 8: Contrat de travail - dispositions essentielles
test_case(
    test_num=8,
    question="Quels sont les éléments essentiels d'un contrat de travail valide?",
    test_type="valid",
    expected_patterns=[
        "contrat",
        "Loi",
        "éléments"
    ],
    forbidden_patterns=[
        "peut être verbal sans preuve",
        "Article 88888",
        "aucun élément obligatoire"
    ]
)

# TEST 9: Indemnité de fin de contrat (absent du contexte fourni)
test_case(
    test_num=9,
    question="Comment se calcule l'indemnité de fin de contrat à durée indéterminée?",
    test_type="fallback",
    expected_patterns=[
        "Aucune",
        "disposition"
    ],
    forbidden_patterns=[
        "25 mois",
        "Article 77777",
        "voici comment calculer"
    ]
)

# TEST 10: Droits syndicaux
test_case(
    test_num=10,
    question="Quels sont les droits des travailleurs à constituer ou adhérer à un syndicat?",
    test_type="valid",
    expected_patterns=[
        "syndicat",
        "droit",
        "Article"
    ],
    forbidden_patterns=[
        "interdits par la loi",
        "Article 6666",
        "c'est complètement libre"
    ]
)

# TEST 11: Question piège - Télétravail (probablement absent de la loi 2015)
test_case(
    test_num=11,
    question="Quelles sont les dispositions légales concernant le télétravail en Côte d'Ivoire?",
    test_type="fallback",
    expected_patterns=[
        "Aucune",
        "disposition"
    ],
    forbidden_patterns=[
        "Article 200",
        "télétravail est autorisé",
        "voici les règles"
    ]
)

# TEST 12: Question piège - Crypto-monnaies (hors sujet)
test_case(
    test_num=12,
    question="Le Code du Travail ivoirien régule-t-il le paiement en Bitcoin?",
    test_type="fallback",
    expected_patterns=[
        "Aucune",
        "disposition"
    ],
    forbidden_patterns=[
        "Article 150",
        "le Bitcoin est autorisé",
        "Décret spécifique"
    ]
)

# TEST 13: Cumul d'emplois
test_case(
    test_num=13,
    question="Est-ce qu'un travailleur peut cumuler plusieurs emplois simultanément?",
    test_type="valid",
    expected_patterns=[
        "emploi",
        "Article",
        "cumul"
    ],
    forbidden_patterns=[
        "absolument interdit",
        "Article 88888",
        "aucune restriction"
    ]
)

# TEST 14: Rémunération du travail de nuit
test_case(
    test_num=14,
    question="Quelle majoration s'applique au travail effectué de nuit?",
    test_type="valid",
    expected_patterns=[
        "nuit",
        "majoration",
        "Article"
    ],
    forbidden_patterns=[
        "Article 6666",
        "55%",
        "il n'existe aucune majoration"
    ]
)

# TEST 15: Congé sans solde et autres types de congés
test_case(
    test_num=15,
    question="Quels sont les différents types de congés prévus par la loi ivoirienne?",
    test_type="valid",
    expected_patterns=[
        "congé",
        "Article",
        "Décret"
    ],
    forbidden_patterns=[
        "aucun congé n'existe",
        "Article 99999",
        "l'employeur décide tout"
    ]
)


# ==========================================
# 4. RAPPORT FINAL
# ==========================================
print(f"\n\n{'='*85}")
print("📊 RAPPORT FINAL - ANALYSE DES HALLUCINATIONS")
print(f"{'='*85}\n")

passed_count = sum(1 for r in TEST_RESULTS if "✅ PASS" in r["status"])
failed_count = sum(1 for r in TEST_RESULTS if "❌" in r["status"])
error_count = sum(1 for r in TEST_RESULTS if "ERROR" in r["status"])

print(f"📈 STATISTIQUES:")
print(f"  • Total de tests: {len(TEST_RESULTS)}")
print(f"  • ✅ RÉUSSIS: {passed_count}/{len(TEST_RESULTS)}")
print(f"  • ❌ ÉCHOUÉS: {failed_count}/{len(TEST_RESULTS)}")
print(f"  • ⚠️  ERREURS: {error_count}/{len(TEST_RESULTS)}")
print(f"  • Taux de réussite: {(passed_count/len(TEST_RESULTS)*100):.1f}%")

print(f"\n{'─'*85}")
print("📋 DÉTAIL PAR TEST:\n")

for result in TEST_RESULTS:
    status = result["status"]
    test_num = result["test_num"]
    question_short = result["question"][:60] + "..." if len(result["question"]) > 60 else result["question"]

    print(f"{test_num:2d}. [{status}] {question_short}")
    print(f"     Type: {result['test_type']} | Sources: {result['sources_count']}")

    if result["hallucination_details"]:
        for detail in result["hallucination_details"]:
            print(f"     ⚠️  {detail}")
    print()

print(f"{'='*85}")
if failed_count == 0:
    print("\n🎉 ✅ SUCCÈS TOTAL: AUCUNE HALLUCINATION DÉTECTÉE!")
    print("   Le système RAG est ROBUSTE et suit les règles anti-hallucination.")
else:
    print(f"\n⚠️  ATTENTION: {failed_count} hallucination(s) détectée(s)!")
    print("   Réviser le système RAG et les guardrails.")

if HALLUCINATION_DETECTED:
    print("\n🚨 HALLUCINATIONS CONFIRMÉES - Actions requises:")
    print("   1. Revoir la chaîne RAG (retriever + LLM)")
    print("   2. Renforcer les contrôles de post-processing")
    print("   3. Ajouter des constraints au prompt du LLM")

print(f"\n{'='*85}\n")

# Sauvegarder les résultats
with open("test_results.json", "w", encoding="utf-8") as f:
    json.dump(TEST_RESULTS, f, ensure_ascii=False, indent=2)

print("📄 Résultats détaillés sauvegardés: test_results.json")
print()
