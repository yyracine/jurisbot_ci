#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST COMPLET - 15 QUESTIONS ANTI-HALLUCINATIONS
Objectif: Verifier 0 hallucination sur 15 questions differentes
"""

import os
import json
import time
import sys
from datetime import datetime
from dotenv import load_dotenv

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from bot_juridique import init_rag_engine, ask_legal_bot

load_dotenv()

# Configuration
TEST_RESULTS = []
HALLUCINATION_COUNT = 0
VALID_TEST_COUNT = 0
FALLBACK_TEST_COUNT = 0

print("=" * 90)
print("TEST DE 15 QUESTIONS - JURISBOT CI")
print("=" * 90)
print("Timestamp: {}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

# Initialiser le moteur RAG
print("Initialisation du moteur RAG...")
try:
    retriever, llm = init_rag_engine()
    print("OK - Moteur RAG initialise\n")
except Exception as e:
    print("ERREUR lors de l'initialisation: {}".format(e))
    exit(1)

# Definition des 15 tests
TESTS = [
    # QUESTIONS VALIDES (10)
    {
        "num": 1,
        "type": "VALIDE",
        "question": "Quels sont les droits des travailleurs en matiere de conges annuels?",
        "expected_patterns": ["conge", "annuel", "article"],
        "forbidden_patterns": ["pizza", "bitcoin", "restaurant"],
        "description": "Droits aux conges annuels"
    },
    {
        "num": 2,
        "type": "VALIDE",
        "question": "Quel est le delai de preavis pour un licenciement?",
        "expected_patterns": ["preavis", "jour", "licenciement"],
        "forbidden_patterns": ["horoscope", "crypto"],
        "description": "Delai de preavis"
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
        "question": "Comment sont calculees les heures supplementaires?",
        "expected_patterns": ["heure", "supplement"],
        "forbidden_patterns": ["horoscope"],
        "description": "Calcul des heures supplementaires"
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
        "question": "Qu'est-ce que le teletravail en Cote d'Ivoire?",
        "expected_patterns": ["teletravail", "travail", "accord"],
        "forbidden_patterns": ["pizza"],
        "description": "Teletravail"
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
        "question": "Quelles sont les indemnites de licenciement?",
        "expected_patterns": ["indemnite", "licenciement"],
        "forbidden_patterns": ["pizza"],
        "description": "Indemnites de licenciement"
    },
    {
        "num": 10,
        "type": "VALIDE",
        "question": "Quels sont les droits syndicaux des travailleurs?",
        "expected_patterns": ["syndicat", "droit", "article"],
        "forbidden_patterns": ["horoscope"],
        "description": "Droits syndicaux"
    },
    # QUESTIONS HORS-SUJET (5)
    {
        "num": 11,
        "type": "HORS-SUJET",
        "question": "Quel est le meilleur restaurant de Yamoussoukro?",
        "expected_patterns": ["Aucune disposition", "inspecteur"],
        "forbidden_patterns": ["pizza", "restaurant", "manger"],
        "description": "Question non-legale (restaurant)"
    },
    {
        "num": 12,
        "type": "HORS-SUJET",
        "question": "Comment programmer en Python efficacement?",
        "expected_patterns": ["Aucune disposition", "inspecteur"],
        "forbidden_patterns": ["code", "fonction", "python"],
        "description": "Question technique (programmation)"
    },
    {
        "num": 13,
        "type": "HORS-SUJET",
        "question": "Quels conseils pour devenir riche?",
        "expected_patterns": ["Aucune disposition", "inspecteur"],
        "forbidden_patterns": ["riche", "argent", "bitcoin"],
        "description": "Question personnelle (richesse)"
    },
    {
        "num": 14,
        "type": "HORS-SUJET",
        "question": "Qu'est-ce que la relativite generale selon Einstein?",
        "expected_patterns": ["Aucune disposition", "inspecteur"],
        "forbidden_patterns": ["einstein", "physique", "relativite"],
        "description": "Question scientifique (physique)"
    },
    {
        "num": 15,
        "type": "HORS-SUJET",
        "question": "Quel est le plus haut sommet d'Afrique?",
        "expected_patterns": ["Aucune disposition", "inspecteur"],
        "forbidden_patterns": ["kilimanjaro", "everest", "montagne"],
        "description": "Question geographique"
    },
]

def run_test(test_config):
    """Execute un test unique"""
    global HALLUCINATION_COUNT, VALID_TEST_COUNT, FALLBACK_TEST_COUNT

    test_num = test_config["num"]
    test_type = test_config["type"]
    question = test_config["question"]
    expected = test_config["expected_patterns"]
    forbidden = test_config["forbidden_patterns"]
    description = test_config["description"]

    print("\n" + "="*90)
    print("TEST {:02d} | {:10} | {}".format(test_num, test_type, description))
    print("="*90)
    print("QUESTION: {}\n".format(question))

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
        result = ask_legal_bot(question, retriever, llm)
        answer = result["answer"]
        sources = result.get("sources", [])

        result_obj["answer"] = answer
        result_obj["sources_count"] = len(sources)

        print("REPONSE:\n{}\n".format(answer))

        if sources:
            print("SOURCES ({}):\n".format(len(sources)))
            for i, src in enumerate(sources, 1):
                ref = src.get('source_ref', 'N/A')
                snippet = src.get('snippet', 'N/A')[:60]
                print("  {}. {} -> {}...".format(i, ref, snippet))
        else:
            print("Aucune source utilisee\n")

        # VERIFICATIONS
        passed = True
        hallucinations = []

        print("\nVERIFICATION 1 - Patterns OBLIGATOIRES:")
        for pattern in expected:
            if pattern.lower() in answer.lower():
                print("  OK - '{}'".format(pattern))
            else:
                print("  MANQUANT - '{}'".format(pattern))
                passed = False
                hallucinations.append("Pattern attendu manquant: {}".format(pattern))

        print("\nVERIFICATION 2 - Patterns INTERDITS (Hallucinations):")
        for pattern in forbidden:
            if pattern.lower() in answer.lower():
                print("  ALERTE - Hallucination trouvee: '{}'".format(pattern))
                passed = False
                HALLUCINATION_COUNT += 1
                hallucinations.append("Hallucination detectee: {}".format(pattern))
            else:
                print("  OK - Absent: '{}'".format(pattern))

        result_obj["passed"] = passed
        result_obj["hallucinations"] = hallucinations

        if passed:
            print("\nRESULTAT: OK")
            if test_type == "VALIDE":
                VALID_TEST_COUNT += 1
            else:
                FALLBACK_TEST_COUNT += 1
        else:
            print("\nRESULTAT: ECHEC - {} hallucinations".format(len(hallucinations)))

    except Exception as e:
        print("ERREUR: {}".format(str(e)))
        result_obj["error"] = str(e)
        result_obj["passed"] = False

    TEST_RESULTS.append(result_obj)
    time.sleep(2)  # Rate limiting

# EXECUTION
print("\nDEMARRAGE DES TESTS...\n")

for test_config in TESTS:
    run_test(test_config)

# RAPPORT FINAL
print("\n\n" + "="*90)
print("RAPPORT FINAL - 15 QUESTIONS")
print("="*90)

total_tests = len(TESTS)
passed_tests = sum(1 for t in TEST_RESULTS if t["passed"])
failed_tests = total_tests - passed_tests

print("\nSTATISTIQUES GLOBALES:")
print("  - Total de tests: {}".format(total_tests))
print("  - Tests reussis: {} (OK)".format(passed_tests))
print("  - Tests echoues: {} (ECHEC)".format(failed_tests))
print("  - Taux de reussite: {:.1f}%".format((passed_tests/total_tests)*100))

print("\nREPARTITION PAR TYPE:")
print("  - Questions VALIDES: {}/10 reussis".format(VALID_TEST_COUNT))
print("  - Questions HORS-SUJET: {}/5 reussis".format(FALLBACK_TEST_COUNT))

print("\nDETECTION DES HALLUCINATIONS:")
print("  - Hallucinations detectees: {}".format(HALLUCINATION_COUNT))
if HALLUCINATION_COUNT == 0:
    print("  - OBJECTIF ATTEINT: 0 hallucination!")
else:
    print("  - ALERTE: {} hallucination(s) trouvee(s)".format(HALLUCINATION_COUNT))

print("\nDETAILS DES TESTS:")
print("{:<4} {:<12} {:<8} {:<30}".format("Num", "Type", "Resultat", "Description"))
print("-" * 60)
for t in TEST_RESULTS:
    status = "OK" if t["passed"] else "ECHEC"
    num = "{:02d}".format(t['test_num'])
    test_type = t['type'][:11]
    desc = t['description'][:28]
    print("{:<4} {:<12} {:<8} {:<30}".format(num, test_type, status, desc))

# Sauvegarder resultats JSON
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
        "objective_achieved": HALLUCINATION_COUNT == 0,
        "results": TEST_RESULTS
    }, f, ensure_ascii=False, indent=2)

print("\nResultats sauvegarde dans: {}".format(output_file))

# Resume final
print("\n" + "="*90)
if HALLUCINATION_COUNT == 0 and passed_tests == total_tests:
    print("SUCCESS! 15/15 tests reussis - 0 hallucination detectee!")
elif HALLUCINATION_COUNT == 0:
    print("{}/15 tests reussis - 0 hallucination (mais {} tests echoues)".format(passed_tests, failed_tests))
else:
    print("ALERTE: {} hallucination(s) detectee(s)".format(HALLUCINATION_COUNT))
print("="*90 + "\n")
