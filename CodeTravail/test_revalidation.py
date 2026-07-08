# -*- coding: utf-8 -*-
"""
Re-validation PROPRE des réponses déjà collectées (sans rappeler Mistral).
Normalise les espaces (35 % == 35%) pour éviter les faux négatifs,
et distingue : valeur juste / source juste / hallucination résiduelle.
"""
import re

# Réponses réelles collectées lors du test post-corrections (rapport_hallucination_retry.md)
RESPONSES = {
    "Q3_heures_sup_plafond": {
        "ground_truth_value": "15 heures",
        "ground_truth_source": "Décret n° 96-203 (Art. 26)",
        "answer": "Selon la Convention Collective Interprofessionnelle du 19 juillet 1977 (Article 26) : le nombre d'heures supplémentaires est limité à quinze (15) heures au maximum par semaine.",
    },
    "Q6_essai_cadres": {
        "ground_truth_value": "trois mois",
        "ground_truth_source": "Décret n° 96-195 (Art. 2)",
        "answer": "Selon la Convention Collective Interprofessionnelle du 19 juillet 1977, la durée maximale de la période d'essai pour les ingénieurs, cadres et assimilés est fixée à trois mois.",
    },
    "Q7_essai_mensuel": {
        "ground_truth_value": "un mois",
        "ground_truth_source": "Décret n° 96-195 (Art. 2)",
        "answer": "Selon la Convention Collective Interprofessionnelle du 19 juillet 1977, la durée maximale de la période d'essai pour un travailleur payé au mois est fixée à : 1 (un) mois.",
    },
    "Q8_preavis_mensuel_6ans": {
        "ground_truth_value": "deux mois",
        "ground_truth_source": "Décret n° 96-200 (Art. 1 2°)",
        "answer": "Selon la Convention Collective Interprofessionnelle du 19 juillet 1977, un travailleur payé au mois [...] 6 ans d'ancienneté, a droit à un préavis de 2 mois.",
    },
    "Q9_saisie_33": {
        "ground_truth_value": "33%",
        "ground_truth_source": "Décret n° 2014-370 (Art. 3)",
        "answer": "Le taux maximum de la quotité saisissable est fixé à 33% de l'assiette définie à l'article 2 du Décret n° 2014-370 du 18 juin 2014 (article 3 dudit décret).",
    },
    "Q10_cession_smig_200k": {
        "ground_truth_value": "35%",
        "ground_truth_source": "Décret n° 2014-370 (Art. 4)",
        "answer": "Selon le Décret n° 2014-370 du 18 juin 2014, le taux de quotité cessible pour un salaire compris entre le SMIG (60 000 FCFA) et 200 000 FCFA est de 35 %.",
    },
    "Q11_licenciement_taux": {
        "ground_truth_value": "30%",
        "ground_truth_source": "Décret n° 2017-210 du 30 mars 2017 (Art. 4)",
        "answer": "Le taux de l'indemnité de licenciement [...] est fixé à 30 % [...] conformément : au Décret n° 2017-210 du 13 mars 2017 (Article 4) ; à la Convention Collective Interprofessionnelle du 19 juillet 1977 (Article 39).",
    },
    "Q12_duree_legale": {
        "ground_truth_value": "40 heures",
        "ground_truth_source": "Décret n° 96-203 (Art. 1)",
        "answer": "La durée légale du travail hebdomadaire pour les entreprises non agricoles est fixée à quarante (40) heures par semaine, conformément à l'Article 21.2 de la Convention Collective Interprofessionnelle du 19 juillet 1977.",
    },
    "Q13_nuit_definition": {
        "ground_truth_value": "21h-5h",
        "ground_truth_source": "Décret n° 96-204 (Art. 1)",
        "answer": "La période de travail de nuit est définie entre 21 heures et 5 heures, selon le Décret n° 96-204 du 7 mars 1996 (Article premier) et la Convention Collective Interprofessionnelle du 19 juillet 1977.",
    },
}


def norm(s):
    # normalise espaces autour des chiffres/pourcent pour comparaison juste
    return re.sub(r'\s+', ' ', s.lower().replace(' %', '%').replace('( ', '(').replace(' )', ')'))


print("=" * 78)
print("  RE-VALIDATION PROPRE (post-corrections) — analyse valeur + source")
print("=" * 78)

value_ok = source_ok = conv_bias = date_bias = 0
for qid, d in RESPONSES.items():
    a = norm(d["answer"])
    val_ok = norm(d["ground_truth_value"]) in a
    # source correcte si la réponse cite le décret attendu OU si pas de mention Loi 2015-532
    cites_decret_attendu = any(part in a for part in norm(d["ground_truth_source"]).split('(')[0:1])
    has_convention = "convention collective" in a
    has_loi_535 = "2015-532" in a
    # date Q11 : 13 mars (faux) vs 30 mars (vrai)
    date_bug = ("13 mars 2017" in a) and qid == "Q11_licenciement_taux"

    value_ok += int(val_ok)
    if has_convention and not cites_decret_attendu:
        conv_bias += 1
    if date_bug:
        date_bias += 1

    status_val = "✅" if val_ok else "❌"
    flags = []
    if has_convention and not cites_decret_attendu:
        flags.append("🟡 cité Convention au lieu du Décret")
    if date_bug:
        flags.append("🔴 date fausse (13 mars vs 30 mars)")
    if has_loi_535:
        flags.append("🚨 Loi 2015-532")

    print(f"\n{qid}")
    print(f"  valeur attendue '{d['ground_truth_value']}' : {status_val}")
    print(f"  source attendue : {d['ground_truth_source']}")
    print(f"  {'; '.join(flags) if flags else '✓ pas de biais source'}")

print("\n" + "=" * 78)
print(f"  VALEURS JUSTES         : {value_ok}/9")
print(f"  Pas de Loi 2015-532     : {9 - sum(1 for d in RESPONSES.values() if '2015-532' in norm(d['answer']))}/9  ← BIAIS PRINCIPAL ÉLIMINÉ")
print(f"  Biais Convention résid. : {conv_bias}/9  (citée au lieu du Décret)")
print(f"  Date hallucinée (Q11)   : {date_bias}     (13 mars vs 30 mars 2017)")
print("=" * 78)
