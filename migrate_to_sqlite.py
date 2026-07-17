#!/usr/bin/env python3
"""
Script de migration des données JSON vers SQLite
Exécutez ce script une fois pour migrer vos données existantes
"""

import json
from pathlib import Path
from db import init_db, add_response, add_feedback, add_alert
import sys
sys.stdout.reconfigure(encoding='utf-8')

def migrate_from_json():
    """Migre les données JSON existantes vers SQLite"""
    print("🔄 Démarrage de la migration JSON → SQLite...\n")

    init_db()
    print("✅ Base de données initialisée\n")

    # Migrer les responses depuis les logs de monitoring
    responses_migrated = 0
    responses_log = Path("hallucination_logs/responses.jsonl")

    if responses_log.exists():
        print(f"📄 Migration des réponses depuis {responses_log}...")
        try:
            with open(responses_log, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            add_response(
                                response_id=data.get("response_id", ""),
                                query=data.get("query", ""),
                                answer=data.get("answer", ""),
                                sources=data.get("sources", []),
                                hallucination_score=data.get("detection_results", {}).get("hallucination_score", 0.0),
                                is_hallucinating=data.get("detection_results", {}).get("is_hallucinating", False),
                                model=data.get("metadata", {}).get("model", "mistral-large-latest"),
                                retriever=data.get("metadata", {}).get("retriever", "FAISS"),
                                embedding_model=data.get("metadata", {}).get("embedding_model", "mistral-embed")
                            )
                            responses_migrated += 1
                        except json.JSONDecodeError:
                            continue
            print(f"   ✅ {responses_migrated} réponses migrées\n")
        except Exception as e:
            print(f"   ❌ Erreur: {e}\n")

    # Migrer les feedbacks
    feedbacks_migrated = 0
    feedbacks_log = Path("hallucination_logs/feedback.jsonl")

    if feedbacks_log.exists():
        print(f"📄 Migration des feedbacks depuis {feedbacks_log}...")
        try:
            with open(feedbacks_log, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            add_feedback(
                                response_id=data.get("response_id", ""),
                                feedback_type="quick",
                                feedback=data.get("feedback", ""),
                                is_hallucination=data.get("is_hallucination", False)
                            )
                            feedbacks_migrated += 1
                        except json.JSONDecodeError:
                            continue
            print(f"   ✅ {feedbacks_migrated} feedbacks migrés\n")
        except Exception as e:
            print(f"   ❌ Erreur: {e}\n")

    # Migrer les feedbacks détaillés
    detailed_feedbacks_migrated = 0
    detailed_feedbacks_log = Path("feedback_logs/detailed_feedback.jsonl")

    if detailed_feedbacks_log.exists():
        print(f"📄 Migration des feedbacks détaillés depuis {detailed_feedbacks_log}...")
        try:
            with open(detailed_feedbacks_log, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            feedback_data = data.get("feedback_data", {})
                            add_feedback(
                                response_id=data.get("response_id", ""),
                                feedback_type="detailed",
                                accuracy=feedback_data.get("accuracy"),
                                clarity=feedback_data.get("clarity"),
                                citations=feedback_data.get("citations"),
                                completeness=feedback_data.get("completeness"),
                                comments=feedback_data.get("comments"),
                                email=feedback_data.get("email", "anonymous")
                            )
                            detailed_feedbacks_migrated += 1
                        except json.JSONDecodeError:
                            continue
            print(f"   ✅ {detailed_feedbacks_migrated} feedbacks détaillés migrés\n")
        except Exception as e:
            print(f"   ❌ Erreur: {e}\n")

    # Migrer les alertes
    alerts_migrated = 0
    alerts_log = Path("hallucination_logs/alerts.jsonl")

    if alerts_log.exists():
        print(f"📄 Migration des alertes depuis {alerts_log}...")
        try:
            with open(alerts_log, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            add_alert(
                                response_id=data.get("response_id", ""),
                                hallucination_description=data.get("hallucination_description", "")
                            )
                            alerts_migrated += 1
                        except json.JSONDecodeError:
                            continue
            print(f"   ✅ {alerts_migrated} alertes migrées\n")
        except Exception as e:
            print(f"   ❌ Erreur: {e}\n")

    # Résumé
    print("=" * 60)
    print("📊 RÉSUMÉ DE LA MIGRATION")
    print("=" * 60)
    print(f"✅ Réponses:           {responses_migrated}")
    print(f"✅ Feedbacks:          {feedbacks_migrated}")
    print(f"✅ Feedbacks détaillés: {detailed_feedbacks_migrated}")
    print(f"✅ Alertes:            {alerts_migrated}")
    print("=" * 60)
    print(f"\n✅ Migration terminée!")
    print(f"📁 Fichier BD: jurisbot_ci.db")
    print(f"\n💡 Vous pouvez maintenant supprimer les fichiers JSON si vous le souhaitez:")
    print(f"   - hallucination_logs/")
    print(f"   - feedback_logs/")

if __name__ == "__main__":
    migrate_from_json()
