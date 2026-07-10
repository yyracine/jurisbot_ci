#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Force UTF-8 on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

print("=" * 70)
print("TEST SIMPLE - DIAGNOSTIQUE")
print("=" * 70)
print("Timestamp: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

# Check API key
api_key = os.getenv("MISTRAL_API_KEY")
if api_key:
    print("1. Clé API trouvée: {}...".format(api_key[:10]))
else:
    print("1. ERREUR: Clé API non trouvée")
    exit(1)

# Test import
print("\n2. Import des modules...")
try:
    from bot_juridique import init_rag_engine, ask_legal_bot
    print("   OK - Modules importés")
except Exception as e:
    print("   ERREUR: {}".format(e))
    exit(1)

# Initialize RAG
print("\n3. Initialisation du moteur RAG...")
start = time.time()
try:
    retriever, llm = init_rag_engine()
    elapsed = time.time() - start
    print("   OK - Moteur initialisé en {:.1f}s".format(elapsed))
except Exception as e:
    print("   ERREUR: {}".format(e))
    import traceback
    traceback.print_exc()
    exit(1)

# Test 1 question
print("\n4. Test d'une question...")
question = "Quels sont les droits des travailleurs en matiere de conges annuels?"
print("   Question: {}".format(question))

start = time.time()
try:
    result = ask_legal_bot(question, retriever, llm)
    elapsed = time.time() - start
    answer = result["answer"]
    sources = result.get("sources", [])

    print("   OK - Reponse en {:.1f}s".format(elapsed))
    print("\n   Reponse: {}".format(answer[:200]))
    print("\n   Sources: {}".format(len(sources)))
except Exception as e:
    print("   ERREUR: {}".format(e))
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 70)
print("DIAGNOSTIC OK - Moteur pret pour les tests")
print("=" * 70 + "\n")
