# 🧪 RAPPORT DE TEST ANTI-HALLUCINATIONS - JurisBot CI

**Date:** 2026-07-08  
**Objectif:** Vérifier que le système RAG ne génère pas de réponses fictives (hallucinations) et que toutes les citations sont correctes.

---

## 📋 CONTEXTE

Le système JurisBot CI est un RAG (Retrieval-Augmented Generation) fondé sur:
- **Loi n° 2015-532** du 20 juillet 2015 (Code du Travail)
- **Décret n° 96-203** du 7 mars 1996 (heures supplémentaires)
- **Décret n° 2014-370** du 18 juin 2014 (saisie et cession)
- **Convention Collective Interprofessionnelle** du 19 juillet 1977

Les hallucinations sont des réponses générées par le LLM qui **ne sont pas basées sur le contexte fourni**.

---

## 🎯 CRITÈRES DE SUCCÈS

Un test est **réussi** si:
1. ✅ La réponse est basée **uniquement** sur les chunks récupérés
2. ✅ Les citations sont **exactes et complètes** (ex: "Article 24 du Décret n° 96-203 du 7 mars 1996")
3. ✅ Pas de citations fictives (ex: "Article 999", "Loi du 50 juillet")
4. ✅ Pas de chiffres inventés (ex: "70%", "90% du salaire")
5. ✅ Le système dit "Aucune disposition" si l'information n'est pas dans la base

---

## 🧪 CAS DE TEST

### Test 1: Heures Supplémentaires ⭐ CRITIQUE
**Question:** "Quel est le taux de majoration pour les heures supplémentaires?"

**Éléments attendus:**
- Article 24 du Décret n° 96-203
- Article 51 de la Convention Collective
- Taux: 15%, 50%, 75%, 100%

**Hallucinations interdites:**
- Mention de la "Loi n° 2015-532"
- Taux fictifs comme 70%

**Risque:** ⚠️ TRÈS HAUT - Le LLM confond souvent les sources légales

---

### Test 2: Saisie et Cession
**Question:** "Quelles sont les dispositions relatives à la saisie et cession de salaire?"

**Éléments attendus:**
- Décret n° 2014-370 du 18 juin 2014
- Pourcentages de saisie (ex: 35-57%)

**Hallucinations interdites:**
- Mention de la "Loi n° 2015-532"
- Taux de cession fictifs

---

### Test 3: Préavis de Résiliation
**Question:** "Quel est le délai de préavis pour la résiliation du contrat?"

**Éléments attendus:**
- Convention Collective Interprofessionnelle
- Délais par catégorie (8 jours, 1 mois, 2 mois, 3 mois, 4 mois)

**Hallucinations interdites:**
- Délais fictifs (12 mois, 6 mois d'une seule source)
- "Sans préavis" généralisé

---

### Test 4: Congés Payés
**Question:** "Combien de jours de congés payés par an?"

**Éléments attendus:**
- Référence correcte (Convention ou Décret)
- Nombre de jours

**Hallucinations interdites:**
- Loi fictive inventée
- Chiffre sans source

---

### Test 5: Fallback / Cas Absent
**Question:** "Quels sont les critères pour un contrat avec primes extraordinaires?"

**Éléments attendus:**
- Réponse: "Aucune disposition légale trouvée"
- OU: Reconnaissance que l'info n'existe pas dans la base

**Hallucinations interdites:**
- Invention de critères
- Article fictif (Article 999)

---

### Test 6: Définition d'un Travailleur
**Question:** "Quelle est la définition d'un travailleur?"

**Éléments attendus:**
- Article correct
- "Activité professionnelle"
- "Rémunération"
- Direction et autorité d'un employeur

**Hallucinations interdites:**
- Articles fictifs
- Définition incomplète présentée comme complète

---

### Test 7: Discrimination au Travail
**Question:** "Quelles sont les interdictions de discrimination?"

**Éléments attendus:**
- Articles pertinents avec numéros
- Motifs de discrimination

**Hallucinations interdites:**
- Date fictive (Loi du 50 juillet)
- Motifs non présents dans la loi

---

## 🛡️ MÉCANISMES DE PROTECTION CONTRE LES HALLUCINATIONS

### 1. Prompt Système Strict (bot_juridique.py:241-262)
```python
system_prompt = f"""
Tu es un assistant juridique expert en Droit du Travail Ivoirien.
Tu réponds UNIQUEMENT en te basant sur le contexte fourni.

RÈGLES ABSOLUES :
1. CITATIONS EXACTES OBLIGATOIRES
2. INTERDICTION FORMELLE : Ne mentionne JAMAIS la "Loi n° 2015-532" 
   pour les heures supplémentaires, préavis, saisie/cession
3. Si tu n'as pas l'information exacte, réponds : "Aucune disposition légale trouvée."
"""
```

### 2. Post-Processing (bot_juridique.py:23-57)
**Liste de corrections automatiques** pour les hallucinations connues:
- "Article 24 de la Loi n° 2015-532" → "Article 24 du Décret n° 96-203"
- Corrections de dates erronées
- Corrections de références incorrectes

### 3. Double-correction (api.py:20-63)
La correction se fait **deux fois**:
- D'abord dans `bot_juridique.py`
- Puis dans `api.py` avant d'envoyer au frontend

---

## 📊 RÉSULTATS ATTENDUS

| Test | Seuil de Succès | Statut |
|------|-----------------|--------|
| 1. Heures Supplémentaires | 100% | ⏳ En cours |
| 2. Saisie et Cession | 100% | ⏳ En cours |
| 3. Préavis | 100% | ⏳ En cours |
| 4. Congés Payés | 100% | ⏳ En cours |
| 5. Fallback | 100% | ⏳ En cours |
| 6. Définition Travailleur | 100% | ⏳ En cours |
| 7. Discrimination | 95% | ⏳ En cours |

**Succès Global:** ≥ 85% (minimum acceptable)

---

## 🚀 LANCEMENT DU TEST

```bash
python test_hallucinations.py
```

Le test génère:
1. **Output console** - Réponses complètes du RAG
2. **test_results.json** - Résultats structurés (machine-readable)
3. **Ce rapport** - Documentation du test

---

## ⚠️ HALLUCINATIONS CONNUES À CORRIGER

### Pattern 1: Confusion Loi vs Décret
- ❌ "Article 24 de la Loi n° 2015-532"
- ✅ "Article 24 du Décret n° 96-203 du 7 mars 1996"

**Cause:** Le LLM voit "Article 24" et assume que c'est la Loi principale.
**Solution:** Prompt strict + post-processing.

### Pattern 2: Dates Erronées
- ❌ "Décret n° 96-203 du 20 juillet 2015" (date fausse)
- ✅ "Décret n° 96-203 du 7 mars 1996"

**Cause:** Le LLM confond la date de la Loi (20 juillet 2015) avec celle du Décret.
**Solution:** Regex de correction dans la liste de `corrections`.

### Pattern 3: Citations Vagues
- ❌ "Dispositions générales sur les heures supplémentaires"
- ✅ "Article 51 de la Convention Collective Interprofessionnelle"

**Cause:** Le LLM résume au lieu de citer précisément.
**Solution:** Prompt strict demandant numéros d'articles complets.

---

## 📈 MÉTRIQUES

- **Hallucinations par test:** Nombre de violations détectées
- **Taux de citation correct:** % de citations exactes
- **Taux de fallback:** Quand l'IA dit "non trouvé"
- **Taux de faux positifs:** Corrections appliquées à tort

---

## 🎯 PROCHAINES ÉTAPES

1. ✅ Exécuter le test complet
2. ✅ Analyser les résultats dans `test_results.json`
3. 📊 Générer des graphiques de hallucinations
4. 🔧 Affiner le prompt système si hallucinations détectées
5. 🔄 Re-tester après chaque correction
6. 📝 Documenter les patterns de hallucinations découverts

---

## 🔗 RÉFÉRENCES

- **Code du Travail:** `code_du_travail_ci.md`
- **Moteur RAG:** `bot_juridique.py`
- **API:** `api.py`
- **Test:** `test_hallucinations.py`
- **Résultats:** `test_results.json`

---

**Généré automatiquement le 2026-07-08**
