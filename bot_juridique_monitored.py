"""
Version améliorée de bot_juridique.py avec monitoring et détection de hallucinations.
Intègre le système de monitoring et feedback pour la production.
"""

import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from bot_juridique import init_rag_engine, ask_legal_bot, verify_and_correct_citations
from monitoring import get_monitor
from hallucination_detector import HallucinationDetector

# Initialiser les services
load_dotenv()
monitor = get_monitor()
detector = HallucinationDetector()


def ask_legal_bot_monitored(query: str, retriever, llm) -> dict:
    """
    Wrapper de ask_legal_bot avec monitoring et détection de hallucinations.

    Args:
        query: La question de l'utilisateur
        retriever: Le retriever FAISS
        llm: Le modèle Mistral

    Returns:
        dict avec:
        - answer: La réponse
        - sources: Les sources
        - detection: Résultats de détection des hallucinations
        - response_id: ID unique pour le feedback
    """
    print(f"\n{'='*70}")
    print(f"❓ QUESTION : {query}")
    print(f"{'='*70}\n")

    # 1. Obtenir la réponse du bot
    response = ask_legal_bot(query, retriever, llm)

    answer = response["answer"]
    sources = response["sources"]

    # 2. Analyser les hallucinations
    print("\n🔍 Analyse des hallucinations en cours...")
    detection_results = detector.detect_hallucinations(answer, sources)

    # 3. Afficher le rapport de détection
    report = detector.format_report(detection_results)
    print(report)

    # 4. Enregistrer dans le monitoring
    response_id = monitor.log_response(
        query=query,
        answer=answer,
        sources=sources,
        detection_results=detection_results,
        metadata={
            "model": "mistral-large-latest",
            "retriever": "FAISS",
            "embedding_model": "mistral-embed"
        }
    )

    print(f"📊 Response ID pour feedback : {response_id}")

    # 5. Alerte si hallucination probable
    if detection_results["is_hallucinating"]:
        print(f"\n⚠️ ALERTE : Hallucination probable détectée (score: {detection_results['hallucination_score']:.0%})")
        monitor.create_alert(
            response_id=response_id,
            hallucination_description=f"Score: {detection_results['hallucination_score']:.0%} - {', '.join(detection_results['issues'][:2])}"
        )

    print(f"\n{'='*70}\n")

    return {
        "answer": answer,
        "sources": sources,
        "detection": detection_results,
        "response_id": response_id
    }


def print_user_feedback_instructions(response_id: str):
    """Affiche les instructions pour soumettre un feedback"""
    print(f"""
╔═════════════════════════════════════════════════════════════╗
║            📝 SOUMETTRE UN FEEDBACK                         ║
╚═════════════════════════════════════════════════════════════╝

Si vous trouvez une ERREUR ou une HALLUCINATION dans la réponse,
envoyez un feedback via cURL ou Postman :

📤 Endpoint (thumbs_down) :
curl -X POST http://localhost:8001/feedback/submit \\
  -H "Content-Type: application/json" \\
  -d '{{
    "response_id": "{response_id}",
    "feedback": "thumbs_down",
    "is_hallucination": true,
    "details": "Description du problème trouvé"
  }}'

✅ Endpoint (thumbs_up) :
curl -X POST http://localhost:8001/feedback/submit \\
  -H "Content-Type: application/json" \\
  -d '{{
    "response_id": "{response_id}",
    "feedback": "thumbs_up",
    "is_hallucination": false,
    "details": "Réponse correcte et bien citée"
  }}'

📊 Voir les statistiques:
curl http://localhost:8001/stats

═════════════════════════════════════════════════════════════
""")


# ==========================================
# EXEMPLE D'UTILISATION
# ==========================================

if __name__ == "__main__":
    print("🚀 Initialisation du bot juridique avec monitoring...")
    retriever, llm = init_rag_engine()

    # Questions de test
    test_queries = [
        "Quel est le taux des heures supplémentaires?",
        "Combien de jours de préavis avant résiliation?",
        "Quels sont les congés payés minimum?",
    ]

    print("\n" + "="*70)
    print("🧪 MODE TEST - MONITORING ACTIVÉ")
    print("="*70)

    for query in test_queries:
        result = ask_legal_bot_monitored(query, retriever, llm)

        # Afficher les instructions de feedback
        print_user_feedback_instructions(result["response_id"])

        # Pause pour rate limit
        import time
        time.sleep(3)

    # Afficher les statistiques finales
    print("\n" + "="*70)
    print("📊 STATISTIQUES FINALES")
    print("="*70)
    monitor.print_summary()

    # Exporter le rapport
    print("\n📄 Export du rapport...")
    monitor.export_report("monitoring_final_report.json")
