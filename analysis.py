"""
Module d'analyse des feedbacks et performances - JurisBot CI
Analyse les données collectées pour identifier les problèmes et opportunités
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from db import get_all_responses, get_all_feedbacks, get_feedback_stats, get_stats

class FeedbackAnalyzer:
    def __init__(self):
        self.responses = get_all_responses()
        self.feedbacks = get_all_feedbacks()
        self.response_stats = get_stats()
        self.feedback_stats = get_feedback_stats()

    def get_problem_areas(self) -> List[Dict[str, Any]]:
        """Identifie les zones problématiques basées sur les feedbacks"""
        problems = []

        # Problème 1: Précision faible
        avg_accuracy = self.feedback_stats.get("avg_accuracy", 5)
        if avg_accuracy and avg_accuracy < 3.5:
            problems.append({
                "severity": "HIGH",
                "area": "Précision juridique",
                "score": avg_accuracy,
                "description": "Les testeurs signalent une précision juridique faible",
                "impact": f"Score moyen: {avg_accuracy:.1f}/5",
                "recommendation": "Vérifier les sources RAG et la qualité des chunks"
            })

        # Problème 2: Hallucinations élevées
        hallucination_rate = self.response_stats.get("hallucination_rate", 0)
        if hallucination_rate > 10:
            problems.append({
                "severity": "CRITICAL",
                "area": "Hallucinations détectées",
                "score": hallucination_rate,
                "description": f"{hallucination_rate:.1f}% des réponses contiennent des hallucinations",
                "impact": f"Taux hallucination: {hallucination_rate:.1f}%",
                "recommendation": "Revoir le post-processing et améliorer le détecteur"
            })

        # Problème 3: Citations manquantes
        avg_citations = self.feedback_stats.get("avg_citations", 5)
        if avg_citations and avg_citations < 3.5:
            problems.append({
                "severity": "HIGH",
                "area": "Qualité des citations",
                "score": avg_citations,
                "description": "Les citations ne sont pas suffisamment précises",
                "impact": f"Score moyen: {avg_citations:.1f}/5",
                "recommendation": "Améliorer le matching article → réponse"
            })

        # Problème 4: Clarté insuffisante
        avg_clarity = self.feedback_stats.get("avg_clarity", 5)
        if avg_clarity and avg_clarity < 3.5:
            problems.append({
                "severity": "MEDIUM",
                "area": "Clarté de la réponse",
                "score": avg_clarity,
                "description": "Les réponses ne sont pas suffisamment claires",
                "impact": f"Score moyen: {avg_clarity:.1f}/5",
                "recommendation": "Reformuler les prompts pour plus de pédagogie"
            })

        # Problème 5: Complétude
        avg_completeness = self.feedback_stats.get("avg_completeness", 5)
        if avg_completeness and avg_completeness < 3.5:
            problems.append({
                "severity": "MEDIUM",
                "area": "Complétude des réponses",
                "score": avg_completeness,
                "description": "Les réponses ne couvrent pas entièrement la question",
                "impact": f"Score moyen: {avg_completeness:.1f}/5",
                "recommendation": "Augmenter le nombre de chunks retrieved"
            })

        return sorted(problems, key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}.get(x["severity"], 3))

    def get_strengths(self) -> List[Dict[str, Any]]:
        """Identifie les forces du système"""
        strengths = []

        # Force 1: Peu de hallucinations
        hallucination_rate = self.response_stats.get("hallucination_rate", 0)
        if hallucination_rate < 5:
            strengths.append({
                "area": "Contrôle des hallucinations",
                "score": 100 - hallucination_rate,
                "description": f"Seulement {hallucination_rate:.1f}% d'hallucinations détectées",
                "value": "Système RAG bien calibré"
            })

        # Force 2: Bonne précision
        avg_accuracy = self.feedback_stats.get("avg_accuracy", 0)
        if avg_accuracy and avg_accuracy >= 4:
            strengths.append({
                "area": "Précision juridique",
                "score": avg_accuracy,
                "description": f"Score moyen: {avg_accuracy:.1f}/5",
                "value": "Réponses juridiquement exactes"
            })

        # Force 3: Citations de qualité
        avg_citations = self.feedback_stats.get("avg_citations", 0)
        if avg_citations and avg_citations >= 4:
            strengths.append({
                "area": "Qualité des citations",
                "score": avg_citations,
                "description": f"Score moyen: {avg_citations:.1f}/5",
                "value": "Sources correctes et traçables"
            })

        return strengths

    def get_trending_questions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Récupère les questions les plus fréquentes"""
        question_counts = {}

        for response in self.responses:
            query = response.get("query", "").lower().strip()
            if query:
                question_counts[query] = question_counts.get(query, 0) + 1

        # Trier et retourner top N
        sorted_questions = sorted(question_counts.items(), key=lambda x: x[1], reverse=True)
        return [
            {"question": q, "frequency": count}
            for q, count in sorted_questions[:limit]
        ]

    def get_user_satisfaction(self) -> Dict[str, Any]:
        """Calcule le score de satisfaction globale"""
        if not self.feedback_stats:
            return {"satisfaction_score": 0, "interpretation": "Pas de données"}

        metrics = [
            self.feedback_stats.get("avg_accuracy", 0),
            self.feedback_stats.get("avg_clarity", 0),
            self.feedback_stats.get("avg_citations", 0),
            self.feedback_stats.get("avg_completeness", 0)
        ]

        valid_metrics = [m for m in metrics if m > 0]
        satisfaction_score = sum(valid_metrics) / len(valid_metrics) if valid_metrics else 0

        if satisfaction_score >= 4.5:
            interpretation = "⭐ Excellent"
        elif satisfaction_score >= 4.0:
            interpretation = "👍 Bon"
        elif satisfaction_score >= 3.0:
            interpretation = "😐 Acceptable"
        else:
            interpretation = "👎 À améliorer"

        return {
            "satisfaction_score": satisfaction_score,
            "interpretation": interpretation,
            "total_feedbacks": self.feedback_stats.get("total_feedbacks", 0),
            "detailed_feedbacks": self.feedback_stats.get("detailed_feedbacks", 0)
        }

    def get_hallucination_analysis(self) -> Dict[str, Any]:
        """Analyse détaillée des hallucinations"""
        hallucinating_responses = [r for r in self.responses if r.get("is_hallucinating")]

        if not hallucinating_responses:
            return {
                "total_hallucinations": 0,
                "hallucination_rate": 0,
                "most_problematic": [],
                "recommendation": "✅ Aucune hallucination détectée!"
            }

        # Trier par score hallucination
        hallucinating_responses.sort(
            key=lambda x: x.get("hallucination_score", 0),
            reverse=True
        )

        most_problematic = [
            {
                "query": r.get("query"),
                "answer": r.get("answer")[:100] + "...",
                "score": r.get("hallucination_score"),
                "timestamp": r.get("created_at")
            }
            for r in hallucinating_responses[:5]
        ]

        return {
            "total_hallucinations": len(hallucinating_responses),
            "hallucination_rate": (len(hallucinating_responses) / len(self.responses) * 100) if self.responses else 0,
            "most_problematic": most_problematic,
            "recommendation": "Revoir les réponses avec score > 0.7"
        }

    def generate_summary_report(self) -> Dict[str, Any]:
        """Génère un rapport résumé complet"""
        return {
            "timestamp": datetime.now().isoformat(),
            "total_responses": len(self.responses),
            "total_feedbacks": len(self.feedbacks),
            "satisfaction": self.get_user_satisfaction(),
            "problem_areas": self.get_problem_areas(),
            "strengths": self.get_strengths(),
            "hallucination_analysis": self.get_hallucination_analysis(),
            "trending_questions": self.get_trending_questions(5),
            "statistics": {
                "hallucination_rate": self.response_stats.get("hallucination_rate", 0),
                "average_hallucination_score": self.response_stats.get("average_hallucination_score", 0),
                "avg_accuracy": self.feedback_stats.get("avg_accuracy", 0),
                "avg_clarity": self.feedback_stats.get("avg_clarity", 0),
                "avg_citations": self.feedback_stats.get("avg_citations", 0),
                "avg_completeness": self.feedback_stats.get("avg_completeness", 0)
            }
        }

    def export_report_json(self, filepath: str = None) -> str:
        """Exporte le rapport en JSON"""
        report = self.generate_summary_report()

        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"jurisbot_analysis_report_{timestamp}.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return filepath

if __name__ == "__main__":
    analyzer = FeedbackAnalyzer()
    report = analyzer.generate_summary_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
