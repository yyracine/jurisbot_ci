# 📚 Guide d'Utilisation - JurisBot CI

Bienvenue dans **JurisBot CI**, votre assistant juridique IA pour le droit du travail ivoirien!

---

## 🎯 Qu'est-ce que JurisBot CI?

JurisBot CI est une plateforme intelligente qui répond à vos questions sur:
- 📜 **Loi n° 2015-532** (Code du Travail ivoirien)
- 📋 **Convention Collective Interprofessionnelle**
- 📖 **Décret n° 2022-31** (Télétravail)

Toutes les réponses sont **basées sur le texte officiel** et incluent des citations exactes.

---

## 🚀 Accès à l'Application

**URL:** 
```
https://share.streamlit.io/yyracine/jurisbot-ci/streamlit_app.py
```

Aucune installation requise - tout se passe dans votre navigateur! 🌐

---

## 💬 Comment Poser une Question

### Étape 1: Allez à l'onglet "Chat"
![](https://via.placeholder.com/300x100?text=Onglet+Chat)

### Étape 2: Entrez votre question
- Cliquez dans la zone de texte
- Tapez votre question **clairement et précisément**
- Appuyez sur **"📤 Envoyer"**

### Exemples de bonnes questions:

✅ **Claires et spécifiques:**
- "Quel est le délai de préavis légal pour un licenciement?"
- "Que dit la loi sur les heures supplémentaires?"
- "Comment fonctionne le télétravail en Côte d'Ivoire?"

❌ **Trop vagues:**
- "Parlez-moi de la loi"
- "Dites-moi tout sur le contrat"

### Étape 3: Lisez la réponse
- La réponse apparaît sous votre question
- Elle est **citée** avec les articles de loi
- Lisez attentivement et vérifiez la cohérence

---

## ⭐ Système de Feedback

Après chaque réponse, vous pouvez donner votre avis:

### 1️⃣ Feedback Rapide (Immédiat)
Cliquez sur l'un des trois boutons:

- **👍 Utile** — La réponse vous a aidé
- **👎 Pas utile** — La réponse n'était pas pertinente  
- **🚫 Hallucination** — La réponse est fausse ou contradictoire

### 2️⃣ Feedback Détaillé (Recommandé ⭐)

Pour une meilleure analyse, remplissez le formulaire complet:

**📌 Précision juridique** (1-5 étoiles)
- 5 = Entièrement correct et exact
- 1 = Entièrement faux

**💬 Clarté de la réponse** (1-5 étoiles)
- 5 = Très facile à comprendre
- 1 = Très confus ou incompréhensible

**📖 Qualité des citations** (1-5 étoiles)
- 5 = Sources exactes et pertinentes
- 1 = Aucune source ou sources erronées

**✅ Complétude** (1-5 étoiles)
- 5 = Répond complètement à la question
- 1 = Ne répond que partiellement

**💭 Commentaires** (Optionnel)
- Décrivez les erreurs trouvées
- Suggérez des améliorations
- Notez ce qui a bien fonctionné

**📧 Email** (Optionnel)
- Pour que nous puissions vous suivre
- Permet un contact ultérieur si besoin

---

## 📊 Consulter les Statistiques

### Onglet "Statistiques"
Montre:
- 📝 Nombre total de réponses générées
- 🚨 Taux d'hallucinations détectées
- 📊 Score de hallucination moyen

**Utile pour:** Voir la performance globale du système

### Onglet "Feedbacks"
Affiche:
- 📈 Scores moyens des évaluations
- 📊 Graphiques d'analyse
- 💬 Tous les commentaires des testeurs
- 📥 Options d'export (JSON, CSV)

**Utile pour:** Voir ce que pensent les autres testeurs

---

## 📋 Checklist de Test Complète

Pendant votre test, essayez de couvrir ces domaines:

### Questions Basiques
- [ ] Durée légale du travail par semaine?
- [ ] Délai de préavis pour licenciement?
- [ ] Droits en matière de congés?

### Questions Intermédiaires
- [ ] Procédure de grève?
- [ ] Indemnité de fin de contrat?
- [ ] Droits des femmes enceintes?

### Questions Avancées
- [ ] Télétravail (modalités)?
- [ ] Clause de confidentialité (validité)?
- [ ] Suspension du contrat de travail?

### Évaluation
Pour chaque question:
- [ ] La réponse est-elle juridiquement exacte?
- [ ] Les citations sont-elles correctes?
- [ ] Les numéros d'article sont-ils exacts?
- [ ] La réponse couvre-t-elle votre question?
- [ ] Le langage est-il clair?

---

## 🎯 Comment Interpréter les Réponses

### Structure Standard d'une Réponse
```
1. DÉFINITION ou RÉSUMÉ
   → Explication simple du concept

2. RÈGLES APPLICABLES
   → Articles de loi cités textuellement

3. CAS PARTICULIERS
   → Exceptions ou conditions spéciales

4. RÉFÉRENCES
   → Articles et décrets cités
```

### Signes d'une Bonne Réponse ✅
- Cite les numéros d'articles
- Inclut le texte officiel
- Couvre plusieurs aspects de la question
- Mentionne les exceptions

### Signes d'une Mauvaise Réponse ⚠️
- Pas de citations précises
- Langage vague ("probablement", "peut-être")
- Contradictions avec la loi connue
- Réponse hors sujet

---

## 🚨 Signaler une Hallucination

**Une hallucination** = la réponse invente des informations

### Exemples:
- ❌ "L'article 42 dit que..." (alors que cet article n'existe pas)
- ❌ "La loi autorise X" (mais la loi dit Y)
- ❌ Inventer des dispositions légales

### Comment Signaler:
1. **Cliquez:** 🚫 **Hallucination**
2. **Remplissez le formulaire détaillé**
3. **Décrivez précisément** ce qui est faux:
   - Quel article/texte est incorrect?
   - Que dit réellement la loi?
   - Quel est le bon numéro d'article?

---

## 💡 Conseils pour de Meilleurs Tests

### 1. Posez des questions variées
- Ne testez pas toujours le même sujet
- Essayez des questions simples ET complexes
- Explorez différentes sections du Code

### 2. Vérifiez les détails
- Les numéros d'article sont-ils corrects?
- Les textes cités correspondent-ils?
- Les dates sont-elles exactes?

### 3. Soyez constructif
- Si vous trouvez une erreur, décrivez-la
- Donnez des suggestions d'amélioration
- Dites ce qui a bien fonctionné!

### 4. Testez les cas limites
- Questions très spécifiques
- Cas particuliers (apprentis, stagiaires, etc.)
- Situations rares ou complexes

---

## ❓ FAQ - Questions Fréquentes

### Q: Je ne trouve pas la réponse à ma question?
**R:** JurisBot CI répond uniquement sur le droit du travail ivoirien. Si votre question n'est pas couverte, elle sort peut-être du scope légal ivoirien.

### Q: La réponse est trop longue/courte?
**R:** Cliquez 📖 "Complétude" dans le feedback détaillé et notez-le!

### Q: Puis-je utiliser les réponses comme conseil juridique?
**R:** Non! JurisBot CI est un outil éducatif. Pour un avis juridique, consultez un avocat.

### Q: Mes données sont-elles sauvegardées?
**R:** Oui! Vos questions et feedbacks aident à améliorer le système.

### Q: Pourquoi y a-t-il des erreurs?
**R:** C'est normal en phase de test! Vos retours aident à corriger les problèmes.

---

## 📞 Support & Retours

### Comment Contacter?
- 📧 Email: racine.yao@gmail.com
- 💬 Formulaire de feedback dans l'app
- 🐛 Signaler un bug via le formulaire

### Que Inclure dans un Bug Report?
1. **La question posée**
2. **La réponse reçue**
3. **Ce qui est incorrect**
4. **La bonne information** (si vous la connaissez)

---

## 🏆 Merci de Tester JurisBot CI!

Votre participation est **cruciale** pour:
- ✅ Améliorer la précision du système
- ✅ Détecter les hallucinations
- ✅ Rendre l'app plus utile
- ✅ Valider la qualité juridique

**Chaque feedback compte!** 🙏

---

## 📚 Ressources Additionnelles

**Textes de Référence:**
- [Loi n° 2015-532](https://example.com) - Code du Travail
- [Convention Collective](https://example.com) - Interprofessionnelle
- [Décret n° 2022-31](https://example.com) - Télétravail

**Contact:**
- Équipe JurisBot CI
- Email: racine.yao@gmail.com

---

**Dernière mise à jour:** 10 juillet 2026  
**Version:** 1.0 Beta
