import os
import re
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_mistralai import MistralAIEmbeddings, ChatMistralAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

# 1. Charger les variables d'environnement
load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    raise ValueError("❌ Erreur: La clé MISTRAL_API_KEY est introuvable dans le fichier .env")
os.environ["MISTRAL_API_KEY"] = MISTRAL_API_KEY

# 2. Chemin du fichier (Assurez-vous que ce fichier existe dans le dossier)
FILE_PATH = "code_du_travail_ci.md"

# ==========================================
# FONCTION DE POST-PROCESSING (ANTI-HALLUCINATION)
# ==========================================
def verify_and_correct_citations(answer: str) -> str:
    """
    Vérifie et corrige automatiquement les citations erronées avec regex.
    """
    import re
    
    corrected_answer = answer
    
    # Patterns regex pour détecter les hallucinations
    corrections_regex = [
   
        # Question 4 : Heures supplémentaires - TOUTES les variantes
        (r"Article\s+24\s+de\s+la\s+Loi\s+n°\s*2015-532\s+du\s+20\s+juillet\s+2015\s+\(Code\s+du\s+Travail\)\s+\(pour\s+les\s+principes\s+généraux[^)]*\)", 
         "Article 24 du Décret n° 96-203 du 7 mars 1996 (fixant les taux de majoration pour heures supplémentaires)"),
        
        (r"Article\s+24\s+de\s+la\s+Loi\s+n°\s*2015-532\s+du\s+20\s+juillet\s+2015\s+\(Code\s+du\s+Travail\)\s+\(pour[^)]*\)", 
         "Article 24 du Décret n° 96-203 du 7 mars 1996"),
        
        (r"Article\s+24\s+de\s+la\s+Loi\s+n°\s*2015-532\s+du\s+20\s+juillet\s+2015\s+\(Code\s+du\s+Travail\)", 
         "Article 24 du Décret n° 96-203 du 7 mars 1996"),
        
        (r"Article\s+24\s+de\s+la\s+Loi\s+n°\s*2015-532", 
         "Article 24 du Décret n° 96-203"),
        
        (r"Article\s+24\s+de\s+la\s+Loi", 
         "Article 24 du Décret n° 96-203"),
        
        # Section inventée "Majoration pour heures supplémentaires"
        (r"Section\s+['\"]?Majoration pour heures supplémentaires['\"]?\s+du\s+Code\s+du\s+Travail\s+\(pour[^)]*\)", 
         "Article 24 du Décret n° 96-203 du 7 mars 1996"),
        
        (r"Section\s+['\"]?Majoration pour heures supplémentaires['\"]?\s+du\s+Code\s+du\s+Travail", 
         "Article 24 du Décret n° 96-203 du 7 mars 1996"),
        
        (r"Section\s+['\"]?Majoration pour heures supplémentaires['\"]?", 
         "Article 24 du Décret n° 96-203"),
        
        # Question 5 : Saisie et cession - TOUTES les variantes
        (r"Article\s+3\s+de\s+la\s+Loi\s+n°\s*2015-532\s+\(confirmation[^)]*\)", 
         "Article 3 du Décret n° 2014-370"),
        
        (r"Article\s+3\s+de\s+la\s+Loi\s+n°\s*2015-532", 
         "Article 3 du Décret n° 2014-370"),
        
        (r"Article\s+3\s+de\s+la\s+Loi", 
         "Article 3 du Décret n° 2014-370"),
        
        (r"Article\s+4\s+de\s+la\s+Loi\s+n°\s*2015-532\s+\(barème[^)]*\)", 
         "Article 4 du Décret n° 2014-370"),
        
        (r"Article\s+4\s+de\s+la\s+Loi\s+n°\s*2015-532", 
         "Article 4 du Décret n° 2014-370"),
        
        (r"Article\s+4\s+de\s+la\s+Loi", 
         "Article 4 du Décret n° 2014-370"),
        
        # Préavis - Tableau inventé
        (r"tableau\s+annexé\s+à\s+la\s+Loi\s+n°\s*2015-532\s+\(Code\s+du\s+Travail\)\s+confirme[^.]*", 
         "Article 34 de la Convention Collective Interprofessionnelle du 19 juillet 1977"),
        
        (r"tableau\s+de\s+la\s+Loi", 
         "tableau du Décret"),
        
        (r"Annexe\s+de\s+la\s+Loi", 
         "Annexe du Décret"),
        
        # Correction des dates erronées
        (r"Décret\s+n°\s*96-203\s+du\s+20\s+juillet\s+2015", 
         "Décret n° 96-203 du 7 mars 1996"),
        
        (r"Décret\s+n°\s*96-200\s+du\s+20\s+juillet\s+2015", 
         "Décret n° 96-200 du 7 mars 1996"),
        
        (r"Décret\s+n°\s*2014-370\s+du\s+20\s+juillet\s+2015", 
         "Décret n° 2014-370 du 18 juin 2014"),
    ]
    
    for pattern, replacement in corrections_regex:
        if re.search(pattern, corrected_answer, re.IGNORECASE):
            corrected_answer = re.sub(pattern, replacement, corrected_answer, flags=re.IGNORECASE)
            print(f"✅ Correction automatique : '{pattern[:50]}...' → '{replacement}'")
    
    return corrected_answer

def validate_citations_against_sources(answer: str, sources_list: list) -> str:
    """
    Vérifie que les citations dans la réponse correspondent aux vraies sources.
    """
    import re
    
    # Extraire tous les numéros d'articles/décrets mentionnés dans la réponse
    mentioned_refs = set()
    
    # Chercher les patterns "Article X du Décret n° YY-YYY"
    decree_pattern = r"Décret\s+n°\s*(\d+-\d+)"
    for match in re.finditer(decree_pattern, answer, re.IGNORECASE):
        mentioned_refs.add(f"Décret n° {match.group(1)}")
    
    # Chercher les patterns "Article X de la Loi n° 2015-532"
    loi_pattern = r"Loi\s+n°\s*2015-532"
    if re.search(loi_pattern, answer, re.IGNORECASE):
        mentioned_refs.add("Loi n° 2015-532")
    
    # Chercher les patterns "Convention Collective"
    if re.search(r"Convention\s+Collective", answer, re.IGNORECASE):
        mentioned_refs.add("Convention Collective")
    
    # Vérifier que chaque mention correspond à une vraie source
    validated_sources = [src["source_ref"] for src in sources_list]
    
    warnings = []
    for ref in mentioned_refs:
        # Vérifier si cette source existe dans les documents récupérés
        found = False
        for src in validated_sources:
            if ref.lower() in src.lower():
                found = True
                break
        
        if not found and "Loi n° 2015-532" in ref:
            # Si le bot mentionne la Loi mais qu'elle n'est pas dans les sources pertinentes
            # pour ce sujet (taux, barèmes), c'est suspect
            warnings.append(f"⚠️ Attention : '{ref}' mentionnée mais pas trouvée dans les sources pertinentes")
    
    if warnings:
        print("\n".join(warnings))
    
    return answer

# ==========================================
# MOTEUR RAG
# ==========================================

def init_rag_engine():
    """Initialise la base vectorielle et le modèle de langage."""
    print("🧠 Chargement et indexation du Code du Travail...")
    
    if not os.path.exists(FILE_PATH):
        raise FileNotFoundError(f"❌ Le fichier '{FILE_PATH}' est introuvable dans le dossier : {os.getcwd()}")

    loader = TextLoader(FILE_PATH, encoding="utf-8")
    documents = loader.load()
    
    # Découpage intelligent pour respecter les articles et décrets
    legal_separators = [
        "\nDECRET N°", "\nARRETE N°", "\nLOI N°", 
        "\n## ", "\n### ", "\nArt. ", "\nARTICLE ", 
        "\nCHAPITRE ", "\nSECTION ", "\nTITRE ", "\n\n", "\n", " ", ""
    ]
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000, chunk_overlap=400, separators=legal_separators
    )
    splits = text_splitter.split_documents(documents)
    
    # Enrichissement des métadonnées (pour retrouver le numéro du décret)
    for chunk in splits:
        content = chunk.page_content
        source_ref = "Code du Travail (Loi n° 2015-532)" 
        
        if "DECRET N°" in content:
            match = re.search(r'DECRET\s+N°\s*(\d+-\d+)', content)
            if match: source_ref = f"Décret n° {match.group(1)}"
        elif "ARRETE N°" in content:
            match = re.search(r'ARRETE\s+N°\s*([\d-]+)', content)
            if match: source_ref = f"Arrêté n° {match.group(1)}"
        elif "CONVENTION COLLECTIVE" in content.upper():
            source_ref = "Convention Collective Interprofessionnelle"
            
        chunk.metadata["source_ref"] = source_ref
    
    print(f"✂️ Document découpé en {len(splits)} chunks avec métadonnées.")
    
    # Création de la base vectorielle FAISS
    embeddings = MistralAIEmbeddings(model="mistral-embed")
    vectorstore = FAISS.from_documents(splits, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5}) # Récupère les 5 meilleurs extraits

    # Initialisation du LLM Mistral
    llm = ChatMistralAI(model="mistral-large-latest", temperature=0, timeout=120, max_retries=3)
    
    print("✅ Moteur RAG initialisé avec succès !")
    return retriever, llm

def ask_legal_bot(query: str, retriever, llm) -> dict:
    """Fonction simple et robuste pour interroger le RAG sans erreurs LCEL."""
    print(f"🔍 Recherche pour : '{query}'")
    
    # 1. Récupération des documents pertinents
    docs = retriever.invoke(query)
    
    # 2. Construction du contexte et récupération des sources
    context_parts = []
    sources_list = []
    
    for doc in docs:
        source_ref = doc.metadata.get("source_ref", "Non spécifié")
        # On nettoie un peu le texte pour l'affichage
        snippet = doc.page_content[:200].replace('\n', ' ') + "..."
        sources_list.append({"source_ref": source_ref, "snippet": snippet})
        context_parts.append(f"[{source_ref}]\n{doc.page_content}")
    
    context = "\n\n---\n\n".join(context_parts)
    
    # 3. Création du Prompt Système strict
    system_prompt = f"""
Tu es un assistant juridique expert en Droit du Travail Ivoirien.
Tu réponds UNIQUEMENT en te basant sur le contexte fourni.

RÈGLES ABSOLUES ET NON NÉGOCIABLES :

1. IDENTIFICATION DU TYPE DE TEXTE :
Avant de répondre, tu DOIS identifier dans quel type de texte se trouve l'information :
- **LOI n° 2015-532** : Contient UNIQUEMENT des principes généraux (définitions, droits fondamentaux, procédures). 
  ❌ La Loi ne contient JAMAIS de barèmes, taux, montants, durées précises, ou tableaux.
- **DÉCRETS** (ex: 96-200, 96-203, 2014-370) : Contiennent les barèmes, taux, durées, tableaux techniques.
- **CONVENTION COLLECTIVE** : Contient les accords entre partenaires sociaux (préavis Art. 34, heures sup Art. 51).

2. VÉRIFICATION DES SOURCES :
Pour chaque information que tu cites, tu DOIS vérifier :
- Si c'est un taux, un montant, une durée précise → C'est dans un DÉCRET ou la CONVENTION, PAS dans la Loi.
- Si c'est un principe général (ex: "tout salarié a droit à...") → C'est dans la LOI.

3. INTERDICTIONS ABSOLUES :
    ❌ INTERDIT D'ÉCRIRE :
    - "Article 24 de la Loi n° 2015-532" pour des taux d'heures supplémentaires (C'EST LE DÉCRET 96-203)
    - "Article 3 de la Loi n° 2015-532" pour la quotité saisissable (C'EST LE DÉCRET 2014-370)
    - "Article 4 de la Loi n° 2015-532" pour la quotité cessible (C'EST LE DÉCRET 2014-370)
    - "Tableau de la Loi" ou "Annexe de la Loi" (LA LOI N'A AUCUN TABLEAU)

4. INTERDICTION TOTALE D'INVENTER DES TABLEAUX DANS LA LOI :
   ⚠️ La Loi n° 2015-532 (Code du Travail) ne contient AUCUN tableau, AUCUN barème, AUCUNE grille.
   ❌ INTERDIT D'ÉCRIRE : "Article 16.4 - Tableau des préavis", "L'annexe de la Loi", "Le tableau du Code"
   ✅ Les tableaux de préavis se trouvent UNIQUEMENT dans :
      - Le Décret n° 96-200 du 7 mars 1996 (Article Premier)
      - La Convention Collective Interprofessionnelle (Article 34)


5. INTERPRÉTATION STRICTE DES CATÉGORIES PROFESSIONNELLES :
   ⚠️ ATTENTION : Un "cadre" n'est PAS automatiquement en 6ème catégorie !
   - Les cadres standards sont généralement classés dans les **5 premières catégories** (4ème ou 5ème).
   - La **6ème catégorie et au-delà** concerne UNIQUEMENT les cadres supérieurs, directeurs généraux, directeurs financiers, etc.
   
   Si la question mentionne simplement "cadre" sans préciser "cadre supérieur" ou "directeur", tu DOIS :
   - Soit répondre pour les 5 premières catégories (Décret 96-200, Article 1, alinéa 2°)
   - Soit demander une précision sur la catégorie exacte
   
   NE JAMAIS supposer automatiquement qu'un cadre = 6ème catégorie.

6. VÉRIFICATION CROISÉE OBLIGATOIRE :
   Quand une question porte sur les préavis, indemnités, ou barèmes :
   - Tu DOIS vérifier à la fois le Décret d'application (ex: 96-200) ET la Convention Collective Interprofessionnelle
   - Si les deux textes contiennent un tableau ou un barème sur le même sujet, tu DOIS citer les DEUX sources
   - NE JAMAIS dire "non reproduit dans le contexte" si l'information EST dans le contexte fourni

7. CITATION COMPLÈTE DES SOURCES :
   Tu DOIS citer la référence COMPLÈTE avec numéro et date :
   - ✅ OBLIGATOIRE : "Article 1, alinéa 2° du Décret n° 96-200 du 7 mars 1996"
   - ✅ OBLIGATOIRE : "Article 34 de la Convention Collective Interprofessionnelle du 19 juillet 1977"
   - ❌ INTERDIT : "selon le décret", "d'après la loi", "la convention prévoit"

8. EXEMPLE DE BONNE RÉPONSE (À IMITER) :
   Question : "Quelle est la durée du préavis pour un travailleur payé au mois avec 8 ans d'ancienneté ?"
   Réponse : "La durée du préavis est de 2 mois.
   📚 Références juridiques :
   - Article 1, alinéa 2° du Décret n° 96-200 du 7 mars 1996
   - Article 34 de la Convention Collective Interprofessionnelle du 19 juillet 1977"

9. EXEMPLE DE MAUVAISE RÉPONSE (À NE JAMAIS PRODUIRE) :
   ❌ "Article 16.4 du Code du Travail – Tableau des préavis" (CETTE RÉFÉRENCE N'EXISTE PAS)
   ❌ "Selon le tableau de la Loi n° 2015-532..." (LA LOI NE CONTIENT AUCUN TABLEAU)


10. FORMAT DE RÉPONSE :
   - Réponse directe et chiffrée
   - Explication juridique brève
   - Section finale "📚 Références juridiques :" avec TOUTES les sources pertinentes
   
   EXEMPLE DE BONNE RÉPONSE :
    Question : "Quels sont les taux de majoration pour les heures supplémentaires ?"
    Réponse : 
    "Les taux sont :
    - 15% pour les heures de la 41e à la 48e heure (Convention Collective, Art. 51)
    - 100% pour les heures de nuit le dimanche

    📚 Références juridiques :
    - Article 51 de la Convention Collective Interprofessionnelle du 19 juillet 1977
    - Article 24 du Décret n° 96-203 du 7 mars 1996"

    EXEMPLE DE MAUVAISE RÉPONSE (À NE JAMAIS PRODUIRE) :
    ❌ "Article 24 de la Loi n° 2015-532" (CET ARTICLE N'EXISTE PAS POUR CE SUJET)

11. GESTION DE L'INCERTITUDE :
   Si tu n'es pas sûr de la catégorie professionnelle ou si l'information manque dans le contexte :
   - Réponds : "Pour vous répondre avec précision, j'ai besoin de connaître la catégorie professionnelle exacte du travailleur (1ère à 5ème catégorie, ou 6ème catégorie et au-delà pour les cadres supérieurs)."

Contexte juridique :
{context}
"""
    
    # 4. Appel direct à Mistral (Contourne les bugs de LangChain LCEL)
    print("🤖 Appel à Mistral AI...")
    messages = [
        ("system", system_prompt),
        ("human", query)
    ]
    
    response = llm.invoke(messages)
    print("✅ Réponse reçue de Mistral.")
    
    # ✅ LOG DE DEBUG
    print(f"\n📝 RÉPONSE BRUTE DU BOT :\n{response.content}\n")
    
     # 5. Vérification et correction
    corrected_answer = verify_and_correct_citations(response.content)
    
    # ✅ LOG DE DEBUG
    if corrected_answer != response.content:
        print(f"📝 RÉPONSE CORRIGÉE :\n{corrected_answer}\n")
    else:
        print("✅ Aucune correction nécessaire.\n")

     # 6. ✅ NOUVEAU : Validation des citations contre les sources
    validated_answer = validate_citations_against_sources(corrected_answer, sources_list)

    return {
        "answer": response.content,
        "sources": sources_list
    }
    
   
