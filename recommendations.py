"""
Système de recommandations - JurisBot CI
Propose des actions concrètes pour améliorer l'application basées sur les données
"""

import json
from typing import Dict, List, Any
from analysis import FeedbackAnalyzer

class RecommendationEngine:
    def __init__(self):
        self.analyzer = FeedbackAnalyzer()

    def get_quick_wins(self) -> List[Dict[str, Any]]:
        """Identifie les améliorations rapides et faciles"""
        quick_wins = []

        problems = self.analyzer.get_problem_areas()

        for problem in problems:
            if problem["area"] == "Précision juridique":
                quick_wins.append({
                    "priority": "P1",
                    "effort": "Medium",
                    "estimated_time": "4-6 heures",
                    "title": "Améliorer les sources RAG",
                    "description": "La précision juridique est faible",
                    "actions": [
                        "1. Relire code_du_travail_ci.md pour erreurs",
                        "2. Vérifier les chunks extraits (5-10 exemples)",
                        "3. Améliorer la stratégie de splitting (plus petit chunks?)",
                        "4. Tester avec 5 questions de précision"
                    ],
                    "expected_impact": "↑ Précision de 3.2 → 4.2/5",
                    "success_metric": "Feedback accuracy ≥ 4.0"
                })

            elif problem["area"] == "Hallucinations détectées":
                quick_wins.append({
                    "priority": "P0",
                    "effort": "High",
                    "estimated_time": "8-12 heures",
                    "title": "Renforcer le contrôle anti-hallucinations",
                    "description": "Trop de hallucinations détectées",
                    "actions": [
                        "1. Analyser les 10 réponses avec plus haut score",
                        "2. Vérifier si c'est un faux positif du détecteur",
                        "3. Ajouter prompt d'instruction 'STRICT MODE'",
                        "4. Tester le modèle mistral avec temperature=0.1",
                        "5. Valider avec 20 questions"
                    ],
                    "expected_impact": "↓ Hallucinations de {rate}% → <5%",
                    "success_metric": "hallucination_rate < 5%"
                })

            elif problem["area"] == "Qualité des citations":
                quick_wins.append({
                    "priority": "P1",
                    "effort": "Medium",
                    "estimated_time": "2-3 heures",
                    "title": "Améliorer le matching article → réponse",
                    "description": "Les citations ne correspondent pas aux réponses",
                    "actions": [
                        "1. Examiner 5 feedbacks négatifs sur citations",
                        "2. Vérifier bot_juridique.py verify_and_correct_citations()",
                        "3. Ajouter log pour déboguer matching",
                        "4. Améliorer la regex de citation"
                    ],
                    "expected_impact": "↑ Score citations de 3.2 → 4.5/5",
                    "success_metric": "avg_citations ≥ 4.0"
                })

            elif problem["area"] == "Clarté de la réponse":
                quick_wins.append({
                    "priority": "P2",
                    "effort": "Low",
                    "estimated_time": "1-2 heures",
                    "title": "Reformuler les prompts pour pédagogie",
                    "description": "Les testeurs ne comprennent pas les réponses",
                    "actions": [
                        "1. Relire prompt en français dans bot_juridique.py",
                        "2. Ajouter instruction: 'Explique simplement'",
                        "3. Tester avec jargon technique minimal",
                        "4. Faire tester par 3 personnes non-juristes"
                    ],
                    "expected_impact": "↑ Clarté de 3.2 → 4.3/5",
                    "success_metric": "avg_clarity ≥ 4.0"
                })

            elif problem["area"] == "Complétude des réponses":
                quick_wins.append({
                    "priority": "P2",
                    "effort": "Low",
                    "estimated_time": "30 minutes",
                    "title": "Augmenter le nombre de chunks retrieved",
                    "description": "Les réponses ne sont pas complètes",
                    "actions": [
                        "1. Vérifier k=3 dans bot_juridique.py",
                        "2. Essayer k=5 ou k=7",
                        "3. Benchmarker le temps de réponse",
                        "4. Valider la qualité avec les testeurs"
                    ],
                    "expected_impact": "↑ Complétude de 3.2 → 4.2/5",
                    "success_metric": "avg_completeness ≥ 4.0"
                })

        return quick_wins

    def get_medium_term_improvements(self) -> List[Dict[str, Any]]:
        """Recommande des améliorations à moyen terme (1-2 semaines)"""
        improvements = [
            {
                "priority": "P1",
                "effort": "High",
                "timeline": "3-5 jours",
                "title": "Dashboard de monitoring avancé",
                "description": "Créer un tableau de bord pour suivre les KPIs en temps réel",
                "actions": [
                    "1. Créer une nouvelle page Streamlit 'Monitoring'",
                    "2. Afficher en temps réel: hallucinations, feedback scores",
                    "3. Graphiques: tendance accuracy, satisfaction over time",
                    "4. Alertes automatiques pour anomalies"
                ],
                "expected_impact": "Meilleure visibilité sur la qualité",
                "tools_needed": ["Streamlit", "Plotly", "SQLite"]
            },
            {
                "priority": "P2",
                "effort": "Medium",
                "timeline": "2-3 jours",
                "title": "Fine-tuning du modèle Mistral",
                "description": "Adapter Mistral spécifiquement au droit ivoirien",
                "actions": [
                    "1. Collecter 50+ pairs (question, bonne_réponse)",
                    "2. Formater pour fine-tuning Mistral",
                    "3. Entraîner sur 1-2 exemples",
                    "4. Comparer accuracy avant/après"
                ],
                "expected_impact": "Amélioration générale des réponses",
                "tools_needed": ["Mistral API fine-tuning", "Python"]
            },
            {
                "priority": "P2",
                "effort": "Medium",
                "timeline": "2-3 jours",
                "title": "Enrichissement de la knowledge base",
                "description": "Ajouter des documents légaux supplémentaires",
                "actions": [
                    "1. Identifier les topics manquants (from feedback)",
                    "2. Trouver/créer documents légaux pour ces topics",
                    "3. Intégrer dans code_du_travail_ci.md",
                    "4. Re-créer l'index FAISS",
                    "5. Re-tester le système"
                ],
                "expected_impact": "Couverture de plus de cas d'usage",
                "tools_needed": ["Markdown", "FAISS", "Python"]
            }
        ]

        return improvements

    def get_long_term_strategy(self) -> List[Dict[str, Any]]:
        """Stratégie long terme (1-3 mois)"""
        strategy = [
            {
                "phase": "Phase 2: Production Ready",
                "timeline": "2-3 semaines",
                "description": "Préparer le système pour des utilisateurs payants",
                "initiatives": [
                    "Migrer vers Supabase pgvector pour scalabilité",
                    "Ajouter authentification des utilisateurs",
                    "Implémenter rate limiting et usage tracking",
                    "Créer système de facturation (Paystack)",
                    "Ajouter analytics pour chaque utilisateur"
                ]
            },
            {
                "phase": "Phase 3: Advanced Features",
                "timeline": "1 mois",
                "description": "Ajouter des capacités avancées",
                "initiatives": [
                    "Chat conversationnel (memory entre questions)",
                    "Génération de contrats basée sur les réponses",
                    "Export PDF des réponses avec citations",
                    "Système de notifications pour mises à jour légales",
                    "API publique pour intégration tiers"
                ]
            },
            {
                "phase": "Phase 4: Scaling",
                "timeline": "2-3 mois",
                "description": "Scaler pour 1000+ utilisateurs",
                "initiatives": [
                    "Multi-langue (Français, Anglais, Bambara)",
                    "Cache Redis pour performances",
                    "CDN pour documents statiques",
                    "Load balancing pour API",
                    "Monitoring/alerting avec Grafana"
                ]
            }
        ]

        return strategy

    def get_personalized_roadmap(self) -> Dict[str, Any]:
        """Crée une roadmap personnalisée basée sur l'état actuel"""
        satisfaction = self.analyzer.get_user_satisfaction()
        problems = self.analyzer.get_problem_areas()

        if not problems:
            priority_focus = "Polishing & Production"
        elif any(p["severity"] == "CRITICAL" for p in problems):
            priority_focus = "Fix Critical Issues"
        elif satisfaction["satisfaction_score"] < 3.5:
            priority_focus = "Improve Core Quality"
        else:
            priority_focus = "Quick Wins & Polish"

        return {
            "current_state": {
                "satisfaction_score": satisfaction["satisfaction_score"],
                "total_responses": self.analyzer.response_stats.get("total_responses", 0),
                "hallucination_rate": self.analyzer.response_stats.get("hallucination_rate", 0)
            },
            "priority_focus": priority_focus,
            "quick_wins": self.get_quick_wins(),
            "medium_term": self.get_medium_term_improvements(),
            "long_term": self.get_long_term_strategy()
        }

    def export_recommendations(self, filepath: str = None) -> str:
        """Exporte les recommandations en JSON"""
        roadmap = self.get_personalized_roadmap()

        if not filepath:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"jurisbot_recommendations_{timestamp}.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(roadmap, f, ensure_ascii=False, indent=2)

        return filepath

if __name__ == "__main__":
    engine = RecommendationEngine()
    roadmap = engine.get_personalized_roadmap()
    print(json.dumps(roadmap, ensure_ascii=False, indent=2))
