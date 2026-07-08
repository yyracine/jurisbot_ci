# 🎬 DÉMO - SYSTÈME DE MONITORING EN PRODUCTION

**Durée:** ~10 minutes  
**Objectif:** Voir le monitoring en action

---

## 📋 PLAN DE DÉMO

```
1. Lancer le bot monitoré (terminal 1)
   ↓
2. Voir les hallucinations détectées automatiquement
   ↓
3. Consulter les logs générés
   ↓
4. Lancer l'API Feedback (terminal 2)
   ↓
5. Soumettre des feedbacks via cURL
   ↓
6. Voir les statistiques en temps réel
```

---

## 🎯 ÉTAPE 1 - Lancer le Bot avec Monitoring

### Terminal 1:

```bash
cd "C:\Users\PC\Documents\Dev\Vibe Coding\CodeTravail"
python bot_juridique_monitored.py
```

### Résultat attendu:

```
🚀 Initialisation du bot juridique avec monitoring...
🧠 Chargement et indexation du Code du Travail...
📑 6 sections juridiques détectées.
✂️ Document découpé en 2156 chunks avec métadonnées.
✅ Moteur RAG initialisé avec succès !

======================================================================
❓ QUESTION : Quel est le taux des heures supplémentaires?
======================================================================

🔍 Recherche pour : 'Quel est le taux des heures supplémentaires?'
🤖 Appel à Mistral AI...
✅ Réponse reçue de Mistral.

╔═══════════════════════════════════════════════════════════════╗
║          🔍 RAPPORT DE DÉTECTION D'HALLUCINATIONS             ║
╚═══════════════════════════════════════════════════════════════╝

🎯 SCORE D'HALLUCINATION : 12%
📊 CONFIANCE : high
✅ PROBABLEMENT VALIDE

📋 PROBLÈMES DÉTECTÉS (0):
  ✅ Aucun problème détecté

⏰ Timestamp : 2026-07-08T12:00:00.123456
═══════════════════════════════════════════════════════════════

📊 Response ID pour feedback : resp_20260708_120000_123456

╔═════════════════════════════════════════════════════════════╗
║            📝 SOUMETTRE UN FEEDBACK                         ║
╚═════════════════════════════════════════════════════════════╝

Si vous trouvez une ERREUR ou une HALLUCINATION dans la réponse,
envoyez un feedback via cURL ou Postman :

📤 Endpoint (thumbs_down) :
curl -X POST http://localhost:8001/feedback/submit \
  -H "Content-Type: application/json" \
  -d '{
    "response_id": "resp_20260708_120000_123456",
    "feedback": "thumbs_down",
    "is_hallucination": true,
    "details": "Description du problème trouvé"
  }'
```

---

## 📊 ÉTAPE 2 - Examiner les Logs

### Terminal 3 (lecture des logs):

```bash
cd "C:\Users\PC\Documents\Dev\Vibe Coding\CodeTravail"

# Voir la dernière session
cat hallucination_logs/session_*.jsonl | tail -1 | python -m json.tool

# Voir les alertes
cat hallucination_logs/alerts.jsonl | python -m json.tool
```

### Résultat:

```json
{
  "id": "resp_20260708_120000_123456",
  "timestamp": "2026-07-08T12:00:00.123456",
  "query": "Quel est le taux des heures supplémentaires?",
  "answer": "Selon l'Article 24 du Décret n° 96-203 du 7 mars 1996, le taux de majoration des heures supplémentaires est de 25%...",
  "sources": [
    {
      "source_ref": "Décret n° 96-203 du 7 mars 1996",
      "snippet": "Article 24 : Majoration des heures supplémentaires..."
    }
  ],
  "detection": {
    "hallucination_score": 0.12,
    "is_hallucinating": false,
    "confidence": "high",
    "issues": []
  },
  "metadata": {
    "model": "mistral-large-latest",
    "retriever": "FAISS",
    "embedding_model": "mistral-embed"
  }
}
```

---

## 🔗 ÉTAPE 3 - Lancer l'API Feedback

### Terminal 2:

```bash
cd "C:\Users\PC\Documents\Dev\Vibe Coding\CodeTravail"
python feedback_api.py
```

### Résultat attendu:

```
🚀 Démarrage de l'API Feedback...
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Application startup complete
```

---

## 💬 ÉTAPE 4 - Soumettre des Feedbacks

### Test 1: Bonne réponse (thumbs up)

```bash
curl -X POST http://localhost:8001/feedback/submit \
  -H "Content-Type: application/json" \
  -d '{
    "response_id": "resp_20260708_120000_123456",
    "feedback": "thumbs_up",
    "is_hallucination": false,
    "details": "Réponse correcte, bien citée, sources valides"
  }'
```

**Réponse:**
```json
{
  "status": "success",
  "message": "Feedback enregistré avec succès",
  "response_id": "resp_20260708_120000_123456",
  "is_hallucination": false
}
```

### Test 2: Mauvaise réponse (hallucination)

```bash
curl -X POST http://localhost:8001/feedback/submit \
  -H "Content-Type: application/json" \
  -d '{
    "response_id": "resp_20260708_120001_654321",
    "feedback": "thumbs_down",
    "is_hallucination": true,
    "details": "La réponse mentionne Article 999 qui n'\''existe pas. Hallucination détectée!"
  }'
```

**Résultat dans les logs:**
```
[Terminal 1] 🚨 ALERTE HALLUCINATION : Score: 75% - Pattern fictif détecté, Article 999
```

**Et dans le fichier:**
```bash
cat hallucination_logs/alerts.jsonl
```
```json
{
  "timestamp": "2026-07-08T12:00:30.123456",
  "severity": "HIGH",
  "type": "HALLUCINATION_DETECTED",
  "response_id": "resp_20260708_120001_654321",
  "description": "Score: 75% - Pattern fictif détecté, Article 999"
}
```

---

## 📊 ÉTAPE 5 - Consulter les Statistiques

### Résumé Simple

```bash
curl http://localhost:8001/stats/summary
```

**Réponse:**
```json
{
  "total_responses": 3,
  "total_feedback": 2,
  "hallucinations_detected": 1,
  "hallucination_rate": "50.00%",
  "recent_alerts_count": 1
}
```

### Statistiques Détaillées

```bash
curl http://localhost:8001/stats | python -m json.tool
```

**Réponse:**
```json
{
  "status": "success",
  "statistics": {
    "total_responses": 3,
    "total_feedback": 2,
    "hallucinations_detected": 1,
    "false_positive_rate": 50.0,
    "alerts": [
      {
        "timestamp": "2026-07-08T12:00:30.123456",
        "severity": "HIGH",
        "type": "HALLUCINATION_DETECTED",
        "response_id": "resp_20260708_120001_654321",
        "description": "Score: 75% - Pattern fictif détecté"
      }
    ]
  }
}
```

### Exporter le Rapport

```bash
curl -X POST http://localhost:8001/export/report
```

**Crée:** `monitoring_report_export.json`

```bash
cat monitoring_report_export.json | python -m json.tool
```

---

## 🎯 ÉTAPE 6 - Analyser une Réponse

### Bonne réponse:

```bash
curl -X POST http://localhost:8001/analyze/response \
  -H "Content-Type: application/json" \
  -d '{
    "answer": "Selon l'\''Article 24 du Décret n° 96-203 du 7 mars 1996, les heures supplémentaires sont majorées de 25%.",
    "sources": [{"source_ref": "Décret n° 96-203"}],
    "query": "Taux heures supp?"
  }'
```

**Réponse:**
```json
{
  "analysis": {
    "hallucination_score": 0.1,
    "is_hallucinating": false,
    "confidence": "high",
    "issues": []
  },
  "report": "╔═══════════════════════════════════════════════════════╗\n║  🔍 RAPPORT DE DÉTECTION D'HALLUCINATIONS        ║\n╚═══════════════════════════════════════════════════════╝\n\n🎯 SCORE D'HALLUCINATION : 10%\n📊 CONFIANCE : high\n✅ PROBABLEMENT VALIDE\n..."
}
```

### Mauvaise réponse (hallucination):

```bash
curl -X POST http://localhost:8001/analyze/response \
  -H "Content-Type: application/json" \
  -d '{
    "answer": "L'\''Article 999 du Décret fantôme stipule que les heures supp sont majorées de 70% toujours.",
    "sources": [],
    "query": "Taux heures supp?"
  }'
```

**Réponse:**
```json
{
  "analysis": {
    "hallucination_score": 0.85,
    "is_hallucinating": true,
    "confidence": "high",
    "issues": [
      "❌ Citation suspecte : Numéro d'article trop grand (fictif) - Article 999",
      "⚠️ Pas de sources fournies (réponse potentiellement hallucination)",
      "❌ Pourcentage suspect : 70%"
    ]
  }
}
```

---

## 📈 RÉSULTATS ATTENDUS

### Après la Démo:

```
hallucination_logs/
├── session_20260708_120000.jsonl    # 3 réponses
├── feedback.jsonl                    # 2 feedbacks
└── alerts.jsonl                      # 1 alerte

Statistiques:
- Total responses: 3
- Total feedback: 2
- Hallucinations detected: 1 (50% feedback rate)
- False positive rate: 50%
```

---

## 🧪 TESTS À FAIRE

### Test 1: Feedback négatif sur bonne réponse

```bash
# Vérifier que le système enregistre le feedback même si la réponse est correcte
curl -X POST http://localhost:8001/feedback/submit \
  -H "Content-Type: application/json" \
  -d '{
    "response_id": "resp_20260708_120000_123456",
    "feedback": "thumbs_down",
    "is_hallucination": false,
    "details": "N'\''aime pas le ton de la réponse"
  }'

# Vérifier dans les stats
curl http://localhost:8001/stats/summary
```

**Attendu:**
```json
{
  "total_feedback": 3,
  "hallucinations_detected": 1,
  "hallucination_rate": "33.33%"
}
```

### Test 2: Plusieurs hallucinations

```bash
# Soumettre 3 mauvaises réponses
for i in {1..3}; do
  curl -X POST http://localhost:8001/feedback/submit \
    -H "Content-Type: application/json" \
    -d "{
      \"response_id\": \"resp_bad_$i\",
      \"feedback\": \"thumbs_down\",
      \"is_hallucination\": true,
      \"details\": \"Hallucination #$i\"
    }"
done

# Vérifier le taux
curl http://localhost:8001/stats/summary
```

---

## 💡 POINTS CLÉS

✅ **Chaque réponse est analysée automatiquement**
- Score calculé en temps réel
- Alertes générées si problème

✅ **Le feedback utilisateur est précieux**
- Valide les hallucinations détectées
- Identifie les faux positifs

✅ **Les données sont tracées pour amélioration**
- Logs JSON pour analyse
- Statistiques en temps réel
- Rapports exportables

✅ **Intégration facile avec UI**
- Endpoints REST simples
- JSON standardisé
- Prêt pour Streamlit/React

---

## 🚀 PROCHAINES ACTIONS

1. **Intégrer Streamlit** - Ajouter boutons de feedback dans UI
2. **Automatiser les alertes** - Email/Slack si hallucination détectée
3. **Dashboard** - Grafana pour suivi en temps réel
4. **Machine Learning** - Fine-tuning basé sur hallucinations

---

**Créé par:** Claude Code  
**Date:** 8 juillet 2026
