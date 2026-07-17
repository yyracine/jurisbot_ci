#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyse avancée des feedbacks - Insights détaillés et recommandations
"""

import json
from collections import defaultdict, Counter
from statistics import mean, stdev
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def load_analysis():
    """Charge le fichier d'analyse"""
    with open("feedback_analysis.json", "r", encoding="utf-8") as f:
        return json.load(f)

def analyze_score_distribution(feedbacks):
    """Analyse la distribution des scores"""
    print("\n" + "="*70)
    print("📊 DISTRIBUTION DES SCORES DÉTAILLÉE")
    print("="*70)

    detailed = [f for f in feedbacks if f.get("feedback_type") == "detailed"]

    if not detailed:
        print("❌ Pas de feedbacks détaillés")
        return

    criteria = ["accuracy", "clarity", "citations", "completeness"]

    for criterion in criteria:
        scores = [f.get(criterion) for f in detailed if f.get(criterion) is not None]

        if not scores:
            continue

        print(f"\n📌 {criterion.upper()}")
        print(f"   Min: {min(scores)} | Max: {max(scores)} | Moyenne: {mean(scores):.2f}")

        # Comptage
        counter = Counter(scores)
        for score in sorted(counter.keys()):
            count = counter[score]
            bar = "█" * score + "░" * (5 - score)
            pct = (count / len(scores)) * 100
            print(f"   {score}/5: {bar} ({count} = {pct:.0f}%)")

def analyze_low_scores(feedbacks):
    """Identifie les problèmes spécifiques"""
    print("\n" + "="*70)
    print("🔴 FEEDBACKS PROBLÉMATIQUES (≤3/5)")
    print("="*70)

    detailed = [f for f in feedbacks if f.get("feedback_type") == "detailed"]
    problems = []

    for f in detailed:
        if f.get("accuracy", 5) <= 3 or f.get("clarity", 5) <= 3:
            problems.append(f)

    if not problems:
        print("✅ Aucun problème détecté!")
        return

    print(f"\nTotal problématique: {len(problems)}")

    for i, f in enumerate(problems, 1):
        print(f"\n{i}. Question: {f.get('query', 'N/A')[:60]}")
        print(f"   Email: {f.get('email', 'anonymous')}")
        print(f"   Scores: Précision={f.get('accuracy')}/5 | Clarté={f.get('clarity')}/5")
        if f.get('comments'):
            print(f"   Commentaire: {f.get('comments')[:100]}")

def analyze_question_patterns(feedbacks):
    """Identifie les patterns de questions"""
    print("\n" + "="*70)
    print("🔍 PATTERNS DE QUESTIONS")
    print("="*70)

    # Compter les questions uniques
    questions = defaultdict(list)
    for f in feedbacks:
        q = f.get("query")
        if q:
            questions[q].append(f)

    # Top questions posées
    print(f"\nTotal questions uniques: {len(questions)}")

    if questions:
        # Trier par fréquence
        top_questions = sorted(questions.items(), key=lambda x: len(x[1]), reverse=True)

        print("\n🏆 Questions les plus posées:")
        for i, (q, feedbacks_list) in enumerate(top_questions[:5], 1):
            avg_score = 0
            detailed = [f for f in feedbacks_list if f.get("feedback_type") == "detailed"]
            if detailed:
                scores = [f.get("accuracy", 3) for f in detailed if f.get("accuracy")]
                avg_score = mean(scores) if scores else 0

            print(f"{i}. {q[:50]}...")
            print(f"   Posée {len(feedbacks_list)}x | Score moyen: {avg_score:.1f}/5")

def analyze_citation_issues(feedbacks):
    """Analyse les problèmes de citations"""
    print("\n" + "="*70)
    print("📖 ANALYSE DES CITATIONS")
    print("="*70)

    detailed = [f for f in feedbacks if f.get("feedback_type") == "detailed"]
    low_citation = [f for f in detailed if f.get("citations", 5) <= 3]

    print(f"\nFeedbacks avec citations ≤3/5: {len(low_citation)}/{len(detailed)}")

    if low_citation:
        print("\nProblèmes détectés:")
        for f in low_citation:
            print(f"  - {f.get('query', 'N/A')[:50]}")
            print(f"    Score: {f.get('citations')}/5")

def analyze_email_patterns(feedbacks):
    """Analyse les patterns par email"""
    print("\n" + "="*70)
    print("📧 ANALYSE PAR EMAIL")
    print("="*70)

    detailed = [f for f in feedbacks if f.get("feedback_type") == "detailed"]
    emails = defaultdict(list)

    for f in detailed:
        email = f.get("email", "anonymous")
        emails[email].append(f)

    print(f"\nUtilisateurs ayant donné du feedback: {len(emails)}")

    for email, user_feedbacks in sorted(emails.items(), key=lambda x: len(x[1]), reverse=True):
        scores = [f.get("accuracy", 3) for f in user_feedbacks if f.get("accuracy")]
        avg = mean(scores) if scores else 0
        count = len(user_feedbacks)

        print(f"\n📧 {email}")
        print(f"   Feedbacks: {count} | Score moyen: {avg:.1f}/5")

def generate_actionable_recommendations(feedbacks, stats):
    """Génère des recommandations actionnables"""
    print("\n" + "="*70)
    print("🎯 RECOMMANDATIONS ACTIONNABLES")
    print("="*70)

    detailed = [f for f in feedbacks if f.get("feedback_type") == "detailed"]

    recommendations = []

    # Vérifier citations
    if stats["citations"] < 4.5:
        recommendations.append({
            "priority": "P1",
            "issue": "Citations",
            "score": stats["citations"],
            "target": 4.5,
            "action": "Vérifier les sources et corriger les hallucinations de citations",
            "timeline": "1-2 jours",
            "effort": "Medium"
        })

    # Vérifier clarté
    low_clarity = [f for f in detailed if f.get("clarity", 5) <= 3]
    if low_clarity:
        recommendations.append({
            "priority": "P2",
            "issue": "Clarté",
            "score": stats["clarity"],
            "count": len(low_clarity),
            "action": "Simplifier les réponses, ajouter plus d'exemples concrets",
            "timeline": "2-3 jours",
            "effort": "Medium"
        })

    # Vérifier précision
    if stats["accuracy"] < 4.0:
        recommendations.append({
            "priority": "P2",
            "issue": "Précision",
            "score": stats["accuracy"],
            "action": "Enrichir la Knowledge Base avec plus de cas juridiques",
            "timeline": "3-5 jours",
            "effort": "High"
        })

    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. [{rec['priority']}] {rec['issue']}")
        print(f"   Score actuel: {rec.get('score', 'N/A'):.2f}")
        if "target" in rec:
            print(f"   Objectif: {rec['target']}")
        print(f"   Action: {rec['action']}")
        print(f"   Timeline: {rec['timeline']}")
        print(f"   Effort: {rec['effort']}")

def main():
    print("\n" + "="*70)
    print("🔬 ANALYSE AVANCÉE DES FEEDBACKS - JurisBot CI")
    print("="*70)

    data = load_analysis()
    feedbacks = data.get("feedbacks", [])
    stats = data.get("statistics", {})

    print(f"\n📊 Données générales:")
    print(f"   Total feedbacks: {data.get('total_feedbacks')}")
    print(f"   Hallucinations: {stats.get('hallucinations', 0)}")
    print(f"   Accuracy: {stats.get('accuracy', 0):.2f}/5")
    print(f"   Clarity: {stats.get('clarity', 0):.2f}/5")
    print(f"   Citations: {stats.get('citations', 0):.2f}/5")
    print(f"   Completeness: {stats.get('completeness', 0):.2f}/5")

    # Analyses
    analyze_score_distribution(feedbacks)
    analyze_low_scores(feedbacks)
    analyze_question_patterns(feedbacks)
    analyze_citation_issues(feedbacks)
    analyze_email_patterns(feedbacks)
    generate_actionable_recommendations(feedbacks, stats)

    print("\n" + "="*70)
    print("✅ Analyse complète terminée!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
