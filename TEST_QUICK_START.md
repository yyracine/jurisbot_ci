# 🚀 QUICK START - TEST D'HALLUCINATIONS

## Objectif
**Atteindre 0 hallucination avec 13 questions de test**

---

## 📋 Comment Lancer le Test

### Méthode 1: Simple (Recommandé)
```bash
python run_test.py
```

Cela va:
1. ✅ Initialiser le moteur RAG
2. ✅ Lancer 13 questions anti-hallucination
3. ✅ Attendre 3 secondes entre chaque question (pour éviter le rate limit)
4. ✅ Générer un rapport JSON avec tous les résultats
5. ✅ Afficher un résumé final dans le terminal

**Durée estimée:** ~2 minutes (39 secondes de délais + temps de réponse)

---

## 📊 Les 13 Tests

| # | Type | Question | Objectif |
|---|------|----------|----------|
| 1 | VALID | Taux de majoration heures supplémentaires | Vérifier citation du Décret n° 96-203 |
| 2 | VALID | Jours de congés payés | Vérifier citation Loi n° 2015-532 |
| 3 | VALID | Saisie et cession de salaire | Vérifier citation Décret n° 2014-370 |
| 4 | VALID | Délai de préavis | Vérifier citation Convention Collective |
| 5 | VALID | Définition du travailleur | Vérifier Article 2 correctement cité |
| 6 | VALID | Discrimination au travail | Vérifier pas d'hallucination sur formes |
| 7 | VALID | Conditions essentielles du contrat | Vérifier conditions réelles |
| 8 | VALID | Indemnité de fin de contrat | Vérifier calcul correct sans chiffre fictif |
| 9 | FALLBACK | Visa touristique (hors-sujet) | Doit retourner "Aucune disposition" |
| 10 | FALLBACK | Pilotage d'avion (absurde) | Doit retourner "Aucune disposition" |
| 11 | VALID | Avantages sociaux | Vérifier pas d'affirmation non sourcée |
| 12 | VALID | Sanctions disciplinaires | Vérifier limitations réelles |
| 13 | VALID | Procédure de licenciement | Vérifier pas de "sans notification" |

---

## 🎯 Critères de Succès

### ✅ Un test PASSE si:
1. Toutes les **expected patterns** sont présentes dans la réponse
2. **Aucun des patterns interdits** n'apparaît
3. Une **citation valide** est présente (Article, Décret, Loi, Convention)
4. Pour les tests FALLBACK: le message "Aucune disposition" apparaît

### ❌ Hallucination Détectée si:
1. ❌ Article/Décret fictif mentionné (ex: "Article 999")
2. ❌ Chiffre inventé (ex: "70%", "45 jours")
3. ❌ Affirmation sans source (ex: "l'employeur peut tout faire")
4. ❌ Citation manquante (violation de MANDATORY CITATIONS)
5. ❌ Réponse positive à une question hors-sujet

---

## 📈 Résultats Attendus

### Scénario Idéal (0 Hallucination)
```
✅ RÉUSSIS: 13/13
❌ ÉCHOUÉS: 0/13
⚠️  ERREURS: 0/13
Taux de réussite: 100.0%

🎉 SUCCÈS TOTAL: AUCUNE HALLUCINATION DÉTECTÉE!
```

### Scénario Réaliste (après correction)
```
✅ RÉUSSIS: 11/13  (patterns très stricts)
❌ ÉCHOUÉS: 2/13   (pattern matching issues)
⚠️  ERREURS: 0/13

Vérifier que les "échoués" sont dus à des patterns trop stricts,
non à des hallucinations réelles.
```

---

## 📁 Fichiers Générés

1. **test_results.json**
   - Résultats détaillés de tous les tests
   - Utilisable pour post-traitement ou dashboards

2. **Terminal Output**
   - Rapport lisible en temps réel
   - Détail des sources utilisées
   - Liste des hallucinations détectées

---

## 🔧 Configuration

### Modifier les Patterns de Test
Fichier: `test_hallucinations.py`

```python
test_case(
    test_num=1,
    question="...",
    test_type="valid",
    expected_patterns=[
        "pattern1",  # DOIT être dans la réponse
        "pattern2"
    ],
    forbidden_patterns=[
        "bad_pattern1",  # NE DOIT PAS être dans la réponse
        "hallucination"
    ]
)
```

### Augmenter le Délai
Si vous avez toujours un rate limit:
```python
time.sleep(5)  # Augmenter de 3 à 5 secondes
```

---

## 🐛 Troubleshooting

### Rate Limit (429 Error)
**Symptôme:** Tests s'arrêtent après 5 questions
**Solution:** Le délai de 3 secondes devrait suffire. Si non:
- Augmenter `time.sleep(3)` à `time.sleep(5)` ou `time.sleep(10)`
- Vérifier que `MISTRAL_API_KEY` est valide dans `.env`
- Attendre 1 heure avant de réessayer

### Pas de Réponse
**Symptôme:** Réponse vide ou timeou
**Solution:**
- Vérifier que `code_du_travail_ci.md` existe
- Vérifier la clé Mistral dans `.env`
- Redémarrer Python

### Pattern Match Trop Strict
**Symptôme:** Tests échouent mais réponse contient les informations
**Solution:** Assouplir les patterns dans `test_hallucinations.py`
```python
# Au lieu de:
"50%"

# Utiliser:
"50",  # Accepte "50%", "50 jours", etc.
```

---

## 📊 Interprétation des Résultats

### PASS (✅)
Réponse correcte, bien sourcée, aucune hallucination

### FAIL (❌)
Réponse contient une hallucination **OU** pattern match échoue
→ Vérifier le détail pour distinguer

### ERROR (⚠️)
Exception technique (rate limit, timeout, erreur API)
→ Relancer le test

---

## 🎓 Guardrails JurisBot Appliqués

✅ **NO HALLUCINATIONS:** Réponses basées uniquement sur le contexte récupéré
✅ **MANDATORY CITATIONS:** Chaque réponse inclut l'article/décret
✅ **FALLBACK PROTOCOL:** Questions hors-sujet déclenchent le message standard
✅ **TONE:** Professionnel, neutre, pédagogique

---

## 📞 Support

Voir: `TEST_HALLUCINATIONS_REPORT.md` pour une analyse détaillée

