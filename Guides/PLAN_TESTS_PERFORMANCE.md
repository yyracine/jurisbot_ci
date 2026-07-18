# 🧪 Plan de Tests de Performance - JurisBot CI

**Date:** Juillet 2026  
**Objectif:** Valider que l'application supporte les tests utilisateurs sans dégradation

---

## 📊 Objectifs de Performance

### Cibles de Production
```
✅ Temps de réponse:        < 30 secondes (incluant latence)
✅ Taux d'erreur:           < 1% (< 1 erreur / 100 requêtes)
✅ Disponibilité:           > 99% (sauf maintenance)
✅ Taux hallucination:      < 5% (0% souhaité)
✅ Satisfaction utilisateur: > 4.0/5 (sur 5)
```

---

## 🏗️ Architecture Test

### Environnement Test
```
Plateforme: Streamlit Cloud (production)
Utilisateurs simulés: 5-10 (bêta interne)
Durée: 1 semaine (7 jours)
Monitoring: 24/7
```

### Métriques à Tracker
```
1. Response Time (temps de réponse)
2. Error Rate (taux d'erreur)
3. Uptime (disponibilité)
4. API Cost (coûts Mistral)
5. Hallucination Rate (taux hallucination)
6. User Satisfaction (satisfaction utilisateurs)
```

---

## 📅 Calendrier des Tests

### Phase 0: Préparation (Jour 1)
```
Activités:
- [ ] Déployer sur Streamlit Cloud
- [ ] Configurer monitoring logs
- [ ] Vérifier connexion Supabase
- [ ] Tester flow complet localement
- [ ] Documenter baseline metrics
```

### Phase 1: Tests Internes (Jour 2-3)
```
Activités:
- [ ] Équipe interne pose 20 questions
- [ ] Valider rate limiting (100 q/jour)
- [ ] Vérifier logs générés
- [ ] Mesurer temps de réponse
- [ ] Tester gestion d'erreur
```

### Phase 2: Beta Restreinte (Jour 4-7)
```
Activités:
- [ ] Inviter 5 testeurs externes
- [ ] Chacun pose 20-30 questions
- [ ] Monitorer en temps réel
- [ ] Collecter feedbacks
- [ ] Identifier problèmes
```

### Phase 3: Analyse (Jour 8)
```
Activités:
- [ ] Compiler tous les résultats
- [ ] Analyser hallucinations
- [ ] Calculer satisfaction moyenne
- [ ] Décider: go/no-go pour production
```

---

## 🔧 Scénarios de Test

### Scénario 1: Questions Légales Simples
```
Questions:
1. "Quel est le salaire minimum en Côte d'Ivoire?"
2. "Combien de jours de congé annuels?"
3. "Quels sont les jours fériés?"
4. "Quels sont les droits du travailleur?"
5. "Comment démissionner?"

Attentes:
- Réponse claire et citée
- Temps < 30 sec
- Pas d'erreur
- Score hallucination = 0
```

### Scénario 2: Questions Complexes
```
Questions:
1. "Procédure complète de licenciement pour faute grave"
2. "Droits et obligations lors du télétravail"
3. "Règles de calcul des heures supplémentaires"
4. "Protection légale des femmes enceintes"
5. "Différences entre CDI et contrats temporaires"

Attentes:
- Réponse complète et structurée
- Temps < 40 sec
- Citations précises
- Score satisfaction > 4/5
```

### Scénario 3: Questions Hors Domaine
```
Questions:
1. "Combien coûte un ticket avion pour Paris?"
2. "Quelle est la meilleure université aux USA?"
3. "Comment préparer un couscous?"
4. "Quelles actions acheter en bourse?"
5. "Est-ce que les vaccins sont sûrs?"

Attentes:
- Fallback: "Aucune disposition légale trouvée..."
- Temps < 10 sec (pas d'appel LLM)
- Pas de hallucination
- Pas d'erreur
```

### Scénario 4: Charge Simultanée
```
Configuration:
- 5 utilisateurs
- Chacun pose 10 questions
- Espacement: 2-5 sec entre questions
- Durée totale: ~30 min

Métriques:
- Tous les utilisateurs reçoivent une réponse ✅
- Pas de timeout ✅
- Pas de crash ✅
- Temps moyen < 30 sec ✅
```

---

## 📈 Métriques Détaillées à Collecter

### Par Question
```json
{
  "question_id": "Q001",
  "user_id": "U001",
  "question": "Quel est le salaire minimum?",
  "response_time_ms": 8500,
  "word_count": 250,
  "citations_found": 2,
  "hallucination_score": 0.0,
  "is_error": false,
  "error_type": null,
  "user_satisfaction": 5,
  "timestamp": "2026-07-18T14:30:00Z"
}
```

### Agrégées
```
Total Questions:          50
Réponses Réussies:        49 (98%)
Erreurs:                  1 (2%)
Temps Moyen:              12.5 sec
Temps Min:                3.2 sec
Temps Max:                45.8 sec
Hallucinations Totales:   0 (0%)
Satisfaction Moyenne:     4.8/5
```

---

## 🎯 Critères de Succès / Échec

### ✅ SUCCÈS (Green Light pour Production)
```
✅ Taux d'erreur ≤ 1%
✅ Temps moyen ≤ 20 sec
✅ Hallucination rate ≤ 5%
✅ Satisfaction ≥ 4.0/5
✅ Uptime ≥ 99%
✅ Rate limiting fonctionne
✅ Logs créés correctement
```

### ⚠️ ATTENTION (Yellow Light - Optimisation Requise)
```
⚠️ Taux d'erreur 1-5%
⚠️ Temps moyen 20-40 sec
⚠️ Hallucination rate 5-10%
⚠️ Satisfaction 3.5-4.0/5
⚠️ Uptime 95-99%
```

### ❌ BLOCKER (Red Light - Halt Production)
```
❌ Taux d'erreur > 5%
❌ Temps moyen > 40 sec
❌ Hallucination rate > 10%
❌ Satisfaction < 3.5/5
❌ Uptime < 95%
❌ Rate limiting échoue
❌ Logs non générés
```

---

## 🔍 Checklist de Monitoring

### Avant les Tests
```
[ ] Logs vides et prêts
[ ] Supabase connectée et testée
[ ] MISTRAL_API_KEY valide et avec quota
[ ] Monitoring.py bug corrigé
[ ] Rate limiting activé
[ ] Erreurs handling en place
```

### Pendant les Tests
```
Daily Check:
[ ] Application up et responsive
[ ] Aucun crash ou erreur critique
[ ] Logs générés correctement
[ ] Hallucinations track
[ ] Quota utilisateurs track
[ ] Performance trends track
```

### Après les Tests
```
[ ] Tous les logs compilés
[ ] Hallucinations analysées
[ ] Satisfaction compilée
[ ] Errors categorizées
[ ] Rapport généré
[ ] Recommandations faites
```

---

## 📊 Dashboard Monitoring Simple

### URL Logs
```
Fichier: jurisbot_production.log
Rotation: Aucune (⚠️ à implémenter)
Nettoyage: Manuel avant prod
```

### Commandes Utiles
```bash
# Voir les 50 dernières erreurs
tail -50 jurisbot_production.log | grep ERROR

# Compter les erreurs
grep -c ERROR jurisbot_production.log

# Voir les 10 dernières questions
tail -10 jurisbot_production.log | grep "Bot answer"

# Voir le taux d'erreur
echo "Total: $(wc -l < jurisbot_production.log) | Errors: $(grep -c ERROR jurisbot_production.log)"
```

---

## 🛠️ Troubleshooting

### Problème: Réponses lentes (> 40 sec)
```
Causes possibles:
1. Mistral API surchargée → Wait & Retry
2. Supabase lent → Check database status
3. Réseau lent → Check connectivity
4. Modèle pas chargé → Première requête toujours lente

Solutions:
1. Réessayer après 5 min
2. Vérifier quota Mistral
3. Vérifier network latency
4. Accepter 20 sec pour 1ère requête
```

### Problème: Taux erreur élevé (> 5%)
```
Causes possibles:
1. MISTRAL_API_KEY invalide
2. SUPABASE_URL invalide
3. Rate limit atteint
4. Bug dans try/except

Solutions:
1. Vérifier credentials dans Streamlit Cloud Secrets
2. Test connexion Supabase
3. Réduire quota ou attendre
4. Vérifier logs pour exceptions
```

### Problème: Hallucinations élevées (> 10%)
```
Causes possibles:
1. Modèle moins fiable que prévu
2. Question ambiguë
3. Knowledge base incomplète
4. Bug dans hallucination detector

Solutions:
1. Vérifier score hallucination_detector
2. Reformuler la question
3. Enrichir knowledge base
4. Revoir fallback protocol
```

---

## 📝 Template Rapport Final

```markdown
# Rapport Tests Performance - JurisBot CI
Date: 2026-07-18
Durée: 7 jours
Testeurs: 5-10 personnes

## Résultats Globaux
- Total Questions: XXX
- Taux Succès: XX%
- Hallucinations: XX
- Satisfaction Moyenne: X.X/5

## Par Catégorie
- Questions Légales: X/5
- Questions Complexes: X/5
- Hors Domaine: X/5
- Load Test: X/5

## Problèmes Identifiés
1. [Si applicable]
2. [Si applicable]

## Recommandations
1. [Pour production]
2. [Pour améliorations]

## Verdict: [GREEN/YELLOW/RED]
```

---

## 🎓 Conclusion

**Cet plan de test assurera que:**

✅ L'application est stable pour beta  
✅ Performance acceptable (< 30 sec)  
✅ Taux erreur minimal (< 1%)  
✅ Hallucinations contrôlées (< 5%)  
✅ Utilisateurs satisfaits (> 4.0/5)  

**Après ces tests → Green Light pour Production!**

---

**Commencer les tests le:** [Indiquer date]  
**Responsable:** [Indiquer personne]  
**Slack/Email:** [Canal de suivi]
