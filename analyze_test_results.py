#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyse des resultats des 15 tests anti-hallucinations
"""

import json
import os
from datetime import datetime

def analyze_results():
    """Analyse les resultats JSON et genere un rapport"""

    results_file = "test_15_questions_results.json"

    if not os.path.exists(results_file):
        print("Fichier de resultats non trouve: {}".format(results_file))
        return

    with open(results_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("\n" + "="*80)
    print("RAPPORT D'ANALYSE - 15 QUESTIONS TEST")
    print("="*80)

    print("\nINFORMATIONS GENERALES:")
    print("  - Timestamp: {}".format(data.get("timestamp", "N/A")))
    print("  - Total tests: {}".format(data.get("total_tests", 0)))
    print("  - Tests reussis: {}".format(data.get("passed_tests", 0)))
    print("  - Tests echoues: {}".format(data.get("failed_tests", 0)))
    print("  - Taux reussite: {:.1f}%".format(data.get("success_rate", 0)))
    print("  - Hallucinations: {}".format(data.get("hallucination_count", 0)))
    print("  - Objectif atteint: {}".format(
        "OUI (0 hallucination)" if data.get("objective_achieved") else "NON"
    ))

    print("\nRESULTATS PAR CATEGORIE:")
    print("  - Questions valides reussies: {}/10".format(data.get("valid_tests_passed", 0)))
    print("  - Questions hors-sujet reussies: {}/5".format(data.get("fallback_tests_passed", 0)))

    print("\nDETAILS DES TESTS:")
    print("\n{:<4} {:<12} {:<7} {:<30} {:<10}".format("Num", "Type", "Resultat", "Description", "Hallucins"))
    print("-" * 70)

    for result in data.get("results", []):
        status = "PASS" if result.get("passed") else "FAIL"
        halluc_count = len(result.get("hallucinations", []))
        print("{:<4} {:<12} {:<7} {:<30} {:<10}".format(
            "{:02d}".format(result.get("test_num", 0)),
            result.get("type", "N/A")[:11],
            status,
            result.get("description", "N/A")[:28],
            str(halluc_count)
        ))

    # Hallucinations details
    print("\n" + "="*80)
    print("HALLUCINATIONS DETECTEES:")
    print("="*80)

    halluc_found = False
    for result in data.get("results", []):
        if result.get("hallucinations"):
            halluc_found = True
            print("\nTest {}: {}".format(result.get("test_num"), result.get("question")))
            for halluc in result.get("hallucinations", []):
                print("  - {}".format(halluc))

    if not halluc_found:
        print("\n✓ AUCUNE HALLUCINATION DETECTEE!")

    # Conclusions
    print("\n" + "="*80)
    print("CONCLUSIONS:")
    print("="*80)

    success_rate = data.get("success_rate", 0)
    halluc_count = data.get("hallucination_count", 0)

    if halluc_count == 0:
        print("\n✓ OBJECTIF ATTEINT: 0 hallucination dans les 15 questions!")
    else:
        print("\n✗ {} hallucination(s) detectee(s)".format(halluc_count))

    if success_rate >= 90:
        print("✓ Taux de reussite excellent: {:.1f}%".format(success_rate))
    elif success_rate >= 75:
        print("✓ Taux de reussite bon: {:.1f}%".format(success_rate))
    else:
        print("✗ Taux de reussite faible: {:.1f}%".format(success_rate))

    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    analyze_results()
