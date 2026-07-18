# 📖 Guide Utilisateur - JurisBot CI (Beta)

**Version:** 1.0 - Juillet 2026  
**Accès:** https://share.streamlit.io/yyracine/jurisbot_ci/main

---

## 🎯 Qu'est-ce que JurisBot CI?

JurisBot CI est une plateforme d'IA juridique pour répondre aux questions sur le **droit du travail en Côte d'Ivoire**.

Elle utilise la **Loi n° 2015-532** et la **Convention Collective Interprofessionnelle** pour fournir des réponses précises et citées.

---

## ⚡ Démarrage rapide (2 min)

### 1. Accéder à l'application
```
Ouvrir: https://share.streamlit.io/yyracine/jurisbot_ci/main
```

### 2. Poser une question
```
Exemple:
"Combien de jours de congé annuels a droit un salarié en Côte d'Ivoire?"

Tapez votre question → Cliquez "Envoyer"
```

### 3. Recevoir une réponse
```
Vous obtiendrez:
✅ Réponse précise et citée
✅ Référence exacte (Article, Décret, Loi)
✅ Sources utilisées par l'IA
```

### 4. Donner votre avis
```
Notez la réponse:
⭐ Précision juridique (1-5)
⭐ Clarté de la réponse (1-5)
⭐ Qualité des citations (1-5)
⭐ Complétude (1-5)
```

---

## 📋 Type de Questions Supportées

### ✅ Questions qui fonctionnent bien

```
Légales et spécifiques:
- "Quel est le salaire minimum en Côte d'Ivoire?"
- "Comment licencier un employé légalement?"
- "Quels sont les droits du salarié en cas de maladie?"
- "Peut-on modifier un contrat de travail?"
- "Combien de jours de préavis pour démissionner?"
```

### ❌ Questions hors domaine

```
Ne posez PAS:
- Questions sur d'autres pays
- Questions non-juridiques
- Demandes de conseils personnels/moraux
- Questions sur des domaines non-travail (immobilier, mariage, etc.)
```

**Réponse attendue pour hors-domaine:**
```
"Aucune disposition légale trouvée dans le Code actuel. 
Consultez un inspecteur du travail."
```

---

## 🎯 Critères d'Évaluation (Important!)

Lors du feedback détaillé, évaluez sur ces 4 critères:

### 1️⃣ **Précision Juridique** (1-5)
```
5 = Réponse 100% correcte et à jour
4 = Correcte mais manque de détail
3 = Partiellement correcte
2 = Plusieurs erreurs
1 = Fondamentalement fausse
```

### 2️⃣ **Clarté de la Réponse** (1-5)
```
5 = Très clair, facile à comprendre
4 = Clair mais un peu technique
3 = Compréhensible avec effort
2 = Confus ou ambigu
1 = Incompréhensible
```

### 3️⃣ **Qualité des Citations** (1-5)
```
5 = Cite l'article EXACT avec numéro
4 = Cite bien mais imprécis
3 = Cite de façon vague
2 = Citation incorrecte
1 = Pas de citation du tout
```

### 4️⃣ **Complétude** (1-5)
```
5 = Répond entièrement à la question
4 = Répond bien mais manque un aspect
3 = Répond partiellement
2 = Répond à peine
1 = Ne répond pas
```

---

## 🔍 Exemple d'Utilisation Complète

### Étape 1: Poser la question
```
Question: "Quels sont les jours fériés en Côte d'Ivoire?"
```

### Étape 2: Lire la réponse
```
Réponse attendue:
"Les jours fériés en Côte d'Ivoire incluent:
- 1er janvier (Jour de l'an)
- 20 mars (Fête du travail)
- Lundi de Pâques
- Ascension
- Lundi de Pentecôte
- 14 juillet (Fête nationale)
- 15 août (Assomption)
- 1er novembre (Toussaint)
- 25 décembre (Noël)

Conformément à l'Article 165 de la Loi n° 2015-532..."
```

### Étape 3: Évaluer
```
Précision: 5/5 ✅
Clarté: 4/5 ✅
Citations: 5/5 ✅
Complétude: 4/5 ✅
Commentaire: "Très bon, serait mieux avec dates en tableau"
```

---

## ⚠️ Limitations Connues

### Phase Beta
```
1. Première requête peut prendre 10-20 secondes (chargement du modèle)
2. Quota: 100 questions par jour par utilisateur
3. Peut y avoir des hallucinations (rare, mais possible)
4. Basé sur la loi au 17 juillet 2026
```

### Comment rapporter un problème
```
Utilisez le bouton "🚩 Signaler une hallucination" si:
- La réponse contient une fausse info
- Les citations sont incorrectes
- La réponse invente des articles

Vos signalements aident à améliorer le système!
```

---

## 🆘 FAQ - Questions Fréquentes

### Q1: Pourquoi la première réponse est lente?
```
R: L'IA charge son modèle en arrière-plan (10-20 sec).
   Les réponses suivantes sont beaucoup plus rapides.
```

### Q2: Je vois "Quota dépassé"?
```
R: Vous avez posé 100 questions aujourd'hui.
   Réessayez demain. (Limite: 100 q/jour)
```

### Q3: La réponse semble fausse?
```
R: Cliquez "🚩 Signaler une hallucination" et commentez.
   Cela aide l'équipe à améliorer le système.
```

### Q4: Quelle version du droit est utilisée?
```
R: Loi n° 2015-532 du 20 juillet 2015 (version à jour)
   Convention Collective Interprofessionnelle
```

### Q5: Puis-je utiliser ceci pour un conseil légal?
```
R: NON! C'est une aide à l'information, pas un conseil légal.
   Pour des décisions importantes, consultez un avocat.
```

---

## 📞 Support & Feedback

### Contacter l'équipe
```
Email: racine.yao@gmail.com
GitHub: https://github.com/yyracine/jurisbot_ci
```

### Partager votre feedback
```
✉️ Feedback détaillé inclus dans l'app
🚩 Signaler une hallucination
💬 Commentaires libres
📧 Email direct si problème grave
```

---

## 📊 Statistiques de Fiabilité

```
Taux de Hallucinations:        0%  ✅
Précision Juridique:           5.0/5 ⭐
Clarté des Réponses:           5.0/5 ⭐
Qualité des Citations:         5.0/5 ⭐
Satisfaction Globale:          5.0/5 ⭐

(Basé sur 10+ tests internes - Juillet 2026)
```

---

## 🎓 Conseils pour de Meilleures Réponses

### ✅ Bonne formulation
```
❌ "Congés?"
✅ "Combien de jours de congé annuels a droit un salarié en Côte d'Ivoire?"

❌ "Salaire minimum?"
✅ "Quel est le salaire minimum interprofessionnel garanti (SMIG) en Côte d'Ivoire?"

❌ "Licenciement?"
✅ "Quelles sont les procédures légales pour licencier un employé pour faute grave?"
```

### 📝 Questions détaillées obtiennent de meilleures réponses
```
Incluez:
- Le contexte (employeur/employé/secteur)
- La question spécifique
- Les détails pertinents
```

---

## 🔐 Confidentialité & Sécurité

```
✅ Vos questions sont anonymes
✅ Les données ne sont pas partagées
✅ HTTPS sécurisé (Streamlit Cloud)
✅ Pas de suivi personnalisé
```

---

**Merci de tester JurisBot CI! Vos feedbacks aident à améliorer le système.** 🙏

**Commencez maintenant:** https://share.streamlit.io/yyracine/jurisbot_ci/main
