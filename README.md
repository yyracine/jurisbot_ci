# 🤖 JurisBot CI - Assistant Juridique IA

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/yyracine/jurisbot-ci/streamlit_app.py)

Plateforme intelligente de conseil juridique basée sur l'IA pour le droit du travail ivoirien.

## 🎯 Fonctionnalités

- ⚖️ **Réponses précises** sur le droit du travail ivoirien
- 📖 **Citations exactes** des articles de loi
- 🚫 **Anti-hallucination** - Garantit des réponses factuelles
- 💬 **Système de feedback** - Pour améliorer continuellement
- 📊 **Dashboard analytics** - Suivre la qualité du système

## 📚 Sources Juridiques

- Loi n° 2015-532 (Code du Travail ivoirien)
- Convention Collective Interprofessionnelle
- Décret n° 2022-31 (Télétravail)

## 🚀 Accès à l'Application

**URL de production:**
```
https://share.streamlit.io/yyracine/jurisbot-ci/streamlit_app.py
```

### Démarrage Local

```bash
# 1. Cloner le repo
git clone https://github.com/yyracine/jurisbot_ci.git
cd jurisbot_ci

# 2. Créer l'environnement virtuel
python -m venv env
source env/Scripts/activate  # Windows: env\Scripts\activate.ps1

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Éditer secrets.toml et ajouter votre clé Mistral API

# 5. Lancer l'app
streamlit run streamlit_app.py
```

L'app sera accessible à: `http://localhost:8501`

---

## 📖 Guides Disponibles

### Pour les Utilisateurs
- **[Guide d'Utilisation](GUIDE_UTILISATEUR.md)** — Comment poser des questions et laisser du feedback
- **[Guide des Testeurs Beta](BETA_TESTER_GUIDE.md)** — Checklist complète de test

### Pour les Développeurs
- **[Documentation RAG](README_RAG_SYSTEM.md)** — Architecture du système RAG
- **[Guide d'Intégration](RAG_INTEGRATION_GUIDE.md)** — Intégrer la base de connaissance

---

## 🏗️ Architecture

```
jurisbot-ci/
├── streamlit_app.py          # Interface utilisateur
├── bot_juridique.py          # Moteur RAG principal
├── hallucination_detector.py # Détection des hallucinations
├── monitoring.py             # Monitoring et analytics
├── feedback_analytics.py      # Analyse des feedbacks
├── requirements.txt          # Dépendances Python
├── .streamlit/
│   ├── config.toml          # Configuration Streamlit
│   └── secrets.toml         # Variables d'environnement
├── code_du_travail_ci.md     # Base de connaissance
├── faiss_indexes/           # Index vectoriel FAISS
└── feedback_logs/           # Logs des feedbacks utilisateurs
```

## 🛠️ Tech Stack

- **Backend:** Python 3.11+
- **Frontend:** Streamlit
- **IA:** LangChain + Mistral AI
- **Vector DB:** FAISS (local), pgvector (production)
- **Monitoring:** Système custom de logging

## 📊 Pages Disponibles

### 1. Chat
- Poser des questions sur le droit du travail
- Recevoir des réponses citées
- Laisser des feedbacks détaillés

### 2. Statistiques
- Taux d'hallucinations détectées
- Nombre de réponses générées
- Métriques de qualité RAG

### 3. Feedbacks
- Voir les évaluations moyennes
- Consulter les commentaires des testeurs
- Exporter les données (JSON/CSV)

---

## 💬 Comment Laisser du Feedback

### Feedback Rapide
Après chaque réponse, cliquez:
- 👍 Utile
- 👎 Pas utile
- 🚫 Hallucination

### Feedback Détaillé (Recommandé)
Remplissez le formulaire avec:
- Scores de précision, clarté, citations, complétude
- Commentaires détaillés
- Email pour suivi

---

## 🧪 Tests & Validation

Lancer les tests:
```bash
python run_15_tests.py
```

Analyser les résultats:
```bash
python feedback_analytics.py
```

---

## 🚨 Signaler un Bug

### Hallucination Détectée?
1. Cliquez 🚫 **Hallucination** dans l'app
2. Remplissez le formulaire avec les détails
3. Précisez ce qui est faux

### Autre Bug?
- Email: racine.yao@gmail.com
- Décrivez la question, la réponse reçue, et ce qui est incorrect

---

## 📋 Configuration Streamlit Cloud

### 1. Secrets Requis
Dans **Settings → Secrets**, ajoutez:
```toml
mistral_api_key = "sk-xxxxx"
```

### 2. Variables d'Environnement
- `MISTRAL_API_KEY` — Clé API Mistral
- `LOG_LEVEL` — "INFO" ou "DEBUG"

---

## 📈 Roadmap

- [ ] Support pgvector pour base de données
- [ ] Authentification utilisateur
- [ ] Export des réponses en PDF
- [ ] Support multilingue
- [ ] API REST pour intégration

---

## 👥 Contribution

Ce projet est en phase **Beta**. Vos retours sont précieux!

### Comment Contribuer
1. Tester l'application
2. Laisser du feedback détaillé
3. Signaler les hallucinations
4. Suggérer des améliorations

---

## 📄 Licence

© 2026 JurisBot CI - Tous droits réservés

---

## 📞 Contact

- **Email:** racine.yao@gmail.com
- **App:** https://share.streamlit.io/yyracine/jurisbot-ci/streamlit_app.py
- **Repo:** https://github.com/yyracine/jurisbot_ci

---

**Merci de tester JurisBot CI! 🙏**

*Dernière mise à jour: 10 juillet 2026*
