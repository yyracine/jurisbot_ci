#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'analyse des feedbacks pour identifier les patterns d'amélioration
Utilise les données SQLite pour générer des insights actionnables
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import sqlite3
from collections import defaultdict
from datetime import datetime
import json

DB_PATH = "jurisbot_ci.db"

class FeedbackAnalyzer:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def get_all_feedbacks(self):
        """Récupère tous les feedbacks avec contexte"""
        self.cursor.execute("""
            SELECT f.*, r.query, r.answer
            FROM feedbacks f
            LEFT JOIN responses r ON f.response_id = r.id
            ORDER BY f.created_at DESC
        """)
        return [dict(row) for row in self.cursor.fetchall()]

    def analyze_hallucinations(self):
        """Identifie les hallucinations récurrentes"""
        self.cursor.execute("""
            SELECT r.query, r.answer, COUNT(*) as count
            FROM responses r
            WHERE r.hallucination_score > 0.5
            GROUP BY r.query
            ORDER BY count DESC
            LIMIT 10
        """)

        results = [dict(row) for row in self.cursor.fetchall()]

        print("\n🚨 HALLUCINATIONS RÉCURRENTES:\n")
        if not results:
            print("✅ Aucune hallucination détectée!")
            return results

        for i, item in enumerate(results, 1):
            print(f"{i}. Question: {item['query'][:50]}...")
            print(f"   Occurrences: {item['count']}")
            print(f"   Score: {item.get('hallucination_score', 'N/A')}")
            print()

        return results

    def analyze_accuracy_issues(self):
        """Identifie les problèmes de précision"""
        self.cursor.execute("""
            SELECT
                accuracy,
                COUNT(*) as count,
                AVG(CAST(accuracy AS FLOAT)) as avg_score
            FROM feedbacks
            WHERE feedback_type = 'detailed'
            GROUP BY accuracy
            ORDER BY accuracy
        """)

        results = [dict(row) for row in self.cursor.fetchall()]

        print("\n📌 DISTRIBUTION PRÉCISION:\n")
        for row in results:
            accuracy = row['accuracy']
            count = row['count']
            avg = row['avg_score']
            bar = "█" * accuracy + "░" * (5 - accuracy)
            print(f"⭐ {bar} ({accuracy}/5): {count} feedbacks")

        # Identifier les basses notes
        self.cursor.execute("""
            SELECT
                f.comments,
                f.accuracy,
                r.query,
                r.answer
            FROM feedbacks f
            LEFT JOIN responses r ON f.response_id = r.id
            WHERE f.accuracy <= 2 AND f.feedback_type = 'detailed'
            ORDER BY f.created_at DESC
        """)

        low_scores = [dict(row) for row in self.cursor.fetchall()]

        if low_scores:
            print("\n⚠️ FEEDBACK CRITIQUE (≤2/5):\n")
            for item in low_scores:
                print(f"Question: {item['query']}")
                print(f"Score: {item['accuracy']}/5")
                print(f"Commentaire: {item['comments']}")
                print("---\n")

        return results, low_scores

    def analyze_clarity_issues(self):
        """Identifie les problèmes de clarté"""
        self.cursor.execute("""
            SELECT
                clarity,
                COUNT(*) as count,
                AVG(CAST(clarity AS FLOAT)) as avg_score
            FROM feedbacks
            WHERE feedback_type = 'detailed'
            GROUP BY clarity
            ORDER BY clarity
        """)

        results = [dict(row) for row in self.cursor.fetchall()]

        print("\n💬 DISTRIBUTION CLARTÉ:\n")
        for row in results:
            clarity = row['clarity']
            count = row['count']
            bar = "█" * clarity + "░" * (5 - clarity)
            print(f"⭐ {bar} ({clarity}/5): {count} feedbacks")

        # Identifier les basses notes
        self.cursor.execute("""
            SELECT
                f.comments,
                f.clarity,
                r.query
            FROM feedbacks f
            LEFT JOIN responses r ON f.response_id = r.id
            WHERE f.clarity <= 2 AND f.feedback_type = 'detailed'
            ORDER BY f.created_at DESC
        """)

        low_scores = [dict(row) for row in self.cursor.fetchall()]

        if low_scores:
            print("\n⚠️ CLARTÉ PROBLÉMATIQUE (≤2/5):\n")
            for item in low_scores:
                print(f"Question: {item['query']}")
                print(f"Score: {item['clarity']}/5")
                print(f"Commentaire: {item['comments']}")
                print("---\n")

        return results, low_scores

    def analyze_citations(self):
        """Analyse la qualité des citations"""
        self.cursor.execute("""
            SELECT
                citations,
                COUNT(*) as count,
                AVG(CAST(citations AS FLOAT)) as avg_score
            FROM feedbacks
            WHERE feedback_type = 'detailed'
            GROUP BY citations
            ORDER BY citations
        """)

        results = [dict(row) for row in self.cursor.fetchall()]

        print("\n📖 DISTRIBUTION CITATIONS:\n")
        for row in results:
            citations = row['citations']
            count = row['count']
            bar = "█" * citations + "░" * (5 - citations)
            print(f"⭐ {bar} ({citations}/5): {count} feedbacks")

        # Identifier les basses notes
        self.cursor.execute("""
            SELECT
                f.comments,
                f.citations,
                r.answer
            FROM feedbacks f
            LEFT JOIN responses r ON f.response_id = r.id
            WHERE f.citations <= 2 AND f.feedback_type = 'detailed'
            ORDER BY f.created_at DESC
        """)

        low_scores = [dict(row) for row in self.cursor.fetchall()]

        if low_scores:
            print("\n⚠️ CITATIONS PROBLÉMATIQUES (≤2/5):\n")
            for item in low_scores:
                print(f"Score: {item['citations']}/5")
                if item['comments']:
                    print(f"Commentaire: {item['comments']}")
                print("---\n")

        return results, low_scores

    def get_monthly_trends(self):
        """Analyse les tendances par mois"""
        self.cursor.execute("""
            SELECT
                strftime('%Y-%m', f.created_at) as month,
                COUNT(*) as total_feedbacks,
                AVG(CAST(
                    CASE f.feedback_type
                    WHEN 'detailed' THEN (accuracy + clarity + citations + completeness) / 4.0
                    ELSE 3.0
                    END AS FLOAT)) as avg_satisfaction,
                SUM(CASE WHEN f.is_hallucination = 1 THEN 1 ELSE 0 END) as hallucinations_count
            FROM feedbacks f
            GROUP BY month
            ORDER BY month DESC
        """)

        results = [dict(row) for row in self.cursor.fetchall()]

        print("\n📅 TENDANCES MENSUELLES:\n")
        for row in results:
            month = row['month']
            total = row['total_feedbacks']
            avg_sat = row['avg_satisfaction'] or 0
            halluc = row['hallucinations_count'] or 0
            bar = "█" * int(avg_sat) + "░" * (5 - int(avg_sat))
            print(f"{month}: {total} feedbacks | Satisfaction: {bar} ({avg_sat:.1f}/5) | Hallucinations: {halluc}")

        return results

    def generate_recommendations(self):
        """Génère des recommandations basées sur les analyses"""
        print("\n🎯 RECOMMANDATIONS D'AMÉLIORATION:\n")

        # Problèmes de précision
        self.cursor.execute("SELECT AVG(CAST(accuracy AS FLOAT)) FROM feedbacks WHERE feedback_type = 'detailed'")
        avg_accuracy = self.cursor.fetchone()[0] or 0

        if avg_accuracy < 4.0:
            print("1. 📌 PRÉCISION JURIDIQUE")
            print(f"   Moyenne: {avg_accuracy:.1f}/5 (Objectif: 4.5/5)")
            print("   Action: Enrichir la KB avec plus de cas juridiques")
            print("   Timeline: 1-2 semaines\n")

        # Problèmes de clarté
        self.cursor.execute("SELECT AVG(CAST(clarity AS FLOAT)) FROM feedbacks WHERE feedback_type = 'detailed'")
        avg_clarity = self.cursor.fetchone()[0] or 0

        if avg_clarity < 4.0:
            print("2. 💬 CLARTÉ DES RÉPONSES")
            print(f"   Moyenne: {avg_clarity:.1f}/5 (Objectif: 4.0/5)")
            print("   Action: Ajouter des exemples et simplifier le langage")
            print("   Timeline: 3-5 jours\n")

        # Hallucinations
        self.cursor.execute("SELECT COUNT(*) FROM responses WHERE hallucination_score > 0.5")
        halluc_count = self.cursor.fetchone()[0] or 0

        if halluc_count > 0:
            print("3. 🚨 HALLUCINATIONS DÉTECTÉES")
            print(f"   Nombre: {halluc_count}")
            print("   Action: Améliorer le prompt et ajouter de corrections")
            print("   Timeline: Même jour (P0)\n")

        # Problèmes de citations
        self.cursor.execute("SELECT AVG(CAST(citations AS FLOAT)) FROM feedbacks WHERE feedback_type = 'detailed'")
        avg_citations = self.cursor.fetchone()[0] or 0

        if avg_citations < 4.5:
            print("4. 📖 QUALITÉ DES CITATIONS")
            print(f"   Moyenne: {avg_citations:.1f}/5 (Objectif: 4.5/5)")
            print("   Action: Vérifier les sources et corriger les hallucinations de citations")
            print("   Timeline: 1-2 jours\n")

    def export_analysis(self, filename="feedback_analysis.json"):
        """Exporte l'analyse complète en JSON"""
        feedbacks = self.get_all_feedbacks()

        # Calculer les statistiques
        self.cursor.execute("SELECT COUNT(*) FROM feedbacks")
        total_feedbacks = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT AVG(CAST(accuracy AS FLOAT)) FROM feedbacks WHERE feedback_type = 'detailed'")
        avg_accuracy = self.cursor.fetchone()[0] or 0

        self.cursor.execute("SELECT AVG(CAST(clarity AS FLOAT)) FROM feedbacks WHERE feedback_type = 'detailed'")
        avg_clarity = self.cursor.fetchone()[0] or 0

        self.cursor.execute("SELECT AVG(CAST(citations AS FLOAT)) FROM feedbacks WHERE feedback_type = 'detailed'")
        avg_citations = self.cursor.fetchone()[0] or 0

        self.cursor.execute("SELECT AVG(CAST(completeness AS FLOAT)) FROM feedbacks WHERE feedback_type = 'detailed'")
        avg_completeness = self.cursor.fetchone()[0] or 0

        self.cursor.execute("SELECT COUNT(*) FROM responses WHERE hallucination_score > 0.5")
        hallucinations = self.cursor.fetchone()[0] or 0

        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_feedbacks": total_feedbacks,
            "statistics": {
                "accuracy": round(avg_accuracy, 2),
                "clarity": round(avg_clarity, 2),
                "citations": round(avg_citations, 2),
                "completeness": round(avg_completeness, 2),
                "hallucinations": hallucinations
            },
            "feedbacks": feedbacks
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Analyse exportée: {filename}")
        return analysis

    def close(self):
        """Ferme la connexion DB"""
        self.conn.close()

def main():
    analyzer = FeedbackAnalyzer()

    print("\n" + "="*60)
    print("📊 ANALYSE COMPLÈTE DES FEEDBACKS - JurisBot CI")
    print("="*60)

    # Analyses
    analyzer.analyze_hallucinations()
    analyzer.analyze_accuracy_issues()
    analyzer.analyze_clarity_issues()
    analyzer.analyze_citations()
    analyzer.get_monthly_trends()
    analyzer.generate_recommendations()

    # Exporter
    analyzer.export_analysis()

    analyzer.close()

    print("\n✅ Analyse complète terminée!")

if __name__ == "__main__":
    main()
