# -*- coding: utf-8 -*-
"""
Second jeu de tests anti-hallucination - JurisBot CI.
13 questions DIFFÉRENTES du premier jeu (sujets nouveaux), avec vérités
terrain vérifiées mot pour mot dans code_du_travail_ci.md.

Sujets couverts (nouveaux) :
  - Congés payés (Décret 98-39)
  - Âge de la retraite (Convention Collective)
  - Prime d'ancienneté (Convention Collective)
  - Préavis de grève (Décret 96-208)
  - Jours fériés (Décret 96-205)
  - Travail à temps partiel (Décret 96-202)
  - Frais funéraires (Décret 2017-210)
  - Âge d'admission à l'emploi (Décret 96-204)
  - Cumul de mandat / durée du mandat (Décret 96-206)
  - SMAG vs SMIG
"""
import sys
import time
import traceback

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from bot_juridique import init_rag_engine, ask_legal_bot

# ============================================================
# NOUVEAU QUESTIONNAIRE (13 sujets entièrement nouveaux)
# ============================================================
TESTS = [
    {
        "id": "N1_conge_2_jours",
        "query": "Combien de jours de congé payé un travailleur adulte acquiert-il par mois de travail effectif ?",
        "must_contain": ["deux jours"],
        "must_not_contain": ["Loi n° 2015-532"],
        "reference": "Article 5 du Décret n° 98-39 du 28 janvier 1998",
        "ground_truth": "deux jours ouvrables par mois de travail pour les adultes",
    },
    {
        "id": "N2_conge_jeune_18ans",
        "query": "Quelle est la durée du congé pour un jeune travailleur de moins de 18 ans ou apprenti ?",
        "must_contain": ["vingt-quatre jours", "24 jours"],
        "must_not_contain": [],
        "reference": "Article 6 du Décret n° 98-39 du 28 janvier 1998",
        "ground_truth": "congé fixé à vingt-quatre jours ouvrables (jeunes < 18 ans et apprentis)",
    },
    {
        "id": "N3_age_retraite",
        "query": "À quel âge un travailleur peut-il partir à la retraite en Côte d'Ivoire ?",
        "must_contain": ["55"],
        "must_not_contain": ["Loi n° 2015-532"],
        "reference": "Convention Collective Interprofessionnelle (Prime de départ à la retraite)",
        "ground_truth": "L'âge du départ à la retraite est fixé à 55 ans",
    },
    {
        "id": "N4_prime_anciennete_2ans",
        "query": "À partir de combien d'années d'ancienneté un travailleur a-t-il droit à la prime d'ancienneté et à quel taux ?",
        "must_contain": ["2 %", "2%"],
        "must_not_contain": [],
        "reference": "Convention Collective Interprofessionnelle (Prime d'ancienneté)",
        "ground_truth": "2 % après 2 années d'ancienneté",
    },
    {
        "id": "N5_preavis_greve",
        "query": "Quelle est la durée du préavis de grève en droit du travail ivoirien ?",
        "must_contain": ["six jours", "6 jours"],
        "must_not_contain": [],
        "reference": "Article du Décret n° 96-208 du 7 mars 1996 (procédure de conciliation)",
        "ground_truth": "Le préavis de grève ... Sa durée est de six jours ouvrables",
    },
    {
        "id": "N6_jours_feries_chomes_payes",
        "query": "Quels sont les deux jours fériés chômés et payés obligatoires selon le Code du Travail ivoirien ?",
        "must_contain": ["Fête nationale", "1er mai"],
        "must_not_contain": [],
        "reference": "Article 1 du Décret n° 96-205 du 7 mars 1996",
        "ground_truth": "le jour de la Fête nationale et le 1er mai, Fête du Travail sont jours fériés chômés et payés",
    },
    {
        "id": "N7_temps_partiel_30h",
        "query": "À partir de quelle durée hebdomadaire un travail est-il considéré comme travail à temps partiel ?",
        "must_contain": ["30", "trente"],
        "must_not_contain": [],
        "reference": "Article du Décret n° 96-202 du 7 mars 1996",
        "ground_truth": "durée inférieure ou au plus égale à trente heures par semaine ou cent vingt heures par mois",
    },
    {
        "id": "N8_frais_funeraires_6ans",
        "query": "Quel est le montant de la participation de l'employeur aux frais funéraires pour un travailleur ayant entre 6 et 10 ans de présence ?",
        "must_contain": ["4 fois", "quatre fois"],
        "must_not_contain": [],
        "reference": "Article 7 du Décret n° 2017-210 du 30 mars 2017",
        "ground_truth": "de la 6è à la 10è année, quatre fois le salaire minimum hiérarchisé conventionnel",
    },
    {
        "id": "N9_age_embauche_14ans",
        "query": "Quel est l'âge minimum d'admission à l'emploi pour les jeunes travailleurs en Côte d'Ivoire ?",
        "must_contain": ["14", "quatorze"],
        "must_not_contain": [],
        "reference": "Décret n° 96-204 du 7 mars 1996 (et Code du Travail)",
        "ground_truth": "âge de quatorze ans requis pour l'admission à l'emploi",
    },
    {
        "id": "N10_conge_sup_15ans",
        "query": "Combien de jours de congé supplémentaires après 15 ans de services continus dans la même entreprise ?",
        "must_contain": ["2 jours", "deux jours"],
        "must_not_contain": [],
        "reference": "Article 7 du Décret n° 98-39 du 28 janvier 1998",
        "ground_truth": "deux jours ouvrables après quinze ans de services continus",
    },
    {
        "id": "N11_mandat_comite_hygiene",
        "query": "Quelle est la durée du mandat des membres du comité d'hygiène, de sécurité et des conditions de travail ?",
        "must_contain": ["2 ans", "deux ans"],
        "must_not_contain": [],
        "reference": "Article du Décret n° 96-206 du 7 mars 1996",
        "ground_truth": "La durée du mandat ... est de deux ans, renouvelable",
    },
    {
        "id": "N12_indemnite_retraite_plafond",
        "query": "Quel est le montant maximum de l'indemnité de fin de carrière (départ à la retraite) ?",
        "must_contain": ["25"],
        "must_not_contain": [],
        "reference": "Convention Collective Interprofessionnelle (Prime de départ à la retraite)",
        "ground_truth": "Le montant total ne peut excéder 25 fois le SMIG calculé sur une base annuelle de 2.080 heures",
    },
    {
        "id": "N13_nuit_jeunes_interval",
        "query": "Pendant quel intervalle horaire les jeunes de plus de 14 ans et de moins de 18 ans sont-ils interdits de travail de nuit ?",
        "must_contain": ["18", "6"],
        "must_not_contain": [],
        "reference": "Article 4 du Décret n° 96-204 du 7 mars 1996",
        "ground_truth": "période minimale de douze heures consécutives, intervalle allant de dix-huit heures à six heures",
    },
]


def normalize(text):
    import re as _re
    t = text.lower()
    t = _re.sub(r'\s*%\s*', '%', t)
    t = _re.sub(r'\s+', ' ', t)
    return t


def run_tests():
    print("=" * 70)
    print("  SECOND JEU DE TESTS (13 sujets NOUVEAUX) - JurisBot CI")
    print("=" * 70)

    print("\n⚙️  Initialisation du moteur RAG hybride (peut prendre ~30s)...")
    retriever, llm, hybrid = init_rag_engine()
    print("✅ Moteur prêt.\n")

    results = []
    for i, test in enumerate(TESTS, 1):
        print("\n" + "─" * 70)
        print(f"[{i}/13] {test['id']}")
        print(f"   ❓ {test['query']}")
        print(f"   📖 Réf. attendue : {test['reference']}")
        print(f"   ✅ Vérité terrain : {test['ground_truth']}")

        answer = ""
        error = None
        for attempt in range(5):
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
                if "429" in error:
                    wait = 20 * (attempt + 1)
                    print(f"   ⏳ Rate limité (429), attente {wait}s avant retry...")
                    time.sleep(wait)
                else:
                    traceback.print_exc()
                    break
            time.sleep(8)

        if error:
            status = "ERREUR"
            details = [f"Exception: {error}"]
        else:
            ans_low = normalize(answer)
            must_ok = [s for s in test["must_contain"] if normalize(s) in ans_low]
            must_ko = [s for s in test["must_not_contain"] if normalize(s) in ans_low]
            # Pour les must_contain à variantes (ex: "2 %" / "2%"), 1 suffisant
            must_pass = len(must_ok) >= 1
            no_hallu = len(must_ko) == 0
            if must_pass and no_hallu:
                status = "PASS ✅"
            elif must_pass and not no_hallu:
                status = "HALLUCINATION 🚨"
            elif not must_pass and not no_hallu:
                status = "FAIL ❌ (valeur absente)"
            else:
                status = "FAIL ❌ (valeur absente + hallucination)"
            details = []
            if must_ok:
                details.append(f"trouvé: {must_ok}")
            if must_ko:
                details.append(f"HALLUCINATION: {must_ko}")

        preview = answer.replace("\n", " ")[:300]
        print(f"   🤖 Réponse ({elapsed:.1f}s) : {preview}...")
        print(f"   🔎 {status}")
        for d in details:
            print(f"      • {d}")

        results.append({"id": test["id"], "query": test["query"], "status": status,
                        "answer": answer, "reference": test["reference"],
                        "ground_truth": test["ground_truth"], "details": details})
        time.sleep(12)

    # Rapport
    print("\n\n" + "=" * 70)
    print("  RAPPORT DE SYNTHÈSE (2e jeu)")
    print("=" * 70)
    pass_n = sum(1 for r in results if r["status"].startswith("PASS"))
    hallu_n = sum(1 for r in results if "HALLUCINATION" in r["status"])
    fail_n = sum(1 for r in results if r["status"].startswith("FAIL"))
    err_n = sum(1 for r in results if r["status"] == "ERREUR")
    print(f"  Total: 13 | ✅ Pass: {pass_n} | 🚨 Hallucinations: {hallu_n} | ❌ Fail: {fail_n} | Erreurs: {err_n}")
    print("=" * 70)

    with open("rapport_hallucination_jeu2.md", "w", encoding="utf-8") as f:
        f.write("# Second jeu de tests anti-hallucination (13 sujets nouveaux)\n\n")
        f.write(f"**Résumé** : {pass_n}/13 réussis, {hallu_n} hallucination(s), {fail_n} échec(s)\n\n")
        for r in results:
            emoji = "✅" if r["status"].startswith("PASS") else ("🚨" if "HALLUCINATION" in r["status"] else "❌")
            f.write(f"## {emoji} {r['id']} — {r['status']}\n\n")
            f.write(f"**Question** : {r['query']}\n\n")
            f.write(f"**Référence attendue** : {r['reference']}\n\n")
            f.write(f"**Vérité terrain** : {r['ground_truth']}\n\n")
            f.write(f"**Réponse du bot** :\n\n> {r['answer']}\n\n")
            f.write(f"**Analyse** : {'; '.join(r['details'])}\n\n---\n\n")
    print("\n📄 Rapport sauvegardé dans : rapport_hallucination_jeu2.md")
    return results


if __name__ == "__main__":
    run_tests()
