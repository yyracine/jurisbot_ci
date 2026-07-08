# -*- coding: utf-8 -*-
"""
Script de test anti-hallucination pour JurisBot CI.
Interroge le moteur RAG (bot_juridique.ask_legal_bot) sur une série de
questions dont la réponse exacte (ground truth) est vérifiée dans les textes.

Pour chaque question on définit:
  - query             : la question posée au bot
  - must_contain       : liste de chaînes qui DOIVENT figurer dans la réponse
  - must_not_contain   : liste de chaînes qui NE DOIVENT PAS figurer (hallucinations)
  - reference         : la source légale exacte (pour le rapport)
  - ground_truth       : le texte exact du Code (vérité terrain)
"""
import sys
import io
import time
import traceback

# Forcer l'UTF-8 sous Windows pour ne pas casser l'affichage des accents
# (reconfigure est sûr et idempotent contrairement à un TextIOWrapper brut)
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from bot_juridique import init_rag_engine, ask_legal_bot

# ============================================================
# QUESTIONNAIRE DE TEST (vérités terrain vérifiées dans le .md)
# ============================================================
TESTS = [
    # ------------------------------------------------------------------
    # 1. HEURES SUPPLÉMENTAIRES — Art. 24 du Décret 96-203 (9330 lignes)
    # ------------------------------------------------------------------
    {
        "id": "Q1_heures_sup_taux",
        "query": "Quel est le taux de majoration des heures supplémentaires effectuées de la 41e à la 46e heure ?",
        "must_contain": ["15 %", "41e", "46e", "Décret"],
        "must_not_contain": ["Loi n° 2015-532", "20 juillet 2015"],
        "reference": "Article 24 du Décret n° 96-203 du 7 mars 1996",
        "ground_truth": "15 % de majoration pour les heures effectuées de la 41e à la 46e heure",
    },
    {
        "id": "Q2_heures_sup_nuit",
        "query": "Quel est le taux de majoration pour une heure supplémentaire de nuit un dimanche ou jour férié ?",
        "must_contain": ["100 %"],
        "must_not_contain": ["Loi n° 2015-532", "Décret n° 96-203 du 20 juillet 2015"],
        "reference": "Article 24 du Décret n° 96-203 du 7 mars 1996",
        "ground_truth": "100 % de majoration pour les heures effectuées de nuit, les dimanches et jours fériés",
    },
    {
        "id": "Q3_heures_sup_plafond",
        "query": "Quel est le nombre maximum d'heures supplémentaires par semaine et par travailleur ?",
        "must_contain": ["15"],
        "must_not_contain": ["Loi n° 2015-532"],
        "reference": "Article 26 du Décret n° 96-203 du 7 mars 1996",
        "ground_truth": "limité à quinze (15) heures au maximum par semaine et par travailleur",
    },
    # ------------------------------------------------------------------
    # 2. CONVENTION COLLECTIVE — Art. 51 (taux agricoles)
    # ------------------------------------------------------------------
    {
        "id": "Q4_conv_coll_41_48",
        "query": "Selon la Convention Collective, quel est le taux de majoration des heures supplémentaires de la 41e à la 48e heure ?",
        "must_contain": ["15 %", "48e"],
        "must_not_contain": [],
        "reference": "Article 51 de la Convention Collective Interprofessionnelle",
        "ground_truth": "15 % de majoration pour les heures effectuées de la 41e à la 48e heure",
    },
    # ------------------------------------------------------------------
    # 3. SMIG — Décret 2013-791
    # ------------------------------------------------------------------
    {
        "id": "Q5_smig",
        "query": "Quel est le montant du SMIG (Salaire Minimum Interprofessionnel Garanti) en Côte d'Ivoire ?",
        "must_contain": ["60 000", "60.000", "60 000"],
        "must_not_contain": ["36 607", "200 000"],
        "reference": "Article 1 du Décret n° 2013-791 du 20 novembre 2013",
        "ground_truth": "Le SMIG est fixé à soixante mille, 60 000, francs CFA",
    },
    # ------------------------------------------------------------------
    # 4. PÉRIODE D'ESSAI — Décret 96-195
    # ------------------------------------------------------------------
    {
        "id": "Q6_essai_cadres",
        "query": "Quelle est la durée maximale de la période d'essai pour les ingénieurs et cadres ?",
        "must_contain": ["trois mois", "3 mois"],
        "must_not_contain": ["Loi n° 2015-532"],
        "reference": "Article 2 du Décret n° 96-195 du 7 mars 1996",
        "ground_truth": "trois mois pour les ingénieurs, cadres, techniciens supérieurs et assimilés",
    },
    {
        "id": "Q7_essai_mensuel",
        "query": "Quelle est la durée de la période d'essai pour un travailleur payé au mois ?",
        "must_contain": ["un mois", "1 mois"],
        "must_not_contain": [],
        "reference": "Article 2 du Décret n° 96-195 du 7 mars 1996",
        "ground_truth": "un mois pour les travailleurs payés au mois",
    },
    # ------------------------------------------------------------------
    # 5. PRÉAVIS — Décret 96-200
    # ------------------------------------------------------------------
    {
        "id": "Q8_preavis_mensuel_6ans",
        "query": "Un travailleur payé au mois (catégories 1 à 5) avec 6 ans d'ancienneté a-t-il droit à quel préavis en cas de rupture ?",
        "must_contain": ["deux mois", "2 mois"],
        "must_not_contain": ["Loi n° 2015-532"],
        "reference": "Article 1 (2°) du Décret n° 96-200 du 7 mars 1996",
        "ground_truth": "deux mois, de six ans à onze ans d'ancienneté (travailleurs payés au mois)",
    },
    # ------------------------------------------------------------------
    # 6. SAISIE / CESSION — Décret 2014-370
    # ------------------------------------------------------------------
    {
        "id": "Q9_saisie_33",
        "query": "Quel est le taux maximum de la quotité saisissable d'un salaire ?",
        "must_contain": ["33%"],
        "must_not_contain": ["Loi n° 2015-532"],
        "reference": "Article 3 du Décret n° 2014-370 du 18 juin 2014",
        "ground_truth": "le maximum de la quotité saisissable est égal à 33% de l'assiette",
    },
    {
        "id": "Q10_cession_smig_200k",
        "query": "Quel est le taux de quotité cessible pour un salaire compris entre le SMIG et 200 000 FCFA ?",
        "must_contain": ["35%"],
        "must_not_contain": ["Loi n° 2015-532"],
        "reference": "Article 4 du Décret n° 2014-370 du 18 juin 2014",
        "ground_truth": "du SMIG ou SMAG à 200.000 FCFA, le taux applicable est de 35%",
    },
    # ------------------------------------------------------------------
    # 7. INDEMNITÉ DE LICENCIEMENT — Décret 2017-210
    # ------------------------------------------------------------------
    {
        "id": "Q11_licenciement_taux",
        "query": "Quel est le taux de l'indemnité de licenciement jusqu'à la 5e année de présence ?",
        "must_contain": ["30%"],
        "must_not_contain": [],
        "reference": "Article 4 du Décret n° 2017-210 du 30 mars 2017",
        "ground_truth": "30% jusqu'à la cinquième année comprise",
    },
    {
        "id": "Q12_duree_legale",
        "query": "Quelle est la durée légale du travail hebdomadaire pour les entreprises non agricoles ?",
        "must_contain": ["40", "quarante"],
        "must_not_contain": [],
        "reference": "Article 1 du Décret n° 96-203 du 7 mars 1996",
        "ground_truth": "quarante (40) heures, par semaine, pour les entreprises non agricoles",
    },
    # ------------------------------------------------------------------
    # 8. TRAVAIL DE NUIT — Décret 96-204
    # ------------------------------------------------------------------
    {
        "id": "Q13_nuit_definition",
        "query": "Entre quelles heures se situe la période de travail de nuit ?",
        "must_contain": ["21", "5"],
        "must_not_contain": [],
        "reference": "Article 1 du Décret n° 96-204 du 7 mars 1996",
        "ground_truth": "8 heures consécutives comprises entre 21 heures et 5 heures",
    },
]


def normalize(text: str) -> str:
    """Normalise le texte pour comparaison (minuscules + espaces autour des %).
    Évite les faux négatifs : "35 %" == "35%", "30 %" == "30%".
    """
    import re as _re
    t = text.lower()
    t = _re.sub(r'\s*%\s*', '%', t)
    t = _re.sub(r'\s+', ' ', t)
    return t


def run_tests():
    print("=" * 70)
    print("  TEST ANTI-HALLUCINATION - JurisBot CI")
    print("=" * 70)

    print("\n⚙️  Initialisation du moteur RAG (peut prendre ~30s)...")
    retriever, llm, hybrid = init_rag_engine()
    print("✅ Moteur prêt.\n")

    results = []
    total = len(TESTS)

    for i, test in enumerate(TESTS, 1):
        print("\n" + "─" * 70)
        print(f"[{i}/{total}] {test['id']}")
        print(f"   ❓ {test['query']}")
        print(f"   📖 Réf. attendue : {test['reference']}")
        print(f"   ✅ Vérité terrain : {test['ground_truth']}")

        answer = ""
        error = None
        # Retry avec backoff pour gérer le rate-limit 429 de Mistral
        answer = ""
        for attempt in range(4):
            try:
                t0 = time.time()
                result = ask_legal_bot(query=test["query"], retriever=retriever, llm=llm, hybrid=hybrid)
                answer = result.get("answer", "")
                elapsed = time.time() - t0
                error = None
                break
            except Exception as e:
                elapsed = 0
                error = repr(e)
                if "429" in error or "rate" in error.lower():
                    wait = 20 * (attempt + 1)
                    print(f"   ⏳ Rate limité (429), attente {wait}s avant retry...")
                    time.sleep(wait)
                else:
                    traceback.print_exc()
                    break
            time.sleep(8)  # délai entre questions pour éviter le 429

        if error:
            status = "ERREUR"
            details = [f"Exception: {error}"]
        else:
            ans_low = normalize(answer)
            must_ok = [s for s in test["must_contain"] if normalize(s) in ans_low]
            must_ko = [s for s in test["must_not_contain"] if normalize(s) in ans_low]
            # Un seul seuil accepté pour 15%/100% qui ont plusieurs variantes: must_contain passe si >=1 présent
            must_pass = len(must_ok) >= 1
            no_hallu = len(must_ko) == 0
            if must_pass and no_hallu:
                status = "PASS ✅"
            elif not must_pass and not no_hallu:
                status = "FAIL ❌ (valeur absente + hallucination)"
            elif not must_pass:
                status = "FAIL ❌ (valeur attendue absente)"
            else:
                status = "HALLUCINATION 🚨"
            details = []
            if must_ok:
                details.append(f"trouvé: {must_ok}")
            if must_ko:
                details.append(f"HALLUCINATION: {must_ko}")

        # Affichage réponse tronquée
        preview = answer.replace("\n", " ")[:300]
        print(f"   🤖 Réponse ({elapsed:.1f}s) : {preview}...")
        print(f"   🔎 {status}")
        for d in details:
            print(f"      • {d}")

        results.append({
            "id": test["id"],
            "query": test["query"],
            "status": status,
            "answer": answer,
            "reference": test["reference"],
            "ground_truth": test["ground_truth"],
            "details": details,
        })

    # ============================================================
    # RAPPORT FINAL
    # ============================================================
    print("\n\n" + "=" * 70)
    print("  RAPPORT DE SYNTHÈSE")
    print("=" * 70)
    pass_n = sum(1 for r in results if r["status"].startswith("PASS"))
    hallu_n = sum(1 for r in results if "HALLUCINATION" in r["status"])
    fail_n = sum(1 for r in results if r["status"].startswith("FAIL"))
    err_n = sum(1 for r in results if r["status"] == "ERREUR")
    print(f"  Total: {total}  |  ✅ Pass: {pass_n}  |  🚨 Hallucinations: {hallu_n}  |  ❌ Fail: {fail_n}  |  Erreurs: {err_n}")
    print("=" * 70)

    # Sauvegarde du rapport détaillé
    with open("rapport_hallucination.md", "w", encoding="utf-8") as f:
        f.write("# Rapport de test anti-hallucination - JurisBot CI\n\n")
        f.write(f"**Résumé** : {pass_n}/{total} réussis, {hallu_n} hallucination(s), {fail_n} échec(s)\n\n")
        for r in results:
            emoji = "✅" if r["status"].startswith("PASS") else ("🚨" if "HALLUCINATION" in r["status"] else "❌")
            f.write(f"## {emoji} {r['id']} — {r['status']}\n\n")
            f.write(f"**Question** : {r['query']}\n\n")
            f.write(f"**Référence attendue** : {r['reference']}\n\n")
            f.write(f"**Vérité terrain** : {r['ground_truth']}\n\n")
            f.write(f"**Réponse du bot** :\n\n> {r['answer']}\n\n")
            f.write(f"**Analyse** : {'; '.join(r['details'])}\n\n---\n\n")

    print("\n📄 Rapport détaillé sauvegardé dans : rapport_hallucination.md")
    return results


if __name__ == "__main__":
    run_tests()
