# 📦 Guide de Migration SQLite - JurisBot CI

**Date:** 17 juillet 2026  
**Statut:** Migration complétée ✅

---

## 🎯 Vue d'ensemble

Votre système de stockage des feedbacks et réponses a été migré de **fichiers JSON** à **SQLite**. C'est plus rapide, plus sûr et mieux pour l'analyse.

### ✅ Avantages de SQLite
- 💰 **Gratuit** - Zéro coût
- ⚡ **Rapide** - Requêtes instantanées
- 🔍 **Queryable** - Facile à filtrer/trier
- 📊 **Scalable** - Pour des milliers de feedbacks
- 🔐 **Sûr** - Données intégrées

---

## 🚀 Étapes de Migration

### **Étape 1: Arrêtez l'application Streamlit**

Assurez-vous que l'app n'est pas en cours d'exécution:

```bash
# Ctrl+C dans le terminal où Streamlit tourne
```

### **Étape 2: Exécutez le script de migration**

```bash
cd "C:\Users\PC\Documents\Dev\Vibe Coding\CodeTravail"
python migrate_to_sqlite.py
```

**Résultat attendu:**
```
🔄 Démarrage de la migration JSON → SQLite...

✅ Base de données initialisée

📄 Migration des réponses depuis hallucination_logs/responses.jsonl...
   ✅ X réponses migrées

📄 Migration des feedbacks depuis hallucination_logs/feedback.jsonl...
   ✅ Y feedbacks migrés

📄 Migration des feedbacks détaillés depuis feedback_logs/detailed_feedback.jsonl...
   ✅ Z feedbacks détaillés migrés

📄 Migration des alertes depuis hallucination_logs/alerts.jsonl...
   ✅ W alertes migrées

==================================================
📊 RÉSUMÉ DE LA MIGRATION
==================================================
✅ Réponses:            X
✅ Feedbacks:           Y
✅ Feedbacks détaillés: Z
✅ Alertes:             W
==================================================

✅ Migration terminée!
📁 Fichier BD: jurisbot_ci.db
```

### **Étape 3: Lancez l'application**

```bash
streamlit run streamlit_app.py
```

Tout fonctionne comme avant, mais maintenant les données sont dans SQLite! 🎉

---

## 📊 Structure de la Base de Données

### **Table: responses**
Stocke chaque réponse générée par le bot

```sql
CREATE TABLE responses (
    id TEXT PRIMARY KEY,                  -- ID unique de la réponse
    query TEXT NOT NULL,                  -- Question posée
    answer TEXT NOT NULL,                 -- Réponse générée
    sources TEXT,                         -- JSON des sources (serialisé)
    hallucination_score REAL,            -- Score hallucination (0.0 à 1.0)
    is_hallucinating INTEGER,            -- 1 si hallucination détectée
    model TEXT,                          -- Modèle utilisé (mistral-large-latest)
    retriever TEXT,                      -- Système retrieval (FAISS)
    embedding_model TEXT,                -- Modèle embedding (mistral-embed)
    created_at TIMESTAMP                 -- Timestamp de création
)
```

### **Table: feedbacks**
Stocke les feedbacks des testeurs

```sql
CREATE TABLE feedbacks (
    id INTEGER PRIMARY KEY,              -- ID auto-incrémenté
    response_id TEXT,                    -- Référence à la réponse
    feedback_type TEXT,                  -- "quick" ou "detailed"
    feedback TEXT,                       -- Feedback rapide (thumbs_up/down/hallucination)
    is_hallucination INTEGER,            -- Flag hallucination
    accuracy INTEGER,                    -- Score 1-5 (feedback détaillé)
    clarity INTEGER,                     -- Score 1-5
    citations INTEGER,                   -- Score 1-5
    completeness INTEGER,                -- Score 1-5
    comments TEXT,                       -- Commentaires libres
    email TEXT,                          -- Email du testeur
    created_at TIMESTAMP                 -- Timestamp
)
```

### **Table: alerts**
Stocke les alertes pour hallucinations

```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY,
    response_id TEXT,
    hallucination_description TEXT,      -- Description de la hallucination
    created_at TIMESTAMP
)
```

### **Table: chat_sessions**
Réservée pour les futures statistiques de session

```sql
CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY,
    user_role TEXT,                      -- "admin" ou "tester"
    user_email TEXT,
    session_start TIMESTAMP,
    session_end TIMESTAMP
)
```

---

## 🔧 Utilisation des Données

### **Interroger les données avec Python**

```python
from db import (
    get_all_responses,
    get_all_feedbacks,
    get_stats,
    get_feedback_stats,
    export_all_data
)

# Récupérer toutes les réponses
responses = get_all_responses()

# Récupérer tous les feedbacks
feedbacks = get_all_feedbacks()

# Récupérer les statistiques du RAG
rag_stats = get_stats()
# Returns: {
#   "total_responses": 10,
#   "hallucinations_detected": 1,
#   "hallucination_rate": 10.0,
#   "average_hallucination_score": 0.15,
#   "responses_by_score": [0.05, 0.1, 0.8, ...]
# }

# Récupérer les stats des feedbacks
feedback_stats = get_feedback_stats()
# Returns: {
#   "total_feedbacks": 5,
#   "detailed_feedbacks": 3,
#   "avg_accuracy": 4.2,
#   "avg_clarity": 4.5,
#   "avg_citations": 3.8,
#   "avg_completeness": 4.1
# }

# Exporter tout (responses + feedbacks + alerts)
all_data = export_all_data()
```

### **Accéder à SQLite directement**

```bash
# Ouvrir la BD dans SQLite CLI
sqlite3 jurisbot_ci.db

# Voir les tables
.tables

# Compter les réponses
SELECT COUNT(*) FROM responses;

# Voir les feedbacks détaillés avec email
SELECT email, accuracy, clarity, comments FROM feedbacks WHERE feedback_type='detailed';

# Afficher les réponses hallucination
SELECT id, query, hallucination_score FROM responses WHERE is_hallucinating=1;
```

---

## 📁 Nettoyage des fichiers JSON

Après la migration, vous pouvez **optionnellement** supprimer les fichiers JSON anciens:

```bash
# Sauvegardez d'abord (recommandé)
mkdir backup_json_old
move hallucination_logs backup_json_old/
move feedback_logs backup_json_old/

# Ou supprimez directement (attention!)
rmdir /s /q hallucination_logs
rmdir /s /q feedback_logs
```

⚠️ **Conseil:** Gardez un backup pendant quelques semaines avant de supprimer.

---

## 🔄 Migration Future vers Supabase

Si vous décidez de passer à Supabase plus tard, c'est facile! 

Le schéma SQLite peut être facilement migré vers Supabase PostgreSQL car:
- ✅ Tables identiques
- ✅ Types de données compatibles
- ✅ Pas de dépendances SQLite spécifiques

**Script de migration Supabase** (à créer plus tard):
```python
# migrate_to_supabase.py
from db import export_all_data
import supabase

all_data = export_all_data()
# Insérer dans Supabase avec la même structure
```

---

## 📊 Fichiers SQLite

### **Localisation**
```
C:\Users\PC\Documents\Dev\Vibe Coding\CodeTravail\jurisbot_ci.db
```

### **Taille**
- Fichier unique
- Taille typique: 1-10 MB pour un MVP
- Croissance lente (1 MB ≈ 10,000 réponses)

### **Sauvegarde**
```bash
# Copier pour backup
copy jurisbot_ci.db jurisbot_ci_backup_2026-07-17.db

# Restaurer si nécessaire
copy jurisbot_ci_backup_2026-07-17.db jurisbot_ci.db
```

---

## ✅ Checklist Post-Migration

- [ ] Migration exécutée avec succès
- [ ] Application Streamlit testée
- [ ] Feedbacks peuvent être soumis
- [ ] Page Admin affiche les stats
- [ ] Export JSON fonctionne
- [ ] Fichiers JSON archivés (optionnel)
- [ ] Backup effectué

---

## 💡 Prochaines Étapes

1. **Testez le système complet** avec quelques questions
2. **Vérifiez les feedbacks** dans la page Admin
3. **Analysez les données** (voir ÉTAPE 3 - Propositions)
4. **Améliorez l'app** basé sur les feedbacks

---

## 🆘 Dépannage

### **Erreur: "jurisbot_ci.db not found"**
```bash
# Relancez juste le migration script
python migrate_to_sqlite.py
```

### **Erreur lors du load des données**
```bash
# Vérifiez que les fichiers JSON existent
ls -la hallucination_logs/
ls -la feedback_logs/
```

### **La BD est corrompue**
```bash
# Supprimez et récréez
rm jurisbot_ci.db
python migrate_to_sqlite.py
```

---

## 📞 Questions?

Consultez:
- `db.py` - Fonctions SQLite (documenté)
- `streamlit_app.py` - Utilisation dans Streamlit
- `CLAUDE.md` - Contexte du projet

---

**Migration complétée le 17 juillet 2026** ✅  
**Prochaine étape:** ÉTAPE 3 - Solutions d'analyse et d'amélioration
