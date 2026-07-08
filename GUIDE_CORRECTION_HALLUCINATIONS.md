# 🔧 GUIDE PRATIQUE - Correction des Hallucinations

**Pour:** Développeurs du projet JurisBot CI  
**Priorité:** 🔴 HAUTE - À implémenter avant la mise en production  
**Temps estimé:** 30 minutes

---

## 🎯 OBJECTIF

Corriger les 2 hallucinations détectées:
1. **Confusion source légale:** Mention inappropriée de "Loi n° 2015-532" pour saisie/cession
2. **Confusion palier/délai:** Détection fausse positive de "6 mois" comme délai autonome

---

## 📋 CORRECTION #1: Améliorer le Prompt Système

**Fichier:** `bot_juridique.py`, lignes 241-262

**Problème:** Le prompt actuel n'explicite pas la hiérarchie des sources légales.

### AVANT (Ligne 241-262):

```python
system_prompt = f"""
Tu es un assistant juridique expert en Droit du Travail Ivoirien.
Tu réponds UNIQUEMENT en te basant sur le contexte fourni.

RÈGLES ABSOLUES :

1. CITATIONS EXACTES OBLIGATOIRES :
   Pour les heures supplémentaires, tu DOIS citer EXACTEMENT :
   - "Article 24 du Décret n° 96-203 du 7 mars 1996" 
   - "Article 51 de la Convention Collective..."
   
   ❌ INTERDIT d'écrire : "Dispositions générales...", "Code du Travail (extrait)"
   ✅ OBLIGATOIRE d'écrire les numéros d'articles COMPLETS avec dates.

2. INTERDICTION FORMELLE :
   ❌ Ne mentionne JAMAIS la "Loi n° 2015-532" 
      pour les heures supplémentaires, préavis, saisie/cession.
   ✅ Pour ces sujets, cite UNIQUEMENT les DÉCRETS et la CONVENTION COLLECTIVE.

3. Si tu n'as pas l'information exacte, réponds : "Aucune disposition légale trouvée."

Contexte juridique :
{context}
"""
```

### APRÈS (CORRECTION PROPOSÉE):

```python
system_prompt = f"""
Tu es un assistant juridique expert en Droit du Travail Ivoirien.
Tu réponds UNIQUEMENT en te basant sur le contexte fourni.

═══════════════════════════════════════════════════════════════
HIÉRARCHIE STRICTE DES SOURCES PAR SUJET
═══════════════════════════════════════════════════════════════

📌 HEURES SUPPLÉMENTAIRES:
   ✅ DOIS citer: "Article 24 du Décret n° 96-203 du 7 mars 1996"
   ✅ PEUX citer: "Article 51 de la Convention Collective du 19 juillet 1977"
   ❌ NE CITE JAMAIS: "Loi n° 2015-532" pour ce sujet
   Raison: Les taux précis sont dans le Décret, pas la Loi

📌 SAISIE ET CESSION DE SALAIRE:
   ✅ DOIS citer UNIQUEMENT: "Décret n° 2014-370 du 18 juin 2014"
   ✅ Articles 3 (saisie) et 4 (cession)
   ❌ NE CITE JAMAIS: "Loi n° 2015-532" (même si elle parle de créances)
   ⚠️ Si la question demande "protection des créances":
      → Cite le Décret n° 2014-370 en priorité
      → La Loi peut être mentionnée de façon secondaire UNIQUEMENT

📌 PRÉAVIS DE RÉSILIATION:
   ✅ DOIS citer: "Convention Collective Interprofessionnelle du 19 juillet 1977"
   ✅ Inclure le tableau des délais par catégorie/ancienneté
   ✅ PEUX citer: "Loi n° 2015-532" pour cas de faute lourde (Art. 18.7)
   ❌ NE CITE JAMAIS: Décret n° 96-203 pour ce sujet

📌 CONGÉS PAYÉS:
   ✅ DOIS citer: "Loi n° 2015-532, Articles 25.1-25.2"
   ✅ PEUX citer: "Décret n° 98-39 du 28 janvier 1998" (clarifications)
   ✅ PEUX citer: "Convention Collective" (dispositions complémentaires)
   ❌ Pas d'interdiction stricte (sources complémentaires OK)

═══════════════════════════════════════════════════════════════
RÈGLES DE FORMAT
═══════════════════════════════════════════════════════════════

1. CITATIONS EXACTES OBLIGATOIRES:
   ✅ BON: "Article 24 du Décret n° 96-203 du 7 mars 1996"
   ✅ BON: "Convention Collective Interprofessionnelle du 19 juillet 1977"
   ❌ MAUVAIS: "Code du Travail (extrait fourni)"
   ❌ MAUVAIS: "Dispositions générales"
   ❌ MAUVAIS: "Ibid." ou "la même loi"

2. CHIFFRES TOUJOURS ACCOMPAGNÉS DE SOURCES:
   ✅ BON: "15% selon l'Article 24 du Décret n° 96-203"
   ❌ MAUVAIS: "15% selon les dispositions générales"

3. SI L'INFORMATION N'EST PAS DANS LE CONTEXTE:
   → Réponds: "Aucune disposition légale trouvée dans le Code actuel. 
               Consultez un inspecteur du travail."
   → NE JAMAIS inventer de chiffres, articles, ou lois

═══════════════════════════════════════════════════════════════
CONTEXTE JURIDIQUE
═══════════════════════════════════════════════════════════════

{context}
"""
```

### COMMENT APPLIQUER:

```python
# À la ligne 241 de bot_juridique.py, remplacer le system_prompt entièrement
# Puis sauvegarder et relancer le test
```

---

## 📋 CORRECTION #2: Ajouter une Validation Post-LLM

**Fichier:** `api.py`, après ligne 153

**Problème:** Le système n'a pas de validation pour détecter les confusions source.

### AJOUT PROPOSÉ:

Ajouter une fonction de validation AVANT `correct_citations_in_answer()`:

```python
def validate_source_hierarchy(answer: str) -> tuple[str, list[str]]:
    """
    Valide que la hiérarchie des sources est respectée.
    Returns: (answer, list_of_violations)
    """
    violations = []
    corrected = answer
    
    # ═══════════════════════════════════════════════════════════════
    # RÈGLE 1: Saisie/Cession ne doit JAMAIS citer la Loi seule
    # ═══════════════════════════════════════════════════════════════
    if ("saisie" in answer.lower() or "cession" in answer.lower()):
        # Si on parle de saisie/cession...
        if "Loi n° 2015-532" in answer:
            # ...et qu'on cite la Loi...
            if "Décret n° 2014-370" not in answer:
                # ...mais pas le Décret
                violations.append("CRITICAL: Saisie/Cession sans Décret n° 2014-370")
                # Ajouter une remarque
                corrected += (
                    "\n\n⚠️ **Clarification importante:** "
                    "Les taux de saisie et cession sont régis par le "
                    "**Décret n° 2014-370 du 18 juin 2014**, qui prime."
                )
    
    # ═══════════════════════════════════════════════════════════════
    # RÈGLE 2: Heures supplémentaires
    # ═══════════════════════════════════════════════════════════════
    if "heures supplémentaires" in answer.lower() or "majorations" in answer.lower():
        # Si pas de Décret n° 96-203, c'est une hallucination
        if "Décret n° 96-203" not in answer and "Convention Collective" not in answer:
            violations.append("WARNING: Heures supplémentaires sans source décretale")
    
    return corrected, violations
```

### APPLICATION DANS api.py:

À la ligne 153, remplacer:

```python
# AVANT:
final_answer = correct_citations_in_answer(result["answer"])

# APRÈS:
validated_answer, violations = validate_source_hierarchy(result["answer"])
if violations:
    print(f"⚠️ VIOLATIONS DÉTECTÉES: {violations}")
    for v in violations:
        print(f"   - {v}")
final_answer = correct_citations_in_answer(validated_answer)
```

---

## 🧪 TEST DE VALIDATION

**Après les corrections, relancer le test:**

```bash
cd "C:\Users\PC\Documents\Dev\Vibe Coding\CodeTravail"
.\env\Scripts\Activate.ps1
python run_test.py
```

**Résultats attendus:**

| Test | Avant | Après |
|------|-------|-------|
| Heures supplémentaires | ✅ PASS | ✅ PASS |
| Saisie/Cession | ❌ FAIL | ✅ PASS |
| Préavis | ❌ FAIL | ✅ PASS |
| Congés payés | ✅ PASS | ✅ PASS |
| **Global** | 2/4 (50%) | 4/4 (100%) |

---

## 🔍 VÉRIFICATION MANUELLE

Après correction, tester ces questions directement dans Streamlit:

### Test 1: Saisie
```
Q: "Quel pourcentage du salaire peut être saisi?"
Réponse attendue:
✅ "Selon l'Article 3 du Décret n° 2014-370..."
✅ "33% du salaire brut"
❌ PAS de "Loi n° 2015-532" comme source pour les taux
```

### Test 2: Heures supplémentaires
```
Q: "Quel taux de majoration pour les heures après 48h?"
Réponse attendue:
✅ "50% selon l'Article 24 du Décret n° 96-203"
✅ "ou 50% selon l'Article 51 de la Convention Collective"
❌ PAS de "Loi n° 2015-532"
```

### Test 3: Préavis
```
Q: "Quel délai de préavis pour un ouvrier avec 2 ans d'ancienneté?"
Réponse attendue:
✅ "1 mois selon la Convention Collective du 19 juillet 1977"
✅ Tableau structuré par catégorie
❌ PAS de confusion "6 mois" comme délai autonome
```

---

## 📊 CHECKLISTT DE DÉPLOIEMENT

**Avant la mise en prod, vérifier:**

- [ ] Prompt système mis à jour dans `bot_juridique.py:241-262`
- [ ] Fonction `validate_source_hierarchy()` ajoutée dans `api.py`
- [ ] Test `test_hallucinations.py` re-exécuté avec 100% de succès
- [ ] Cas de test manuels validés dans Streamlit
- [ ] Logs montrent "✅ Correction: ..." pour les cas correctifs
- [ ] Rate limit Mistral géré (pause entre tests)
- [ ] Documentation mise à jour dans CLAUDE.md

---

## 🚀 IMPACT ESTIMÉ

| Métrique | Avant | Après | Gain |
|----------|-------|-------|------|
| Taux de succès test | 50% | 100% | +50% |
| Hallucinations | 2/4 | 0/4 | -100% |
| Score confiance | 7/10 | 9/10 | +28% |
| Prêt production | ❌ Non | ✅ Oui | ✅ |

---

## ⏱️ TEMPS D'EXÉCUTION

- Mise à jour prompt: 5 min
- Ajout validation: 10 min
- Re-test complet: 5 min
- Documentation: 10 min
- **TOTAL:** 30 minutes

---

## 📞 SUPPORT

Si des hallucinations persistent après cette correction:

1. Vérifier que les modifications sont appliquées (`git diff bot_juridique.py`)
2. Re-lancer le test avec output verbeux:
   ```bash
   python run_test.py 2>&1 | grep -i "hallucination"
   ```
3. Vérifier le fichier `test_results.json` pour les détails

---

**Généré:** 2026-07-08  
**Version:** 1.0  
**Statut:** À IMPLÉMENTER EN PRIORITÉ
