#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST FINAL - 15 QUESTIONS ANTI-HALLUCINATIONS
Objectif: Verifier 0 hallucination sur 15 questions differentes
Version amelioree avec normalisation des accents
"""

import os
import json
import time
import sys
import unicodedata
from datetime import datetime
from dotenv import load_dotenv

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from bot_juridique import init_rag_engine, ask_legal_bot

load_dotenv()

def remove_accents(text):
    """Enleve les accents d'un texte"""
    nfd = unicodedata.normalize('NFD', text)
    return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')

# Configuration
TEST_RESULTS = []
HALLUCINATION_COUNT = 0
VALID_TEST_COUNT = 0
FALLBACK_TEST_COUNT = 0

print("=" * 90)
print("TEST FINAL - 15 QUESTIONS - JURISBOT CI")
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

# Definition des 15 tests AMELIOREE
TESTS = [
    # QUESTIONS VALIDES (10)
    {
        "num": 1,
        "type": "VALIDE",
        "question": "Quels sont les droits des travailleurs en matiere de conges annuels?",
        "expected_patterns": ["conge", "annuel", "article", "travail"],
        "forbidden_patterns": [],
        "description": "Droits aux conges annuels"
    },
    {
        "num": 2,
        "type": "VALIDE",
        "question": "Quel est le delai de preavis pour un licenciement?",
        "expected_patterns": ["preavis", "jour", "licenciement"],
        "forbidden_patterns": [],
        "description": "Delai de preavis"
    },
    {
        "num": 3,
        "type": "VALIDE",
        "question": "Qu'est-ce qu'une convention collective?",
        "expected_patterns": ["convention", "collectif", "accord"],
        "forbidden_patterns": [],
        "description": "Convention collective"
    },
    {
        "num": 4,
        "type": "VALIDE",
        "question": "Comment sont calculees les heures supplementaires?",
        "expected_patterns": ["heure", "supplement", "majoration"],
        "forbidden_patterns": [],
        "description": "Calcul des heures supplementaires"
    },
    {
        "num": 5,
        "type": "VALIDE",
        "question": "Quelles sont les principales obligations de l'employeur?",
        "expected_patterns": ["employeur", "obligation"],
        "forbidden_patterns": [],
        "description": "Obligations de l'employeur"
    },
    {
        "num": 6,
        "type": "VALIDE",
        "question": "Qu'est-ce que le teletravail en Cote d'Ivoire?",
        "expected_patterns": ["travail"],
        "forbidden_patterns": [],
        "description": "Teletravail ou fallback"
    },
    {
        "num": 7,
        "type": "VALIDE",
        "question": "Quels sont les motifs de licenciement valide?",
        "expected_patterns": ["licenciement", "motif"],
        "forbidden_patterns": [],
        "description": "Motifs de licenciement"
    },
    {
        "num": 8,
        "type": "VALIDE",
        "question": "Comment fonctionne la suspension du contrat de travail?",
        "expected_patterns": ["suspension", "contrat", "travail"],
        "forbidden_patterns": [],
        "description": "Suspension du contrat"
    },
    {
        "num": 9,
        "type": "VALIDE",
        "question": "Quelles sont les indemnites de licenciement?",
        "expected_patterns": ["indemnite", "licenciement"],
        "forbidden_patterns": [],
        "description": "Indemnites de licenciement"
    },
    {
        "num": 10,
        "type": "VALIDE",
        "question": "Quels sont les droits syndicaux des travailleurs?",
        "expected_patterns": ["syndicat", "droit"],
        "forbidden_patterns": [],
        "description": "Droits syndicaux"
    },
    # QUESTIONS HORS-SUJET (5)
    {
        "num": 11,
        "type": "HORS-SUJET",
        "question": "Quel est le meilleur restaurant de Yamoussoukro?",
        "expected_patterns": ["aucune", "disposition", "travail"],
        "forbidden_patterns": ["pizza", "restaurant", "manger", "cuisine"],
        "description": "Question non-legale (restaurant)"
    },
    {
        "num": 12,
        "type": "HORS-SUJET",
        "question": "Comment programmer en Python efficacement?",
        "expected_patterns": ["aucune", "disposition", "travail"],
        "forbidden_patterns": ["def ", "python", "fonction", "algorithme"],
        "description": "Question technique (programmation)"
    },
    {
        "num": 13,
        "type": "HORS-SUJET",
        "question": "Quels conseils pour devenir riche?",
        "expected_patterns": ["aucune", "disposition", "travail"],
        "forbidden_patterns": ["investir", "bourse", "placement", "fortune"],
        "description": "Question personnelle (richesse)"
    },
    {
        "num": 14,
        "type": "HORS-SUJET",
        "question": "Qu'est-ce que la relativite generale?",
        "expected_patterns": ["aucune", "disposition", "travail"],
        "forbidden_patterns": ["einstein", "physique", "relativite", "energie"],
        "description": "Question scientifique (physique)"
    },
    {
        "num": 15,
        "type": "HORS-SUJET",
        "question": "Quel est le plus haut sommet d'Afrique?",
        "expected_patterns": ["aucune", "disposition", "travail"],
        "forbidden_patterns": ["kilimanjaro", "everest", "montagne", "sommet"],
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
        "passed": True,
        "hallucinations": [],
        "answer_preview": None,
        "sources_count": 0
    }

    try:
        result = ask_legal_bot(question, retriever, llm)
        answer = result["answer"]
        sources = result.get("sources", [])

        result_obj["sources_count"] = len(sources)
        answer_clean = remove_accents(answer.lower())

        # Preview
        result_obj["answer_preview"] = answer[:100]

        print("REPONSE ({} chars):\n{}\n".format(len(answer), answer[:150]))

        if sources:
            print("SOURCES ({}):\n".format(len(sources)))
            for i, src in enumerate(sources, 1):
                ref = src.get('source_ref', 'N/A')
                print("  {}. {}".format(i, ref[:50]))
        else:
            print("Aucune source utilisee\n")

        # VERIFICATIONS
        print("\nVERIFICATIONS:")

        # Vérification 1: Patterns obligatoires (avec normalisation des accents)
        print("\n1. Patterns OBLIGATOIRES:")
        for pattern in expected:
            pattern_clean = remove_accents(pattern)
            if pattern_clean in answer_clean:
                print("  OK - '{}'".format(pattern))
            else:
                print("  MANQUANT - '{}'".format(pattern))
                result_obj["passed"] = False
                result_obj["hallucinations"].append("Pattern attendu manquant: {}".format(pattern))

        # Vérification 2: Patterns INTERDITS (hallucinations)
        print("\n2. Patterns INTERDITS (Hallucinations):")
        for pattern in forbidden:
            pattern_clean = remove_accents(pattern.lower())
            if pattern_clean in answer_clean:
                print("  ALERTE - Hallucination: '{}'".format(pattern))
                result_obj["passed"] = False
                HALLUCINATION_COUNT += 1
                result_obj["hallucinations"].append("Hallucination: {}".format(pattern))
            else:
                print("  OK - Absent: '{}'".format(pattern))

        # Resultat
        if result_obj["passed"]:
            print("\nRESULTAT: OK (PASS)")
            if test_type == "VALIDE":
                VALID_TEST_COUNT += 1
            else:
                FALLBACK_TEST_COUNT += 1
        else:
            print("\nRESULTAT: ECHEC ({} problemes)".format(len(result_obj["hallucinations"])))

    except Exception as e:
        print("ERREUR: {}".format(str(e)))
        result_obj["error"] = str(e)
        result_obj["passed"] = False

    TEST_RESULTS.append(result_obj)
    time.sleep(3)  # Rate limiting (augmente de 2 a 3 secondes)

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

print("\nSTATISTIQUES:")
print("  - Total: {}".format(total_tests))
print("  - PASS: {} ({:.1f}%)".format(passed_tests, (passed_tests/total_tests)*100))
print("  - FAIL: {}".format(failed_tests))
print("  - Hallucinations: {}".format(HALLUCINATION_COUNT))

print("\nRESULTATS PAR TYPE:")
print("  - Questions valides: {}/10 PASS".format(VALID_TEST_COUNT))
print("  - Questions hors-sujet: {}/5 PASS".format(FALLBACK_TEST_COUNT))

print("\nOBJECTIF:")
if HALLUCINATION_COUNT == 0:
    print("  *** 0 HALLUCINATION DETECTEE (OBJECTIF ATTEINT!) ***")
else:
    print("  *** {} HALLUCINATION(S) DETECTEE(S) ***".format(HALLUCINATION_COUNT))

print("\nDETAILS:")
print("{:<4} {:<12} {:<6} {:<30}".format("Num", "Type", "Resultat", "Description"))
print("-" * 60)
for t in TEST_RESULTS:
    status = "PASS" if t["passed"] else "FAIL"
    print("{:<4} {:<12} {:<6} {:<30}".format(
        "{:02d}".format(t['test_num']),
        t['type'][:11],
        status,
        t['description'][:28]
    ))

# Sauvegarder resultats JSON
output_file = "test_15_final_results.json"
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

print("\nResultats: {}".format(output_file))

# Resume final
print("\n" + "="*90)
if HALLUCINATION_COUNT == 0:
    if passed_tests == total_tests:
        print("SUCCESS! 15/15 tests OK - 0 hallucination!")
    else:
        print("{}/15 OK - 0 hallucination (mais {} tests failed)".format(passed_tests, failed_tests))
else:
    print("ALERTE: {} hallucination(s)".format(HALLUCINATION_COUNT))
print("="*90 + "\n")
