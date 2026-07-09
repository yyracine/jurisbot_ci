import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

sys.stdout.reconfigure(encoding='utf-8')

class HallucinationMonitor:
    """Système de monitoring des hallucinations en production"""

    def __init__(self, log_dir: str = "hallucination_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.session_log = self.log_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        self.alerts_log = self.log_dir / "alerts.jsonl"
        self.feedback_log = self.log_dir / "feedback.jsonl"

    def log_response(self, query: str, answer: str, sources: List[Dict],
                    detection_results: Dict = None, metadata: Dict = None) -> str:
        """
        Enregistre une réponse du système avec méta-données de détection.
        Retourne l'ID unique de la réponse.
        """
        response_id = f"resp_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        log_entry = {
            "id": response_id,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "answer": answer[:500],  # Garder les 500 premiers chars
            "sources": sources,
            "detection": detection_results or {},
            "metadata": metadata or {}
        }

        # Enregistrer dans le session log
        with open(self.session_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        return response_id

    def log_user_feedback(self, response_id: str, feedback: str,
                         is_hallucination: bool = False, details: str = ""):
        """
        Enregistre le feedback utilisateur (bonne/mauvaise réponse).
        """
        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "response_id": response_id,
            "feedback": feedback,  # "thumbs_up" | "thumbs_down"
            "is_hallucination": is_hallucination,
            "details": details
        }

        with open(self.feedback_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(feedback_entry, ensure_ascii=False) + "\n")

        # Si hallucination détectée, créer une alerte
        if is_hallucination:
            self.create_alert(response_id, details)

    def create_alert(self, response_id: str, hallucination_description: str):
        """Crée une alerte pour hallucination détectée"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "severity": "HIGH",
            "type": "HALLUCINATION_DETECTED",
            "response_id": response_id,
            "description": hallucination_description
        }

        with open(self.alerts_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(alert, ensure_ascii=False) + "\n")

        print(f"🚨 ALERTE HALLUCINATION : {hallucination_description}")

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de monitoring"""
        stats = {
            "total_responses": 0,
            "total_feedback": 0,
            "hallucinations_detected": 0,
            "hallucinations_by_score": 0,
            "hallucination_rate": 0.0,
            "average_hallucination_score": 0.0,
            "alerts": [],
            "responses_by_score": []
        }

        # Compter les réponses et calculer le score d'hallucination
        if self.session_log.exists():
            with open(self.session_log, "r", encoding="utf-8") as f:
                responses = [json.loads(line) for line in f]
                stats["total_responses"] = len(responses)

                # Calculer le score moyen d'hallucination et compter les réponses avec hallucination détectée
                hallucination_scores = []
                auto_hallucinations = 0
                for resp in responses:
                    detection = resp.get("detection", {})
                    if detection.get("is_hallucinating"):
                        auto_hallucinations += 1
                    score = detection.get("hallucination_score", 0.0)
                    hallucination_scores.append(score)

                stats["hallucinations_by_score"] = auto_hallucinations
                if hallucination_scores:
                    stats["average_hallucination_score"] = sum(hallucination_scores) / len(hallucination_scores)
                    # Taux d'hallucination basé sur score >= 0.5
                    stats["hallucination_rate"] = (sum(1 for s in hallucination_scores if s >= 0.5) / len(hallucination_scores)) * 100

                stats["responses_by_score"] = hallucination_scores

        # Compter les feedbacks utilisateur
        feedbacks = 0
        user_hallucinations = 0
        if self.feedback_log.exists():
            with open(self.feedback_log, "r", encoding="utf-8") as f:
                for line in f:
                    entry = json.loads(line)
                    feedbacks += 1
                    if entry.get("is_hallucination"):
                        user_hallucinations += 1

        stats["total_feedback"] = feedbacks
        stats["hallucinations_detected"] = user_hallucinations  # Feedback utilisateur

        # Lister les dernières alertes
        if self.alerts_log.exists():
            with open(self.alerts_log, "r", encoding="utf-8") as f:
                alerts = [json.loads(line) for line in f]
                stats["alerts"] = alerts[-10:]  # Dernières 10 alertes

        return stats

    def export_report(self, output_file: str = "monitoring_report.json"):
        """Exporte un rapport complet de monitoring"""
        stats = self.get_stats()
        report = {
            "generated_at": datetime.now().isoformat(),
            "statistics": stats,
            "log_directory": str(self.log_dir),
            "files": {
                "session_log": str(self.session_log),
                "feedback_log": str(self.feedback_log),
                "alerts_log": str(self.alerts_log)
            }
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"📊 Rapport exporté : {output_file}")
        return report

    def print_summary(self):
        """Affiche un résumé des statistiques"""
        stats = self.get_stats()
        print("\n" + "="*60)
        print("📊 STATISTIQUES DE MONITORING")
        print("="*60)
        print(f"Total réponses : {stats['total_responses']}")
        print(f"Total feedbacks : {stats['total_feedback']}")
        print(f"Hallucinations détectées : {stats['hallucinations_detected']}")
        print(f"Taux d'hallucination : {stats['false_positive_rate']:.2f}%")
        print("="*60 + "\n")


# Singleton global
_monitor = None

def get_monitor(log_dir: str = "hallucination_logs") -> HallucinationMonitor:
    """Retourne l'instance globale du monitor"""
    global _monitor
    if _monitor is None:
        _monitor = HallucinationMonitor(log_dir)
    return _monitor
