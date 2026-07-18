# 🚀 Configuration Streamlit Cloud - Guide Complet

**Date:** Juillet 2026  
**Objectif:** Déployer JurisBot CI sur Streamlit Cloud

---

## 📋 Avant de Commencer

### Prérequis
```
✅ Compte GitHub: yyracine/jurisbot_ci
✅ Compte Streamlit Cloud (gratuit)
✅ MISTRAL_API_KEY (clé API active)
✅ SUPABASE_URL et SERVICE_ROLE_KEY
✅ ADMIN_PASSWORD (récupérer depuis .env)
```

---

## 🔑 Étape 1: Récupérer les Secrets

### A. MISTRAL_API_KEY
```
1. Aller sur https://console.mistral.ai/api-keys
2. Login et copier votre clé active
3. Format: [votre-mistral-api-key]
```

### B. SUPABASE URL & KEY
```
1. Aller sur https://app.supabase.com
2. Sélectionner projet "jurisbot_ci"
3. Settings → API
4. Copier:
   - URL: [votre-supabase-url]
   - Key: [votre-supabase-service-role-key]
```

### C. ADMIN_PASSWORD
```
Récupérer du fichier .env:
grep ADMIN_PASSWORD .env
```

---

## 🌐 Étape 2: Streamlit Cloud Deployment

### Connexion et Création
```
1. Aller sur https://share.streamlit.io
2. Sign in with GitHub
3. Cliquer "New app"
4. Sélectionner:
   - Repository: yyracine/jurisbot_ci
   - Branch: main
   - Main file: streamlit_app.py
5. Cliquer Deploy
```

---

## 🔐 Étape 3: Configurer les Secrets

### Accès aux Secrets
```
1. Dans votre app, cliquer ⚙️ "Manage app" (bas-droit)
2. Cliquer "Settings"
3. Cliquer "Secrets"
```

### Ajouter les Secrets
```
Copier ceci dans l'éditeur:

MISTRAL_API_KEY = "[votre-mistral-api-key]"
SUPABASE_URL = "[votre-supabase-url]"
SUPABASE_SERVICE_ROLE_KEY = "[votre-supabase-key]"
ADMIN_PASSWORD = "[votre-admin-password]"
```

**Format Important:**
```
- Une variable par ligne
- Pas d'espaces autour du =
- Valeurs entre guillemets
```

### Sauvegarder
```
1. Cliquer "Save"
2. Attendre redémarrage (30-60 sec)
3. App doit charger sans erreur
```

---

## 🧪 Tests Post-Configuration

### Test 1: App Fonctionne
```
✅ Pas d'erreur "ValueError"
✅ Chat interface visible
```

### Test 2: Poser une Question
```
Q: "Quel est le salaire minimum en Côte d'Ivoire?"
✅ Reçoit une réponse (15-30 sec)
```

### Test 3: Admin Login
```
✅ Entrer le password admin
✅ Sidebar montre "Admin Mode"
```

### Test 4: Rate Limiting
```
✅ Après 100 questions: "Quota dépassé"
```

---

## 🆘 Troubleshooting

### "ValueError: MISTRAL_API_KEY introuvable"
```
→ Vérifier secret "MISTRAL_API_KEY" dans Settings
→ Pas d'espace, format correct
→ Save et redémarrer
```

### "Timeout after 30 seconds"
```
→ Première requête: 20 sec normal (FAISS loading)
→ Vérifier quota Mistral: console.mistral.ai
→ Attendre 5 min et réessayer
```

### "Authentication failed with Supabase"
```
→ Vérifier SUPABASE_SERVICE_ROLE_KEY correcte
→ Doit commencer par "sb_secret_"
→ Regénérer dans Supabase si besoin
```

---

## ✅ Checklist Finale

```
[ ] Secrets configurés (4 variables)
[ ] App redémarrée sans erreur
[ ] Chat interface visible
[ ] Question test reçoit réponse
[ ] Admin login fonctionne
[ ] Rate limiting actif
```

---

**Setup Time:** ~25 minutes  
**Support:** racine.yao@gmail.com

---

⚠️ **Sécurité:**
- Ne JAMAIS partager les secrets
- Streamlit Cloud chiffre automatiquement
- Secrets visibles uniquement par vous
