import re
from typing import Dict, Tuple, List
from datetime import datetime

class HallucinationDetector:
    """Détecteur avancé de hallucinations dans les réponses RAG"""

    def __init__(self):
        # Références VALIDES du code du travail ivoirien
        self.valid_decrees = {
            "96-203": "Décret n° 96-203 du 7 mars 1996",
            "2014-370": "Décret n° 2014-370 du 18 juin 2014",
            "2015-532": "Loi n° 2015-532 du 20 juillet 2015",
        }

        self.valid_articles = {
            "article 2": "Article 2 - Définition du travailleur",
            "article 24": "Article 24 - Heures supplémentaires",
            "article 51": "Article 51 - Convention Collective",
        }

        # Patterns de hallucinations CONNUES
        self.hallucination_patterns = [
            # Dates fictives
            (r"Décret n° \d+-\d+ du \d+ juillet \d{4}", "date_suspect"),
            (r"Loi du \d+ juillet \d{4}", "loi_sans_numero"),
            (r"Article \d{3,4}(?! du)", "article_fictif"),  # Articles à 3+ chiffres

            # Pourcentages inventés (pas citables)
            (r"(\d{2,3})%\s+(?:de)?(?:majoration|augmentation|salaire)", "pourcentage_invente"),

            # Références incomplètes
            (r"Décret\s+(?!n°)", "reference_incomplete"),
            (r"Article \d+ de la Loi", "mauvaise_reference"),  # Loi pas bonne pour certains sujets

            # Affirmations non sourcées
            (r"(?:Le|La|Les)\s+(?:contrat|employeur|syndicat).*(?:doit|peut|doit)\s+", "affirmation_non_source"),
        ]

    def detect_hallucinations(self, answer: str, sources: List[Dict]) -> Dict:
        """
        Détecte les hallucinations potentielles dans une réponse.

        Args:
            answer: La réponse du bot
            sources: Les sources utilisées pour générer la réponse

        Returns:
            Dict avec:
            - hallucination_score: 0.0-1.0 (0 = pas de hallucination, 1 = certain)
            - issues: Liste des problèmes détectés
            - is_hallucinating: True si hallucination probable
        """
        issues = []
        score = 0.0

        # 1. Vérifier les citations
        citation_issues = self._check_citations(answer)
        issues.extend(citation_issues["issues"])
        score += citation_issues["score"]

        # 2. Chercher les patterns de hallucinations
        pattern_issues = self._check_patterns(answer)
        issues.extend(pattern_issues["issues"])
        score += pattern_issues["score"]

        # 3. Vérifier la cohérence avec les sources
        source_issues = self._check_source_consistency(answer, sources)
        issues.extend(source_issues["issues"])
        score += source_issues["score"]

        # 4. Vérifier les nombres et chiffres
        number_issues = self._check_numbers(answer)
        issues.extend(number_issues["issues"])
        score += number_issues["score"]

        # Normaliser le score entre 0 et 1
        hallucination_score = min(score / 4.0, 1.0)

        return {
            "hallucination_score": round(hallucination_score, 2),
            "is_hallucinating": hallucination_score > 0.5,
            "confidence": "high" if hallucination_score > 0.7 else "medium" if hallucination_score > 0.3 else "low",
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        }

    def _check_citations(self, answer: str) -> Dict:
        """Vérifie la validité des citations"""
        issues = []
        score = 0.0

        # Vérifier que chaque citation existe
        for decree_num, decree_full in self.valid_decrees.items():
            if decree_num in answer:
                # Bonne référence trouvée
                pass

        # Chercher des références invalides
        invalid_patterns = [
            (r"Décret n° \d+-\d+(?!\d)", "Référence Décret incomplète"),
            (r"Article \d{4,}", "Numéro d'article trop grand (fictif)"),
            (r"Loi n° \d{10,}", "Numéro de Loi trop long"),
        ]

        for pattern, message in invalid_patterns:
            matches = re.findall(pattern, answer)
            if matches:
                issues.append(f"❌ Citation suspecte : {message} - {matches[0]}")
                score += 0.3

        # Vérifier les citations obligatoires
        has_citation = any(ref in answer for ref in self.valid_decrees.values())
        if not has_citation and len(answer) > 100:
            issues.append("⚠️ Pas de citation valide trouvée (peut être acceptable pour fallback)")
            score += 0.1

        return {"issues": issues, "score": score}

    def _check_patterns(self, answer: str) -> Dict:
        """Cherche les patterns de hallucinations connus"""
        issues = []
        score = 0.0

        for pattern, pattern_type in self.hallucination_patterns:
            matches = re.finditer(pattern, answer, re.IGNORECASE)
            for match in matches:
                issues.append(f"⚠️ Pattern {pattern_type} détecté : '{match.group()}'")
                score += 0.15

        return {"issues": issues, "score": score}

    def _check_source_consistency(self, answer: str, sources: List[Dict]) -> Dict:
        """Vérifie la cohérence avec les sources"""
        issues = []
        score = 0.0

        if not sources:
            issues.append("⚠️ Pas de sources fournies (réponse potentiellement hallucination)")
            score += 0.3
            return {"issues": issues, "score": score}

        # Extraire les références mentionnées dans la réponse
        mentioned_refs = set()
        for ref_key, ref_full in self.valid_decrees.items():
            if ref_key in answer or ref_full in answer:
                mentioned_refs.add(ref_full)

        # Vérifier que les références mentionnées sont dans les sources
        source_refs = {src.get("source_ref", "") for src in sources}

        for ref in mentioned_refs:
            found = any(ref in src_ref for src_ref in source_refs)
            if not found:
                issues.append(f"⚠️ Référence '{ref}' mentionnée mais pas dans les sources")
                score += 0.2

        return {"issues": issues, "score": score}

    def _check_numbers(self, answer: str) -> Dict:
        """Vérifie la validité des nombres et taux"""
        issues = []
        score = 0.0

        # Chercher les pourcentages
        percentages = re.findall(r"(\d+(?:[.,]\d+)?)\s*%", answer)

        # Pourcentages valides (exemples pour heures supp: 25%, 50%, 100%)
        valid_percentages = {"25", "50", "100", "75", "33", "40", "60", "80", "10", "15", "20", "30"}

        for pct in percentages:
            pct_clean = pct.replace(",", ".").split(".")[0]
            if pct_clean not in valid_percentages and int(pct_clean) > 100:
                issues.append(f"❌ Pourcentage suspect : {pct}%")
                score += 0.25

        # Chercher les délais
        delays = re.findall(r"(\d+)\s*(?:jour|mois|an)s?(?:\s+de|\s+avant|\s+après)?", answer)
        if delays:
            for delay in delays:
                try:
                    days = int(delay)
                    if days > 365 or days < 0:
                        issues.append(f"⚠️ Délai suspect : {delay} jours")
                        score += 0.1
                except:
                    pass

        return {"issues": issues, "score": score}

    def format_report(self, detection_results: Dict) -> str:
        """Formate le rapport de détection en texte lisible"""
        score = detection_results["hallucination_score"]
        confidence = detection_results["confidence"]
        is_hallucinating = detection_results["is_hallucinating"]

        report = f"""
╔═══════════════════════════════════════════════════════════════╗
║          🔍 RAPPORT DE DÉTECTION D'HALLUCINATIONS             ║
╚═══════════════════════════════════════════════════════════════╝

🎯 SCORE D'HALLUCINATION : {score:.0%}
📊 CONFIANCE : {confidence.upper()}
{'🚨 HALLUCINATION PROBABLE' if is_hallucinating else '✅ PROBABLEMENT VALIDE'}

📋 PROBLÈMES DÉTECTÉS ({len(detection_results['issues'])}):
{chr(10).join('  • ' + issue for issue in detection_results['issues']) if detection_results['issues'] else '  ✅ Aucun problème détecté'}

⏰ Timestamp : {detection_results['timestamp']}
═══════════════════════════════════════════════════════════════
"""
        return report
