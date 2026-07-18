# 🔍 SYSTÈME DE MONITORING & FEEDBACK - GUIDE COMPLET

**Date:** 8 juillet 2026  
**Objectif:** Détecter et tracker les hallucinations en production  
**Status:** ✅ Prêt pour la production

---

## 📌 RÉSUMÉ EXÉCUTIF

Le projet JurisBot CI est passé de "0 hallucination détectée dans les tests" à **un système complet de monitoring en production** qui:

✅ **Enregistre chaque réponse** du bot  
✅ **Analyse automatiquement** les hallucinations  
✅ **Collecte le feedback utilisateur**  
✅ **Génère des alertes** en temps réel  
✅ **Exporte des rapports** pour analyse  

---

## 🏗️ ARCHITECTURE DU SYSTÈME

```
┌─────────────────────────────────────────────────────────┐
│          USER FACING - Frontend Streamlit               │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
   ask_legal_bot_monitored()      FEEDBACK BUTTON
        │                             │
┌───────▼─────────────────┐ ┌────────▼─────────────────┐
│  bot_juridique_monitored│ │   Feedback Submission    │
│  + Hallucination Check  │ │   (HTTP POST)            │
└───────┬─────────────────┘ └────────┬─────────────────┘
        │                            │
        │    HallucinationDetector   │
        │    (analyse la réponse)    │
        │                            │
        └────────────┬───────────────┘
                     │
            ┌────────▼────────┐
            │   Monitoring    │
            │   (enregistre)  │
            └────────┬────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
   Session    Feedback    Alerts
    Logs       Logs       Logs
```

---

## 📁 FICHIERS DU SYSTÈME

| Fichier | Rôle | Taille |
|---------|------|--------|
| **monitoring.py** | Logger les réponses et feedbacks | ~150 lignes |
| **hallucination_detector.py** | Analyser les hallucinations | ~300 lignes |
| **feedback_api.py** | API FastAPI pour feedback/stats | ~200 lignes |
| **bot_juridique_monitored.py** | Wrapper du bot avec monitoring | ~150 lignes |
| **MONITORING_GUIDE.md** | Ce guide | Ce fichier |

---

## 🚀 DÉMARRAGE RAPIDE

### 1️⃣ Lancer le Bot Monitoré

```bash
python bot_juridique_monitored.py
```

**Que se passe-t-il:**
- 🧠 Initialisation du moteur RAG
- ❓ 3 questions de test sont posées
- 🔍 Chaque réponse est analysée pour hallucinations
- 📊 Statistiques affichées à la fin

### 2️⃣ Lancer l'API Feedback (dans un autre terminal)

```bash
python feedback_api.py
```

**API disponible sur:** `http://localhost:8001`

### 3️⃣ Soumettre un Feedback

```bash
# Bonne réponse (thumbs up)
curl -X POST http://localhost:8001/feedback/submit \
  -H "Content-Type: application/json" \
  -d '{
    "response_id": "resp_20260708_120000_123456",
    "feedback": "thumbs_up",
    "is_hallucination": false,
    "details": "Réponse correcte et bien citée"
  }'

# Mauvaise réponse (thumbs down)
curl -X POST http://localhost:8001/feedback/submit \
  -H "Content-Type: application/json" \
  -d '{
    "response_id": "resp_20260708_120000_123456",
    "feedback": "thumbs_down",
    "is_hallucination": true,
    "details": "Mentionne Article 999 qui n'\''existe pas"
  }'
```

### 4️⃣ Consulter les Statistiques

```bash
# Résumé simple
curl http://localhost:8001/stats/summary

# Statistiques détaillées
curl http://localhost:8001/stats

# Exporter un rapport
curl -X POST http://localhost:8001/export/report
```

---

## 🔍 COMMENT FONCTIONNE LA DÉTECTION

### Phase 1: Enregistrement de la Réponse

```python
response = ask_legal_bot_monitored(query, retriever, llm)
# Génère un response_id unique : resp_20260708_120000_123456
```

**Enregistré dans:** `hallucination_logs/session_*.jsonl`

### Phase 2: Analyse Automatique

Le `HallucinationDetector` vérifie:

#### ✅ 1. CITATIONS (30 points)
- Références valides: "Décret n° 96-203", "Loi n° 2015-532"
- Articles réels: "Article 24", "Article 2"
- Pas d'articles > 200 (fictifs)

```python
❌ BAD: "Selon l'Article 999..."
✅ GOOD: "Selon l'Article 24 du Décret n° 96-203..."
```

#### ✅ 2. PATTERNS (15 points)
- Dates suspectes: "Loi du 50 juillet" (impossible)
- Références incomplètes: "Décret n°" (sans numéro)
- Affirmations non sourcées

```python
❌ BAD: "Décret n° 96-203 du 20 juillet 2015" (mauvaise date)
✅ GOOD: "Décret n° 96-203 du 7 mars 1996"
```

#### ✅ 3. COHÉRENCE SOURCES (30 points)
- Références mentionnées = références dans sources?
- Contexte coherent?
- Pas de contradiction?

#### ✅ 4. NOMBRES (25 points)
- Pourcentages réalistes (0-100%)
- Délais logiques (1-365 jours)
- Pas de chiffres inventés

```python
❌ BAD: "Les heures supp sont majorées de 70%"
✅ GOOD: "Les heures supp sont majorées de 25% ou 50%"
```

### Phase 3: Score Final

```
Score = (Citations + Patterns + Sources + Nombres) / 4.0
```

- **0.0 - 0.3:** ✅ Probablement valide
- **0.3 - 0.5:** ⚠️ Confiance moyenne
- **0.5 - 0.7:** 🟠 Suspect
- **0.7 - 1.0:** 🚨 Hallucination probable

---

## 📊 LOGS & RAPPORTS

### Structure des Logs

```
hallucination_logs/
├── session_20260708_120000.jsonl      # Session courante
├── session_20260708_130000.jsonl      # Sessions précédentes
├── feedback.jsonl                      # Tous les feedbacks
├── alerts.jsonl                        # Toutes les alertes
└── monitoring_report_export.json       # Rapport exporté
```

### Contenu d'une Session

```jsonl
{
  "id": "resp_20260708_120000_123456",
  "timestamp": "2026-07-08T12:00:00.123456",
  "query": "Quel est le taux des heures supplémentaires?",
  "answer": "Selon l'Article 24 du Décret n° 96-203...",
  "sources": [{"source_ref": "Décret n° 96-203", "snippet": "..."}],
  "detection": {
    "hallucination_score": 0.15,
    "is_hallucinating": false,
    "confidence": "high",
    "issues": []
  }
}
```

### Exemple d'Alerte

```jsonl
{
  "timestamp": "2026-07-08T12:00:30.123456",
  "severity": "HIGH",
  "type": "HALLUCINATION_DETECTED",
  "response_id": "resp_20260708_120000_999999",
  "description": "Score: 75% - Pattern fictif détecté, Article 999"
}
```

---

## 🎯 TABLEAU DE BORD

### Endpoint: GET /stats/summary

```json
{
  "total_responses": 42,
  "total_feedback": 15,
  "hallucinations_detected": 2,
  "hallucination_rate": "13.33%",
  "recent_alerts_count": 2
}
```

**Interprétation:**
- 42 réponses générées
- 15 feedbacks collectés (35.7% de participation)
- 2 hallucinations confirmées par utilisateurs
- Taux d'hallucination: 13.33%

### Endpoint: POST /export/report

Génère un rapport JSON complet avec:
- Statistiques globales
- Derniers alertes
- Chemins des fichiers logs
- Timestamp du rapport

---

## 🔄 INTÉGRATION AVEC LE FRONTEND

### Option 1: Streamlit (Recommandée)

```python
import streamlit as st
import requests

st.title("🤖 JurisBot - Assistant Juridique")

# Poser une question
query = st.text_input("Votre question:")

if st.button("Demander"):
    # Appeler le bot
    response = ask_legal_bot_monitored(query, retriever, llm)
    
    st.write(response["answer"])
    
    # Afficher les sources
    with st.expander("📎 Sources"):
        for src in response["sources"]:
            st.write(f"• {src['source_ref']}")
    
    # Afficher le score d'hallucination
    detection = response["detection"]
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Score Hallucination", f"{detection['hallucination_score']:.0%}")
    with col2:
        st.metric("Confiance", detection['confidence'].upper())
    
    # Boutons de feedback
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👍 Bonne réponse"):
            # Soumettre feedback
            requests.post("http://localhost:8001/feedback/submit", json={
                "response_id": response["response_id"],
                "feedback": "thumbs_up",
                "is_hallucination": False
            })
            st.success("Merci pour votre feedback!")
    
    with col2:
        if st.button("👎 Mauvaise réponse"):
            details = st.text_input("Détails du problème:")
            if details:
                requests.post("http://localhost:8001/feedback/submit", json={
                    "response_id": response["response_id"],
                    "feedback": "thumbs_down",
                    "is_hallucination": True,
                    "details": details
                })
                st.error("Problème enregistré, merci!")
```

### Option 2: FastAPI REST

Le bot peut être intégré dans une API FastAPI:

```python
from fastapi import FastAPI
from bot_juridique_monitored import ask_legal_bot_monitored

app = FastAPI()
retriever, llm = init_rag_engine()

@app.post("/ask")
async def ask(query: str):
    return ask_legal_bot_monitored(query, retriever, llm)
```

---

## 📈 ANALYSE DES DONNÉES

### Extraire les Hallucinations Confirmées

```bash
# Afficher les hallucinations trouvées par les utilisateurs
cat hallucination_logs/feedback.jsonl | \
  jq 'select(.is_hallucination == true)'
```

### Calculer le Taux de Hallucination

```python
import json

hallucinations = 0
total = 0

with open("hallucination_logs/feedback.jsonl") as f:
    for line in f:
        entry = json.loads(line)
        total += 1
        if entry.get("is_hallucination"):
            hallucinations += 1

rate = (hallucinations / total) * 100
print(f"Taux d'hallucination: {rate:.2f}%")
```

### Identifier les Patterns Problématiques

```python
import json
from collections import Counter

patterns = Counter()

with open("hallucination_logs/alerts.jsonl") as f:
    for line in f:
        alert = json.loads(line)
        # Extraire le pattern du type d'alerte
        alert_type = alert.get("type")
        patterns[alert_type] += 1

print(patterns.most_common())
```

---

## 🚨 SEUILS D'ALERTE (Recommandés)

| Métrique | Alerte | Critique |
|----------|--------|----------|
| Taux hallucination | > 10% | > 20% |
| Hallucinations/jour | > 5 | > 10 |
| Feedback négatif | > 30% | > 50% |
| Score moyen | < 0.5 | < 0.3 |

---

## 🔧 CONFIGURATION

### Modifier les Patterns de Détection

Éditer `hallucination_detector.py`:

```python
class HallucinationDetector:
    def __init__(self):
        self.valid_decrees = {
            "96-203": "Décret n° 96-203 du 7 mars 1996",
            # Ajouter de nouveaux décrets ici
        }
```

### Changer le Répertoire des Logs

```python
from monitoring import HallucinationMonitor

monitor = HallucinationMonitor(log_dir="/chemin/custom/logs")
```

### Ajuster les Seuils de Score

```python
# Changer le seuil d'hallucination (par défaut 0.5)
if detection_results["hallucination_score"] > 0.6:  # Plus strict
    print("Possible hallucination")
```

---

## 🧪 TESTS DU SYSTÈME

### Test 1: Bonne Réponse

```bash
python -c "
from bot_juridique_monitored import *
retriever, llm = init_rag_engine()
result = ask_legal_bot_monitored('Quel est le taux des heures supplémentaires?', retriever, llm)
assert result['detection']['hallucination_score'] < 0.5
print('✅ Test 1 OK')
"
```

### Test 2: Hallucination Détectée

```bash
python -c "
from hallucination_detector import HallucinationDetector
detector = HallucinationDetector()
result = detector.detect_hallucinations('Article 999 dit que...', [])
assert result['is_hallucinating']
print('✅ Test 2 OK')
"
```

### Test 3: API Feedback

```bash
# Démarrer l'API
python feedback_api.py &
sleep 2

# Tester l'endpoint health
curl http://localhost:8001/health

# Tester les stats
curl http://localhost:8001/stats/summary
```

---

## 📚 RESSOURCES ADDITIONNELLES

- **RESUME.md** - État global du projet
- **TEST_HALLUCINATIONS_REPORT.md** - Résultats des tests initiaux
- **bot_juridique.py** - Moteur RAG original
- **CLAUDE.md** - Règles métier

---

## 🎯 PROCHAINES ÉTAPES

### Phase 2 (Recommandée)
- [ ] Intégrer avec Streamlit UI
- [ ] Ajouter authentification utilisateur
- [ ] Stocker logs dans base de données

### Phase 3
- [ ] Dashboard de monitoring (Grafana/Metabase)
- [ ] Alertes email automatiques
- [ ] Retraitement automatique des hallucinations

### Phase 4
- [ ] Machine learning pour prédiction (fine-tuning)
- [ ] Boucle d'apprentissage continu
- [ ] A/B testing des prompts

---

## 📞 SUPPORT

**Questions?** Consultez CLAUDE.md ou le RESUME.md

**Problèmes?** Vérifiez:
1. `MISTRAL_API_KEY` dans `.env`
2. Ports disponibles (8000, 8001)
3. Fichiers de logs dans `hallucination_logs/`

---

**Créé par:** Claude Code  
**Version:** 1.0 Production  
**Statut:** ✅ Prêt à déployer
