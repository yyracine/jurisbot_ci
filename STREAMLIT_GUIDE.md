# 🚀 Guide Streamlit - JurisBot CI

## Installation des dépendances

```bash
pip install streamlit pandas
```

## Lancement de l'application

### 1. Démarrer l'app Streamlit
```bash
streamlit run streamlit_app.py
```

L'application s'ouvrira automatiquement dans votre navigateur à l'adresse:
```
http://localhost:8501
```

### 2. (Optionnel) Démarrer l'API FastAPI en parallèle
Pour utiliser l'API feedback complète:

```bash
python feedback_api.py
```

L'API sera disponible à:
```
http://localhost:8001
```

## 🎯 Fonctionnalités

### Page "Chat"
- **Interface de chat:** Posez des questions sur le droit du travail ivoirien
- **Boutons de feedback:**
  - 👍 **Utile** - Marquer la réponse comme correcte
  - 👎 **Pas utile** - Marquer la réponse comme erronée
  - 🚫 **Hallucination** - Signaler une hallucination détectée

### Page "Statistiques"
- **Métriques globales:**
  - Total de réponses générées
  - Total de feedbacks reçus
  - Taux d'hallucinations détectées

- **Graphiques:**
  - Distribution des feedbacks (thumbs_up, thumbs_down)
  - Visualisation des statistiques

## 📊 Données stockées

Toutes les données sont enregistrées dans le répertoire `hallucination_logs/`:
- `session_*.jsonl` - Logs des réponses
- `feedback.jsonl` - Feedbacks utilisateurs
- `alerts.jsonl` - Alertes hallucinations

## ⚙️ Configuration

### Variables d'environnement requises
Assurez-vous que votre fichier `.env` contient:
```
MISTRAL_API_KEY=votre_clé_api_mistral
```

### Paramètres Streamlit
Vous pouvez créer un fichier `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

## 🐛 Dépannage

### "ModuleNotFoundError: No module named 'streamlit'"
```bash
pip install streamlit
```

### "MISTRAL_API_KEY not found"
- Assurez-vous que `.env` est dans le même répertoire que `streamlit_app.py`
- Vérifiez que votre clé API Mistral est correcte

### "FileNotFoundError: code_du_travail_ci.md"
- Le fichier Knowledge Base doit être dans le même répertoire
- Vérifiez que le chemin est correct dans `bot_juridique.py`

## 📝 Exemple d'utilisation

1. **Lancez Streamlit:**
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Posez une question:**
   ```
   Quel est le taux des heures supplémentaires?
   ```

3. **Soumettez du feedback:**
   - Cliquez sur 👍 pour une bonne réponse
   - Cliquez sur 👎 pour une mauvaise réponse
   - Cliquez sur 🚫 pour signaler une hallucination

4. **Consultez les statistiques:**
   - Allez à l'onglet "Statistiques"
   - Visualisez les graphiques de feedback

## 🔄 Cycle de vie des données

```
Question utilisateur
    ↓
[RAG Engine] - Récupère chunks pertinents
    ↓
[LLM Mistral] - Génère réponse
    ↓
[Hallucination Detector] - Analyse réponse
    ↓
[Monitoring] - Enregistre logs + metadata
    ↓
[UI Streamlit] - Affiche réponse + boutons feedback
    ↓
Utilisateur clique feedback
    ↓
[Monitor] - Enregistre feedback
    ↓
[Statistiques] - Mise à jour des métriques
```

## 📈 Monitoring

Le système génère automatiquement:
- **Logs de session** - Une par démarrage de l'app
- **Logs de feedback** - Un par feedback utilisateur
- **Alertes** - Automatiquement si hallucination détectée

Tous les fichiers sont en format JSON Lines (`.jsonl`) pour faciliter le parsing.

## 🎓 Prochaines étapes

- [ ] Intégrer Grafana pour les dashboards
- [ ] Ajouter authentification utilisateur
- [ ] Implémenter cache pour les questions fréquentes
- [ ] Exporter rapports PDF

---

**Questions?** Consultez le CLAUDE.md ou RESUME.md pour plus de contexte.
