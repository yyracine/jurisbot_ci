#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test rapide des améliorations du fallback
Focus sur les 2 questions qui causaient des hallucinations
"""

import os
import sys
import time
from dotenv import load_dotenv

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from bot_juridique import init_rag_engine, ask_legal_bot

load_dotenv()

print("="*80)
print("TEST DE CORRECTION DES HALLUCINATIONS")
print("="*80)
print("\nInitialisation du moteur RAG...\n")

try:
    retriever, llm = init_rag_engine()
except Exception as e:
    print("ERREUR: {}".format(e))
    exit(1)

# Test les 2 questions problématiques
tests = [
    {
        "num": 12,
        "question": "Comment programmer en Python efficacement?",
        "expected_in_fallback": ["Aucune disposition", "droit du travail"],
        "forbidden_in_fallback": ["python", "code", "fonction"],
    },
    {
        "num": 13,
        "question": "Quels conseils pour devenir riche?",
        "expected_in_fallback": ["Aucune disposition", "droit du travail"],
        "forbidden_in_fallback": ["investir", "riche", "bourse"],
    },
]

print("\n" + "="*80)
print("TEST 1: Question Python (était hallucination avant)")
print("="*80 + "\n")

q1 = tests[0]["question"]
print("Question: {}".format(q1))
result1 = ask_legal_bot(q1, retriever, llm)
answer1 = result1["answer"]

print("\nReponse:\n{}".format(answer1))
print("\nAnalyse:")

# Verifier les patterns avec recherche plus strict (pas dans "Code du Travail")
forbidden1 = tests[0]["forbidden_in_fallback"]
hallucins1 = []

# Exceptions: termes legaux
answer1_clean = answer1.lower().replace("code du travail", "").replace("code de travail", "")

for pattern in forbidden1:
    if pattern.lower() in answer1_clean:
        print("  ALERTE - '{}' TROUVE".format(pattern))
        hallucins1.append(pattern)
    else:
        print("  OK - '{}' ABSENT".format(pattern))

# Verifier que le fallback est present
if "Aucune disposition" in answer1:
    print("  OK - Fallback correct applique")

print("\n" + "="*80)
print("TEST 2: Question Richesse (était hallucination avant)")
print("="*80 + "\n")

time.sleep(3)

q2 = tests[1]["question"]
print("Question: {}".format(q2))
result2 = ask_legal_bot(q2, retriever, llm)
answer2 = result2["answer"]

print("\nReponse:\n{}".format(answer2))
print("\nAnalyse:")

forbidden2 = tests[1]["forbidden_in_fallback"]
hallucins2 = []

# Exceptions: termes legaux
answer2_clean = answer2.lower().replace("code du travail", "").replace("code de travail", "")

for pattern in forbidden2:
    if pattern.lower() in answer2_clean:
        print("  ALERTE - '{}' TROUVE".format(pattern))
        hallucins2.append(pattern)
    else:
        print("  OK - '{}' ABSENT".format(pattern))

# Verifier que le fallback est present
if "Aucune disposition" in answer2:
    print("  OK - Fallback correct applique")

# Verdict final
print("\n" + "="*80)
print("VERDICT FINAL")
print("="*80)

if not hallucins1 and not hallucins2:
    print("\n✓ SUCCESS! Les 2 hallucinations ont ete eliminées!")
    print("  - Test 12 (Python): OK")
    print("  - Test 13 (Richesse): OK")
else:
    print("\n✗ Des hallucinations restent detectees:")
    if hallucins1:
        print("  - Test 12: {}".format(hallucins1))
    if hallucins2:
        print("  - Test 13: {}".format(hallucins2))

print("\n" + "="*80 + "\n")
