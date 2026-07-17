import os
import re
import unicodedata
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_mistralai import MistralAIEmbeddings, ChatMistralAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

# 1. Charger les variables d'environnement
try:
    import streamlit as st
    MISTRAL_API_KEY = st.secrets.get("mistral_api_key")
except (ImportError, AttributeError, KeyError):
    MISTRAL_API_KEY = None

if not MISTRAL_API_KEY:
    load_dotenv()
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

if not MISTRAL_API_KEY:
    raise ValueError(
        "❌ Erreur: La clé MISTRAL_API_KEY est introuvable.\n"
        "Pour Streamlit Cloud: Allez à 'Settings' → 'Secrets' et ajoutez:\n"
        "mistral_api_key = 'votre-clé-ici'\n"
        "Pour développement local: Créez un fichier .env avec:\n"
        "MISTRAL_API_KEY=votre-clé-ici"
    )
os.environ["MISTRAL_API_KEY"] = MISTRAL_API_KEY

# 2. Chemin du fichier
FILE_PATH = "code_du_travail_ci.md"

# ==========================================
# FONCTION DE POST-PROCESSING (ANTI-HALLUCINATION)
# ==========================================
def verify_and_correct_citations(answer: str) -> str:
    """
    Version simplifiée : remplacements directs sans regex complexes.
    """
    corrected = answer

    # Liste de tuples (texte_faux, texte_vrai)
    corrections = [
        # Heures supplémentaires
        ("Article 24 de la Loi n° 2015-532 du 20 juillet 2015", "Article 24 du Décret n° 96-203 du 7 mars 1996"),
        ("Article 24 de la Loi n° 2015-532", "Article 24 du Décret n° 96-203"),
        ("Article 24 de la Loi", "Article 24 du Décret n° 96-203"),

        # Saisie et cession
        ("Article 3 de la Loi n° 2015-532", "Article 3 du Décret n° 2014-370"),
        ("Article 3 de la Loi", "Article 3 du Décret n° 2014-370"),
        ("Article 4 de la Loi n° 2015-532", "Article 4 du Décret n° 2014-370"),
        ("Article 4 de la Loi", "Article 4 du Décret n° 2014-370"),

        # Dates erronées
        ("Décret n° 96-203 du 20 juillet 2015", "Décret n° 96-203 du 7 mars 1996"),
        ("Décret n° 96-200 du 20 juillet 2015", "Décret n° 96-200 du 7 mars 1996"),
        ("Décret n° 2014-370 du 20 juillet 2015", "Décret n° 2014-370 du 18 juin 2014"),

        # Préavis
        ("tableau de la Loi", "tableau du Décret"),
        ("Annexe de la Loi", "Annexe du Décret"),

        # Congés payés (Article 25.2) - Hallucination correction
        ("Article 25.2 de la Loi n° 2015-532 et Convention Collective Interprofessionnelle du 19 juillet 1977", "Article 25.2 de la Loi n° 2015-532 (modifié par Ordonnance n° 2021-902 du 22 décembre 2021)"),
        ("Article 25.2 et Convention Collective Interprofessionnelle du 19 juillet 1977", "Article 25.2 de la Loi n° 2015-532 (modifié par Ordonnance n° 2021-902 du 22 décembre 2021)"),
    ]

    for wrong, correct in corrections:
        if wrong in corrected:
            corrected = corrected.replace(wrong, correct)
            print(f"✅ Correction : '{wrong}' → '{correct}'")

    return corrected


def clean_fallback_response(answer: str, query: str) -> str:
    """
    Nettoie les réponses de fallback pour éliminer les hallucinations.

    Si la réponse est un fallback (commence par "Aucune disposition"),
    elle doit rester simple et ne pas mentionner les mots-clés de la question.
    """
    if "Aucune disposition" not in answer:
        return answer  # Ce n'est pas un fallback, retourner tel quel

    # C'est un fallback : vérifier qu'il n'y a pas de hallucinations
    # (mots-clés spécifiques de la question)

    # Mots-clés dangereux à éviter dans un fallback
    # Ignorer "Code du Travail" (terme légal) et autres contextes légaux
    dangerous_keywords = [
        "python", "programmer", "coding", "fonction", "algorithme",
        "riche", "investir", "bourse", "placement", "fortune",
        "restaurant", "pizza", "cuisine", "manger", "nourriture",
        "montagne", "sommet", "everest", "kilimanjaro",
        "einstein", "physique", "relativite", "energie"
    ]

    # Vérifier si des mots-clés dangereux apparaissent dans la réponse
    answer_lower = answer.lower()
    detected_keywords = []

    # Exceptions : termes légaux qui peuvent contenir des mots-clés
    exceptions = [
        "code du travail",
        "code de travail",
        "code civil",
        "code pénal"
    ]

    for keyword in dangerous_keywords:
        # Chercher le mot exact (entouré d'espaces ou ponctuation)
        if re.search(rf'\b{re.escape(keyword)}\b', answer_lower):
            # Vérifier que ce n'est pas dans une exception
            is_exception = False
            for exc in exceptions:
                if exc in answer_lower and keyword in exc:
                    is_exception = True
                    break

            if not is_exception:
                detected_keywords.append(keyword)

    if detected_keywords:
        # Hallucination détectée : remplacer par la réponse standard stricte
        print(f"⚠️ Hallucination détectée dans fallback: {detected_keywords}")
        return "Aucune disposition légale trouvée dans le Code du Travail Ivoirien. Je suis spécialisé dans le droit du travail ivoirien uniquement."

    # Vérifier que le fallback est court et direct (pas de reformulation)
    if len(answer) > 300:
        # Le fallback est trop long, probablement une reformulation
        print("⚠️ Fallback trop long, possibilité de reformulation")
        return "Aucune disposition légale trouvée dans le Code du Travail Ivoirien. Je suis spécialisé dans le droit du travail ivoirien uniquement."

    return answer

# ==========================================
# MOTEUR RAG
# ==========================================
def _strip_accents(s: str) -> str:
    """Supprime les accents (utilitaire pour les comparaisons insensibles)."""
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


# Nom de mois (sans accent, tel qu'il apparaît après lower()) -> forme française correcte.
_MONTH_FIX = {
    "janvier": "janvier", "fevrier": "février", "mars": "mars", "avril": "avril",
    "mai": "mai", "juin": "juin", "juillet": "juillet", "aout": "août",
    "septembre": "septembre", "octobre": "octobre", "novembre": "novembre",
    "decembre": "décembre", "dec": "décembre",
    "janv": "janvier", "fevr": "février", "avr": "avril", "juil": "juillet",
    "sept": "septembre", "decemb": "décembre",
}


def _normalize_date(date_str: str) -> str:
    """Restaure les accents des noms de mois et uniformise le format de date."""
    s = date_str.lower()
    for abbr, full in _MONTH_FIX.items():
        # remplace le token mois (mot entier)
        s = re.sub(rf'\b{re.escape(abbr)}\b', full, s)
    return s


def _detect_source_ref(header: str) -> str:
    """
    Parse un TITRE de section H1 et renvoie un libellé court et propre :
        'Décret n° 96-203 du 7 mars 1996'
        'Loi n° 2015-532 du 20 juillet 2015'
        'Arrêté n° 2015-855 du 30 décembre 2015'
        'Convention Collective Interprofessionnelle du 19 juillet 1977'
    Retourne '' si le type de texte n'est pas reconnu.
    """
    norm = _strip_accents(header).upper()

    # --- Convention Collective Interprofessionnelle (CCNI, sans numéro) ---
    if "CONVENTION COLLECTIVE INTERPROFESSIONNELLE" in norm:
        return "Convention Collective Interprofessionnelle du 19 juillet 1977"

    # --- Loi / Décret / Arrêté : on extrait type + numéro + date ---
    type_map = {"LOI": "Loi", "DECRET": "Décret", "ARRETE": "Arrêté"}
    for raw_type, label in type_map.items():
        if raw_type in norm:
            # Numéro : 'N° 96-203' (digits-digits) OU 'N° 2250' / 'N° 009 MEMEASS/CAB'
            # (arrêtés au format simple ou avec préfixe ministériel)
            num_m = re.search(r'N°\s*([\dA-Z/-]+(?:\s+[A-Z/]+)?)', header, re.IGNORECASE)
            # On épure : on garde le numéro principal (digits + éventuel suffixe ministériel)
            # Date : 'DU 7 MARS 1996' ou 'DU 30 SEPTEMBRE 2010'
            date_m = re.search(
                r'(\d{1,2}(?:ER)?\s+[A-ZÉÛÀÔÈÉÙÎÇÂÊŒ]+\.?\s+\d{4})',
                header, re.IGNORECASE
            )
            if not num_m:
                continue
            # Nettoyage du numéro : on stoppe avant le 'DU' qui annonce la date
            # (ex: '2250 DU' -> '2250', '009 MEMEASS/CAB' reste tel quel).
            num_raw = re.split(r'\s+DU\b', num_m.group(1).strip(), flags=re.IGNORECASE)[0]
            ref = f"{label} n° {num_raw}"
            if date_m:
                ref += f" du {_normalize_date(date_m.group(1))}"
            return ref

    return ""


def _split_by_section(documents):
    """
    Pré-découpe le document en grandes sections juridiques (Loi / Décret /
    Arrêté / Convention Collective), identifiées par un titre H1 Markdown :
        # LOI N° ... / # DECRET N° ... / # ARRETE N° ... / # CONVENTION COLLECTIVE ...
    Chaque section hérite du 'source_ref' de son titre H1, propagé ensuite à
    tous les chunks enfants issus du redécoupage.
    Le sommaire (lignes 'DECRET N° ...' sans '#') est ignoré car non préfixé.
    Retourne une liste de tuples (texte_section, source_ref).
    """
    full_text = "\n".join(d.page_content for d in documents)

    # Titre de section H1 : '# LOI/DECRET/ARRETE N° <num>' ou
    # '# ... CONVENTION COLLECTIVE INTERPROFESSIONNELLE ...' (la CCNI n'a pas
    # de numéro dans son titre, d'où une branche dédiée).
    header_pattern = re.compile(
        r'^#\s+(?:'
        r'(?:LOI|DECRET|ARRETE)\s+N°\s*\d'          # Loi / Décret / Arrêté numérotés
        r'|.*CONVENTION COLLECTIVE INTERPROFESSIONNELLE'  # CCNI (pas de N°)
        r')',
        re.MULTILINE | re.IGNORECASE
    )

    matches = list(header_pattern.finditer(full_text))
    if not matches:
        # Pas de structure détectée : tout dans une seule section générique
        return [(full_text, "Code du Travail (Loi n° 2015-532)")]

    sections = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        section_text = full_text[start:end].strip()

        # Le titre de section (première ligne) contient le numéro du texte
        source_ref = _detect_source_ref(section_text.split("\n", 1)[0])
        if not source_ref:
            source_ref = section_text.split("\n", 1)[0].lstrip("# ").strip()
        sections.append((section_text, source_ref))

    # Préambule (contenu avant la première section H1 détectée)
    if matches[0].start() > 0:
        pre_text = full_text[:matches[0].start()].strip()
        if pre_text:
            sections.insert(0, (pre_text, "Code du Travail (Préambule / Sommaire)"))

    return sections


def init_rag_engine():
    """Initialise la base vectorielle et le modèle de langage."""
    print("🧠 Chargement et indexation du Code du Travail...")

    if not os.path.exists(FILE_PATH):
        raise FileNotFoundError(f"❌ Le fichier '{FILE_PATH}' est introuvable dans le dossier : {os.getcwd()}")

    loader = TextLoader(FILE_PATH, encoding="utf-8")
    documents = loader.load()

    # 1. Pré-découpage en sections juridiques (chaque section = 1 source_ref)
    sections = _split_by_section(documents)
    print(f"📑 {len(sections)} sections juridiques détectées.")

    # 2. Découpage intelligent de chaque section
    legal_separators = [
        "\n## ", "\n### ", "\nArt. ", "\nARTICLE ",
        "\nCHAPITRE ", "\nSECTION ", "\nTITRE ", "\n\n", "\n", " ", ""
    ]
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000, chunk_overlap=400, separators=legal_separators
    )

    from langchain_core.documents import Document
    splits = []
    for section_text, source_ref in sections:
        sub_docs = text_splitter.split_documents(
            [Document(page_content=section_text)]
        )
        for doc in sub_docs:
            doc.metadata["source_ref"] = source_ref  # propagation parent → enfant
            splits.append(doc)

    print(f"✂️ Document découpé en {len(splits)} chunks avec métadonnées.")
    
    embeddings = MistralAIEmbeddings(model="mistral-embed")
    vectorstore = FAISS.from_documents(splits, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    llm = ChatMistralAI(model="mistral-large-latest", temperature=0, timeout=120, max_retries=3)
    
    print("✅ Moteur RAG initialisé avec succès !")
    return retriever, llm

def ask_legal_bot(query: str, retriever, llm) -> dict:
    """Fonction simple et robuste pour interroger le RAG."""
    print(f"🔍 Recherche pour : '{query}'")

    # 1. Récupération des documents
    docs = retriever.invoke(query)

    # 2. Construction du contexte
    context_parts = []
    sources_list = []

    for doc in docs:
        source_ref = doc.metadata.get("source_ref", "Non spécifié")
        snippet = doc.page_content[:200].replace('\n', ' ') + "..."
        sources_list.append({"source_ref": source_ref, "snippet": snippet})
        context_parts.append(f"[{source_ref}]\n{doc.page_content}")

    context = "\n\n---\n\n".join(context_parts)

    # 3. Prompt système AMÉLIORÉ avec fallback strict
    system_prompt = f"""
Tu es un assistant juridique expert en Droit du Travail Ivoirien.
Tu réponds UNIQUEMENT en te basant sur le contexte fourni.

RÈGLES ABSOLUES :

1. CITATIONS EXACTES OBLIGATOIRES :
   Pour les heures supplémentaires, tu DOIS citer EXACTEMENT :
   - "Article 24 du Décret n° 96-203 du 7 mars 1996" (pour les taux de majoration)
   - "Article 51 de la Convention Collective Interprofessionnelle du 19 juillet 1977" (pour les majorations conventionnelles)

   Pour les congés payés (Articles 25.x), tu DOIS citer :
   - "Article 25.x de la Loi n° 2015-532 (modifié par Ordonnance n° 2021-902 du 22 décembre 2021)"
   ❌ NE JAMAIS mixer les congés payés (Article 25) avec la Convention Collective du 19 juillet 1977

   ❌ INTERDIT d'écrire : "Dispositions générales sur les heures supplémentaires", "Code du Travail (extrait fourni)", "Ibid."
   ✅ OBLIGATOIRE d'écrire les numéros d'articles COMPLETS avec dates.

2. INTERDICTION FORMELLE :
   ❌ Ne mentionne JAMAIS la "Loi n° 2015-532" pour les heures supplémentaires, préavis, saisie/cession.
   ✅ Pour ces sujets, cite UNIQUEMENT les DÉCRETS et la CONVENTION COLLECTIVE.
   ⚠️ EXCEPTION : Les CONGÉS PAYÉS (Article 25) proviennent de la Loi n° 2015-532, cite-la TOUJOURS pour Article 25.

3. FALLBACK STRICT - RÉPONSE OBLIGATOIRE POUR QUESTIONS HORS-SUJET :

   ⚠️ Si la question ne concerne PAS le droit du travail ivoirien :

   ❌ NE JAMAIS reformuler la question
   ❌ NE JAMAIS mentionner les mots-clés spécifiques de la question (ex: "Python", "programmer", "riche", "investir", "relativity", "montagne", "restaurant")
   ❌ NE PAS écrire de phrases contenant le sujet de la question

   ✅ RÉPONDRE EXACTEMENT CECI (mot pour mot) :
   "Aucune disposition légale trouvée dans le Code du Travail Ivoirien. Je suis spécialisé dans le droit du travail ivoirien uniquement."

   C'est la SEULE réponse acceptable pour les questions hors-sujet. Ne pas ajouter d'explication supplémentaire.

4. Si tu n'as pas l'information exacte sur une question juridique, réponds : "Aucune disposition légale trouvée."

Contexte juridique :
{context}
"""
    
    # 4. Appel à Mistral
    print("🤖 Appel à Mistral AI...")
    messages = [("system", system_prompt), ("human", query)]
    response = llm.invoke(messages)
    print("✅ Réponse reçue de Mistral.")

    # 5. Vérification et correction automatique des citations
    corrected_answer = verify_and_correct_citations(response.content)

    # 6. Nettoyage des fallbacks pour éliminer les hallucinations
    final_answer = clean_fallback_response(corrected_answer, query)

    print(f"\n📝 RÉPONSE FINALE :\n{final_answer}\n")

    # LOG CRITIQUE : Voir ce qui est retourné
    print(f"🔍 VALEUR QUI VA ÊTRE RETOURNÉE : {final_answer[:100]}...\n")

    return {
        "answer": final_answer,  # ← ✅ RÉPONSE FINALE NETTOYÉE
        "sources": sources_list
    }