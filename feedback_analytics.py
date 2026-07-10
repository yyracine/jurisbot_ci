"""
Analyseur de feedback pour JurisBot CI.
Traite et analyse les retours des testeurs beta.
"""

import json
from pathlib import Path
from datetime import datetime
from statistics import mean, stdev
from collections import defaultdict


class FeedbackAnalyzer:
    def __init__(self, feedback_file: str = "feedback_logs/detailed_feedback.jsonl"):
        self.feedback_file = Path(feedback_file)
        self.feedbacks = self._load_feedbacks()

    def _load_feedbacks(self) -> list:
        """Charge tous les feedbacks du fichier"""
        if not self.feedback_file.exists():
            return []

        feedbacks = []
        with open(self.feedback_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    feedbacks.append(json.loads(line))
        return feedbacks

    def get_statistics(self) -> dict:
        """Calcule les statistiques globales"""
        if not self.feedbacks:
            return {}

        detailed_ratings = [
            f["feedback_data"] for f in self.feedbacks
            if f.get("feedback_type") == "detailed" and f.get("feedback_data")
        ]

        if not detailed_ratings:
            return {"total_feedbacks": len(self.feedbacks), "detailed_ratings": 0}

        accuracy_scores = [r.get("accuracy", 0) for r in detailed_ratings]
        clarity_scores = [r.get("clarity", 0) for r in detailed_ratings]
        citation_scores = [r.get("citations", 0) for r in detailed_ratings]
        completeness_scores = [r.get("completeness", 0) for r in detailed_ratings]

        all_scores = accuracy_scores + clarity_scores + citation_scores + completeness_scores
        overall_avg = mean(all_scores) if all_scores else 0

        stats = {
            "total_feedbacks": len(self.feedbacks),
            "detailed_ratings": len(detailed_ratings),
            "accuracy": {
                "mean": mean(accuracy_scores) if accuracy_scores else 0,
                "stdev": stdev(accuracy_scores) if len(accuracy_scores) > 1 else 0,
            },
            "clarity": {
                "mean": mean(clarity_scores) if clarity_scores else 0,
                "stdev": stdev(clarity_scores) if len(clarity_scores) > 1 else 0,
            },
            "citations": {
                "mean": mean(citation_scores) if citation_scores else 0,
                "stdev": stdev(citation_scores) if len(citation_scores) > 1 else 0,
            },
            "completeness": {
                "mean": mean(completeness_scores) if completeness_scores else 0,
                "stdev": stdev(completeness_scores) if len(completeness_scores) > 1 else 0,
            },
            "overall_average": overall_avg,
            "rating_distribution": self._get_distribution(all_scores),
        }

        return stats

    def _get_distribution(self, scores: list) -> dict:
        """Compte la distribution des scores"""
        distribution = defaultdict(int)
        for score in scores:
            distribution[score] += 1
        return dict(distribution)

    def get_issues_summary(self) -> dict:
        """Extrait les problèmes identifiés par les testeurs"""
        issues = {
            "accuracy_issues": [],
            "clarity_issues": [],
            "citation_issues": [],
            "completeness_issues": [],
            "hallucinations": [],
            "other_comments": []
        }

        for fb in self.feedbacks:
            timestamp = fb.get("timestamp", "")
            data = fb.get("feedback_data", {})
            comments = data.get("comments", "").lower()

            # Catégoriser par score faible
            if data.get("accuracy", 5) <= 2 and comments:
                issues["accuracy_issues"].append({
                    "timestamp": timestamp,
                    "comment": data.get("comments", ""),
                    "score": data.get("accuracy")
                })

            if data.get("clarity", 5) <= 2 and comments:
                issues["clarity_issues"].append({
                    "timestamp": timestamp,
                    "comment": data.get("comments", ""),
                    "score": data.get("clarity")
                })

            if data.get("citations", 5) <= 2 and comments:
                issues["citation_issues"].append({
                    "timestamp": timestamp,
                    "comment": data.get("comments", ""),
                    "score": data.get("citations")
                })

            if data.get("completeness", 5) <= 2 and comments:
                issues["completeness_issues"].append({
                    "timestamp": timestamp,
                    "comment": data.get("comments", ""),
                    "score": data.get("completeness")
                })

            if fb.get("feedback_type") == "hallucination":
                issues["hallucinations"].append({
                    "timestamp": timestamp,
                    "comment": data.get("comments", "N/A")
                })

            if comments and any(kw in comments for kw in ["error", "wrong", "incorrect", "bug"]):
                if not any(issue in comments for issue in ["accuracy", "clarity", "citation", "completeness"]):
                    issues["other_comments"].append({
                        "timestamp": timestamp,
                        "comment": data.get("comments", "")
                    })

        return {k: v for k, v in issues.items() if v}

    def export_report(self, filename: str = "feedback_report.json"):
        """Exporte un rapport complet en JSON"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "statistics": self.get_statistics(),
            "issues_summary": self.get_issues_summary(),
            "all_feedbacks": self.feedbacks
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"✅ Rapport exporté: {filename}")
        return report

    def print_summary(self):
        """Affiche un résumé texte des feedbacks"""
        stats = self.get_statistics()
        issues = self.get_issues_summary()

        print("\n" + "=" * 60)
        print("📊 RAPPORT DE FEEDBACK - JurisBot CI")
        print("=" * 60)

        print(f"\n📈 Statistiques Globales:")
        print(f"  • Feedbacks reçus: {stats.get('total_feedbacks', 0)}")
        print(f"  • Évaluations détaillées: {stats.get('detailed_ratings', 0)}")
        print(f"  • Score global: {stats.get('overall_average', 0):.2f}/5")

        print(f"\n📌 Précision juridique: {stats.get('accuracy', {}).get('mean', 0):.2f}/5")
        print(f"💬 Clarté: {stats.get('clarity', {}).get('mean', 0):.2f}/5")
        print(f"📖 Citations: {stats.get('citations', {}).get('mean', 0):.2f}/5")
        print(f"✅ Complétude: {stats.get('completeness', {}).get('mean', 0):.2f}/5")

        if issues:
            print(f"\n🚨 Problèmes Identifiés:")
            if issues.get("accuracy_issues"):
                print(f"  • Précision: {len(issues['accuracy_issues'])} problèmes")
            if issues.get("clarity_issues"):
                print(f"  • Clarté: {len(issues['clarity_issues'])} problèmes")
            if issues.get("citation_issues"):
                print(f"  • Citations: {len(issues['citation_issues'])} problèmes")
            if issues.get("completeness_issues"):
                print(f"  • Complétude: {len(issues['completeness_issues'])} problèmes")
            if issues.get("hallucinations"):
                print(f"  • Hallucinations: {len(issues['hallucinations'])}")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    analyzer = FeedbackAnalyzer()
    analyzer.print_summary()
    analyzer.export_report()
