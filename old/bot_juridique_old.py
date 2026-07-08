# bot_juridique.py
import os
from langchain_community.document_loaders import TextLoader
from langchain_mistralai import MistralAIEmbeddings, ChatMistralAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# Configuration
# 1. Charger les variables depuis le fichier .env
load_dotenv()

# 2. Récupérer la clé de manière sécurisée
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Vérification de sécurité (optionnelle mais recommandée)
if not MISTRAL_API_KEY:
    raise ValueError("❌ Erreur: La clé MISTRAL_API_KEY est introuvable dans le fichier .env")

os.environ["MISTRAL_API_KEY"] = MISTRAL_API_KEY # Nécessaire pour LangChain
FILE_PATH = "code_du_travail_ci.md"

def build_rag_engine():
    """Charge le document, crée la base vectorielle et retourne le chain RAG et le retriever."""
    print("🧠 Chargement et indexation du Code du Travail...")
    
    loader = TextLoader(FILE_PATH, encoding="utf-8")
    documents = loader.load()
    
    # ✅ CORRECTIF 1 : Séparateurs enrichis pour respecter la structure juridique
    # On ajoute DECRET, ARRETE, LOI, CHAPITRE, SECTION, TITRE dans les séparateurs
    legal_separators = [
        "\nDECRET N°", "\nDECRET N° ", "\nARRETE N°", "\nARRETE N° ",
        "\nLOI N°", "\nLOI N° ", "\nORDONNANCE N°",
        "\n## ", "\n### ", 
        "\nArt. ", "\nARTICLE ", "\nART. ",
        "\nCHAPITRE ", "\nSECTION ", "\nTITRE ",
        "\n\n", "\n", " ", ""
    ]
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,      # ✅ Augmenté pour garder plus de contexte
        chunk_overlap=400,    # ✅ Augmenté pour éviter de couper les articles
        separators=legal_separators
    )
    splits = text_splitter.split_documents(documents)
    
    # ✅ CORRECTIF 2 : Enrichir chaque chunk avec des métadonnées de source
    for chunk in splits:
        content = chunk.page_content
        source_ref = "Code du Travail (Loi n° 2015-532)"  # Valeur par défaut
        
        # Détection automatique du décret/loi/convention dans le chunk ou les chunks voisins
        if "DECRET N°" in content or "DECRET N° " in content:
            import re
            match = re.search(r'DECRET\s+N°\s*(\d+-\d+)', content)
            if match:
                source_ref = f"Décret n° {match.group(1)}"
        elif "ARRETE N°" in content or "ARRETE N° " in content:
            import re
            match = re.search(r'ARRETE\s+N°\s*([\d-]+)', content)
            if match:
                source_ref = f"Arrêté n° {match.group(1)}"
        elif "CONVENTION COLLECTIVE" in content.upper():
            source_ref = "Convention Collective Interprofessionnelle"
        elif "LOI N°" in content:
            import re
            match = re.search(r'LOI\s+N°\s*([\d-]+)', content)
            if match:
                source_ref = f"Loi n° {match.group(1)}"
        
        # Injecter la source dans les métadonnées du chunk
        chunk.metadata["source_ref"] = source_ref
    
    print(f"✂️ Document découpé en {len(splits)} chunks avec métadonnées de source")
    
    # Création de la base vectorielle
    embeddings = MistralAIEmbeddings(model="mistral-embed")
    vectorstore = FAISS.from_documents(splits, embeddings)
    
    # ✅ CORRECTIF 3 : Augmenter k à 5 pour récupérer plus de contexte
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    # ✅ CORRECTIF 4 : System Prompt renforcé pour forcer la citation des numéros
    system_prompt = """
Tu es un assistant juridique expert en Droit du Travail Ivoirien (Loi n° 2015-532), 
les Décrets d'application et la Convention Collective Interprofessionnelle.

RÈGLES STRICTES ET NON NÉGOCIABLES :

1. RÉPONSE UNIQUEMENT BASÉE SUR LE CONTEXTE :
   Tu réponds UNIQUEMENT en te basant sur les extraits fournis dans le contexte.
   Si la réponse ne s'y trouve pas, réponds : "Aucune disposition légale trouvée dans le Code actuel. Consultez un inspecteur du travail."

2. CITATION OBLIGATOIRE DES SOURCES COMPLÈTES :
   Tu DOIS TOUJOURS citer la référence EXACTE et COMPLÈTE de chaque disposition utilisée :
   - Pour la Loi : "Article X de la Loi n° 2015-532 du 20 juillet 2015"
   - Pour un Décret : "Article X du Décret n° YY-YYY du [date]" (ex: Décret n° 96-200 du 7 mars 1996)
   - Pour la Convention Collective : "Article X de la Convention Collective Interprofessionnelle"
   - Pour un Arrêté : "Arrêté n° [numéro] du [date]"
   
   ⚠️ NE JAMAIS dire juste "selon le décret" ou "d'après la loi". TOUJOURS donner le NUMÉRO COMPLET.

3. FORMAT DE RÉPONSE :
   - Commence par une réponse claire et directe à la question
   - Développe avec les détails juridiques pertinents
   - Termine TOUJOURS par une section " Références juridiques :" listant toutes les sources citées avec leurs numéros complets

4. TON : Professionnel, neutre, pédagogique et strictement juridique.

5. PRÉCISION SUR LES DÉCRETS :
   Quand une question porte sur des détails techniques (durée de préavis, taux de majoration, quotité saisissable...), 
   ces informations se trouvent TOUJOURS dans un Décret d'application. Tu DOIS identifier et citer le numéro exact de ce décret.

Contexte juridique fourni :
{context}

Métadonnées des sources récupérées :
{sources_metadata}
"""
    
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{input}")])
    llm = ChatMistralAI(model="mistral-large-latest", temperature=0, timeout=120, max_retries=3)

    # ✅ CORRECTIF 5 : Fonction de formatage qui injecte les métadonnées de source
    def format_docs_with_sources(docs):
        # Construire une liste des sources uniques trouvées
        sources_found = set()
        for doc in docs:
            if "source_ref" in doc.metadata:
                sources_found.add(doc.metadata["source_ref"])
        
        sources_text = "\n".join([f"- {s}" for s in sources_found]) if sources_found else "Non identifiées"
        
        # Construire le contexte avec les sources
        context_parts = []
        for doc in docs:
            source_tag = f"[Source: {doc.metadata.get('source_ref', 'Inconnue')}]"
            context_parts.append(f"{source_tag}\n{doc.page_content}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Retourner un dictionnaire pour le LCEL
        return {"context": context, "sources_metadata": sources_text}

    # ✅ CORRECTIF 6 : Chaîne LCEL adaptée pour passer les métadonnées
    def prepare_input(query):
        docs = retriever.invoke(query)
        formatted = format_docs_with_sources(docs)
        return {
            "input": query,
            "context": formatted["context"],
            "sources_metadata": formatted["sources_metadata"]
        }

    # Chaîne simplifiée qui prend directement la query
    from langchain_core.runnables import RunnableLambda
    
    rag_chain = (
        RunnableLambda(prepare_input)
        | prompt
        | llm
        | StrOutputParser()
    )
    
    print("✅ Moteur RAG initialisé avec métadonnées de sources !")
    return rag_chain, retriever