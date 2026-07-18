# 📊 Guide d'Amélioration par Analyse des Feedbacks - JurisBot CI

**Date:** 17 juillet 2026  
**Statut:** Guide complet pour exploiter les données de feedback

---

## 🎯 Objectif

Transformer les feedbacks utilisateurs en actions concrètes d'amélioration.

---

## 📋 PARTIE 1: Purger la Base de Données

### 1.1 Voir l'état actuel

```bash
python purge_database.py
```

**Résultat:**
```
📊 État actuel de la base de données:
   • Réponses: 0
   • Feedbacks: 12
   • Alertes: 2
   • Sessions: 0
   • Total: 14
```

### 1.2 Créer une sauvegarde

```bash
python purge_database.py backup
```

**Crée un fichier:** `jurisbot_ci_backup_20260717_134500.db`

### 1.3 Purger une table spécifique

```bash
# Purger uniquement les feedbacks
python purge_database.py feedbacks

# Purger uniquement les alertes
python purge_database.py alerts

# Purger uniquement les réponses
python purge_database.py responses
```

### 1.4 Purger TOUT (utiliser avec précaution!)

```bash
python purge_database.py all
```

**⚠️ Attention:** Cette action est irréversible! Une sauvegarde est créée automatiquement.

---

## 📈 PARTIE 2: Analyser les Feedbacks

### 2.1 Accès au Dashboard Admin

1. Connectez-vous avec le mot de passe admin
2. Allez dans **"Analyse & Recommandations"**
3. Explorez les 4 onglets:
   - **Satisfaction** - Score global utilisateurs
   - **Problèmes** - Zones à améliorer
   - **Quick Wins** - Actions rapides
   - **Roadmap** - Plan long terme

### 2.2 Interprétation des Métriques

#### Score de Satisfaction (0-5)

| Score | Signification | Action |
|-------|---------------|--------|
| **4.5-5.0** | ✅ Excellent | Maintenir la qualité |
| **3.5-4.4** | ⚠️ Bon | Amélioration mineure |
| **2.5-3.4** | 🔴 Moyen | Intervention requise |
| **<2.5** | 🚨 Critique | Urgence d'amélioration |

#### Taux d'Hallucination

- **0%** = ✅ Parfait (pas de fausses réponses)
- **1-5%** = ⚠️ Acceptable (surveiller)
- **>5%** = 🔴 Critique (corriger RAG)

#### Scores par Critère (1-5)

| Critère | Objectif | Signification |
|---------|----------|---------------|
| **Précision** | ≥4.5 | Réponses juridiquement exactes |
| **Clarté** | ≥4.0 | Réponses compréhensibles |
| **Citations** | ≥4.5 | Sources correctes & traçables |
| **Complétude** | ≥4.0 | Couvre la question posée |

---

## 🔍 PARTIE 3: Patterns de Feedback et Corrections

### Pattern #1: Hallucinations sur Citations

**Symptôme:**
- Utilisateur cite: "Convention Collective Interprofessionnelle du 19 juillet 1977"
- Mais la KB contient: "Ordonnance n° 2021-902 du 22 décembre 2021"

**Cause:**
- Le modèle confond les sources (hallucine les citations)

**Correction:**
```python
# Dans bot_juridique.py, fonction verify_and_correct_citations()
# Ajouter des corrections:
corrections = [
    ("Citation incorrecte A", "Citation correcte A"),
    ("Citation incorrecte B", "Citation correcte B"),
]
```

**Implémentation:**
1. Identifier les citations récurrentes incorrectes
2. Les ajouter à la liste des corrections dans `verify_and_correct_citations()`
3. Tester avec la même question pour valider

### Pattern #2: Réponses Incomplètes

**Symptôme:**
- Score Complétude < 3.5
- Utilisateur dit: "N'a pas mentionné le cas X"

**Cause:**
- Knowledge base manque d'informations
- Ou le prompt n'encourage pas les cas limites

**Correction:**
1. **Enrichir la KB:** Ajouter plus de contexte dans `code_du_travail_ci.md`
2. **Améliorer le prompt:** Ajouter une section "Cas particuliers à couvrir"

**Exemple:**
```markdown
## Art. 25.2

[Article contenu...]

### Cas particuliers:
- Femmes en congé maternité
- Travailleurs migrants
- Contrats à durée déterminée
```

### Pattern #3: Manque de Clarté

**Symptôme:**
- Score Clarté < 4.0
- Utilisateur dit: "Trop compliqué à comprendre"

**Cause:**
- Réponses trop techniques
- Pas d'exemples concrets
- Structure confuse

**Correction:**
1. Améliorer le prompt pour demander des exemples
2. Structurer avec des listes à puces
3. Ajouter des cas d'usage

**Exemple dans le prompt:**
```
Rendez votre réponse claire:
1. Réponse directe (1-2 phrases)
2. Explication légale (2-3 paragraphes)
3. Exemple concret
4. Citation exacte

Structure avec des listes à puces quand possible.
```

### Pattern #4: Précision Juridique Faible

**Symptôme:**
- Score Précision < 4.0
- Utilisateur signale une erreur juridique

**Cause:**
- Model hallucine ou confond les articles
- Knowledge base incomplète
- Erreur dans l'extraction du contexte

**Correction:**
1. Vérifier la KB pour les erreurs
2. Ajouter des clarifications dans le prompt
3. Tester avec des questions similaires

---

## 🛠️ PARTIE 4: Workflow d'Amélioration Continu

### Étape 1: Collecter les Feedbacks (Hebdomadaire)

```bash
# Télécharger les rapports
# 1. Allez dans Streamlit → Analyse & Recommandations
# 2. Téléchargez le rapport HTML
# 3. Sauvegardez dans: reports/jurisbot_report_YYYY_WW.html
```

### Étape 2: Identifier les Problèmes (Analyse)

```python
# Script: analyze_problems.py (voir exemple ci-dessous)
from db import get_all_feedbacks
from analysis import FeedbackAnalyzer

feedbacks = get_all_feedbacks()
analyzer = FeedbackAnalyzer(feedbacks, [])

problems = analyzer.get_problem_areas()
for problem in problems:
    print(f"{problem['severity']}: {problem['description']}")
```

### Étape 3: Prioriser les Corrections

| Priorité | Sévérité | Timeline |
|----------|----------|----------|
| **P0** | CRITICAL | ⚡ Même jour |
| **P1** | HIGH | 🟠 1-2 jours |
| **P2** | MEDIUM | 🟡 3-5 jours |
| **P3** | LOW | 🟢 Prochaine sprint |

### Étape 4: Implémenter les Corrections

**Checklist:**
- [ ] Reproduire le problème
- [ ] Identifier la cause racine
- [ ] Implémenter la correction
- [ ] Tester avec 5+ questions similaires
- [ ] Vérifier pas de régression
- [ ] Documenter le changement

### Étape 5: Valider les Améliorations

```bash
# 1. Redémarrer Streamlit
python -m streamlit run streamlit_app.py

# 2. Tester manuellement
# - Poser la question problématique
# - Vérifier la nouvelle réponse

# 3. Faire un test à l'IA
# - Générer 10 feedbacks de test
# - Valider les scores

# 4. Commit et push
git add .
git commit -m "Fix: [Description du problème et solution]"
git push
```

---

## 📊 PARTIE 5: Rapports d'Amélioration

### 5.1 Générer un Rapport de Feedback

```bash
python generate_report.py
```

**Fichiers générés:**
- `jurisbot_report_analysis_*.json` - Données brutes
- `jurisbot_report_recommendations_*.json` - Actions
- `jurisbot_report_*.html` - Rapport visuel

### 5.2 Exporter les Données

```python
from db import export_all_data

data = export_all_data()
# Retourne un dict avec:
# {
#     "responses": [...],
#     "feedbacks": [...],
#     "alerts": [...],
#     "chat_sessions": [...]
# }
```

### 5.3 Créer un Rapport CSV

```python
import pandas as pd
from db import get_all_feedbacks

feedbacks = get_all_feedbacks()
df = pd.DataFrame([f.dict() for f in feedbacks])
df.to_csv("feedbacks_export.csv", index=False)
```

---

## 🎯 PARTIE 6: Cas d'Usage Réels

### Cas #1: Hallucinations Récurrentes

**Problème observé:**
```
Feedback #5: Citations incorrectes (Article 25.2 + Convention 1977)
Feedback #8: Même problème
Feedback #12: Même problème encore
```

**Analyse:**
- 3 occurrences du même bug
- Sévérité: HIGH
- Cause: Prompt confond les sources

**Solution:**
1. Ajouter correction dans `verify_and_correct_citations()`
2. Améliorer le prompt pour Article 25
3. Tester avec 10 questions sur Article 25
4. Valider que le taux d'hallucination reste à 0%

**Temps estimé:** 30 minutes

### Cas #2: Réponses Incomplètes

**Problème observé:**
```
Score Complétude moyen: 3.2/5
Feedback: "Vous n'avez pas mentionné le délai de 48h"
```

**Analyse:**
- Question concernant délais préavis
- KB manque de détails sur les délais
- Besoin d'enrichissement

**Solution:**
1. Enrichir `code_du_travail_ci.md` avec tableaux de délais
2. Ajouter exemples concrets
3. Améliorer le prompt: "Toujours mentionner les délais exacts"

**Temps estimé:** 1 heure

### Cas #3: Manque de Clarté

**Problème observé:**
```
Score Clarté moyen: 3.8/5
Feedback: "Réponse trop technique, pas assez d'exemples"
```

**Analyse:**
- Utilisateurs non-juridiques ne comprennent pas
- Besoin de langage simplifié
- Manque d'exemples concrets

**Solution:**
1. Améliorer le prompt: demander plus d'exemples
2. Ajouter section "En langage simple" à chaque réponse
3. Tester avec utilisateurs non-juridiques

**Temps estimé:** 1-2 heures

---

## 📅 Schedule Recommandé

### Chaque Jour
- [ ] Lire les nouveaux feedbacks
- [ ] Signaler les bugs critiques

### Chaque Semaine
- [ ] Générer un rapport d'analyse
- [ ] Identifier les patterns récurrents
- [ ] Prioriser les corrections

### Chaque 2 Semaines
- [ ] Implémenter les corrections P0/P1
- [ ] Tester les améliorations
- [ ] Recueillir des métriques de validation

### Chaque Mois
- [ ] Rapport complet d'amélioration
- [ ] Revue de la satisfaction globale
- [ ] Planning de la prochaine itération

---

## 🚀 Améliorations Futures

### Quick Wins (1-2 jours)
1. [ ] Corriger hallucinations de citations
2. [ ] Améliorer clarté des réponses
3. [ ] Ajouter plus d'exemples

### Moyen Terme (1-2 semaines)
1. [ ] Enrichir KB avec nouveaux cas
2. [ ] Fine-tuner le prompt système
3. [ ] Ajouter FAQ basées sur feedbacks

### Long Terme (1-3 mois)
1. [ ] Implémenter feedback multilangue
2. [ ] Ajouter apprentissage automatique
3. [ ] Créer modèle spécialisé Mistral
4. [ ] Migrer vers Supabase pgvector

---

## 📞 Support & Questions

Pour des questions sur l'interprétation des feedbacks:
1. Consultez le fichier `ANALYSIS_GUIDE.md`
2. Vérifiez les exemples dans `analysis.py`
3. Testez avec le dashboard Streamlit

---

**Créé par:** Claude Code (Haiku 4.5)  
**Date:** 17 juillet 2026  
**Dernier update:** Session courante  
**Status:** 🟢 Prêt à utiliser

