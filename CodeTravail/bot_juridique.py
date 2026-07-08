import os
import re
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_mistralai import MistralAIEmbeddings, ChatMistralAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

# Recherche hybride (mots-clés BM25 + sémantique) pour corriger le défaut du
# retriever sémantique qui renvoie surtout des chunks de la Loi 2015-532 et
# "manque" les Décrets pertinents (problème observé sur préavis, cession).
from rank_bm25 import BM25Okapi

# 1. Charger les variables d'environnement
load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    raise ValueError("❌ Erreur: La clé MISTRAL_API_KEY est introuvable dans le fichier .env")
os.environ["MISTRAL_API_KEY"] = MISTRAL_API_KEY

# 2. Chemin du fichier
FILE_PATH = "code_du_travail_ci.md"

# ==========================================
# INDEX DES SOURCES OFFICIELLES (anti-hallucination)
# ==========================================
# Liste blanche des numéros de textes présents dans le corpus.
# Toute citation d'un numéro ABSENT de cette liste est une hallucination.
import re as _re
_TEXT_CACHE = None

def _load_raw_text() -> str:
    global _TEXT_CACHE
    if _TEXT_CACHE is None:
        with open(FILE_PATH, encoding="utf-8") as f:
            _TEXT_CACHE = f.read()
    return _TEXT_CACHE

def build_official_numbers_whitelist() -> set:
    """Extrait tous les numéros (LOI/DECRET/ARRETE N° XXX) du corpus."""
    txt = _load_raw_text()
    return set(_re.findall(r'(?:LOI|DECRET|ARRETE)\s+N°\s*([\d-]+)', txt))

# ==========================================
# FONCTION DE POST-PROCESSING (ANTI-HALLUCINATION)
# ==========================================
def verify_and_correct_citations(answer: str, retrieved_docs: list = None) -> str:
    """
    Validation anti-hallucination basée sur le contexte réellement récupéré.

    1. Neutralise les numéros de textes INVENTÉS (absents du corpus).
    2. Neutralise les attributions parasites à la Loi n° 2015-532 quand le
       contexte récupéré ne contient AUCUN chunk étiqueté Loi.
    3. Ne tente plus de réécrire à l'aveugle : on invalide ce qui n'est pas
       sourcé, plutôt que d'inventer une correction potentiellement fausse.
    """
    corrected = answer

    # --- 1. Détection des numéros officiels inventés ----------------------
    whitelist = build_official_numbers_whitelist()
    # Tous les "n° XXXX-XX" cités dans la réponse
    cited_numbers = set(_re.findall(r'n°\s*([\d-]+)', corrected, flags=_re.IGNORECASE))
    invented = cited_numbers - whitelist
    if invented:
        # On ajoute un avertissement clair en pied de réponse plutôt que de
        # réécrire la phrase (ce qui produisait des formulations non grammaticales).
        warning_nums = ", ".join(sorted(invented))
        print(f"🚨 Hallucination détectée : numéro(s) inventé(s) [{warning_nums}].")
        corrected += (
            f"\n\n⚠️ *Avertissement : la citation « n° {warning_nums} » ne figure "
            f"pas dans le Code du Travail fourni et a été identifiée comme non vérifiée. "
            f"Veuillez vous référer aux sources listées ci-dessous.*"
        )

    # --- 2. Attributions parasites à la Loi 2015-532 ----------------------
    # Si la réponse cite la Loi 2015-532 MAIS qu'aucun chunk récupéré n'est
    # étiqueté comme Loi, c'est une attribution fallacieuse.
    if retrieved_docs is not None and "2015-532" in corrected:
        docs_tags = " ".join(d.metadata.get("source_ref", "") for d in retrieved_docs).lower()
        has_loi_context = ("loi n° 2015-532" in docs_tags) or ("code du travail" in docs_tags and "décret" not in docs_tags)
        if not has_loi_context:
            # Le contexte est décret/convention-only : remplacer la Loi par le Décret dominant
            corrected = corrected.replace("Loi n° 2015-532", "texte réglementaire (Décret)")
            print("🚨 Attribution parasite à la Loi n° 2015-532 neutralisée.")

    return corrected

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
    
    # Découpage intelligent
    legal_separators = [
        "\nDECRET N°", "\nARRETE N°", "\nLOI N°", 
        "\n## ", "\n### ", "\nArt. ", "\nARTICLE ", 
        "\nCHAPITRE ", "\nSECTION ", "\nTITRE ", "\n\n", "\n", " ", ""
    ]
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000, chunk_overlap=400, separators=legal_separators
    )
    splits = text_splitter.split_documents(documents)
    
    # Enrichissement des métadonnées
    # IMPORTANT : on propage l'en-tête de Loi/Décret/Arrêté/Convention aux chunks
    # suivants. Sinon, un article isolé du Décret 96-203 (dont l'en-tête est
    # tombé dans le chunk précédent) hérite du libellé par défaut "Loi 2015-532",
    # ce qui pousse le LLM à citer la Loi à tort (source d'hallucinations).
    #
    # On capture AUSSI la date officielle du texte (ex: "du 30 mars 2017") pour
    # éviter que le LLM n'invente une date (hallucination observée en Q11).
    current_source = None
    in_convention = False   # Une fois entré dans la Convention Collective, on y reste :
                            # les mentions "Loi 2015-532" qui suivent sont des RENVOIS
                            # internes (ex: "Conformément à l'art. 32.7 du Code"), pas
                            # des en-têtes de texte. Sans ce verrouillage, les articles
                            # 39/40/42 de la Convention étaient à tort étiquetés "Loi".
    header_re = re.compile(
        r'(LOI|DECRET|ARRETE)\s+N°\s*([\d-]+)\s+DU\s+(\d{1,2}\s+\w+\s+\d{4})',
        flags=re.IGNORECASE,
    )
    # La vraie Convention Collective commence à "# LA CONVENTION COLLECTIVE
    # INTERPROFESSIONNELLE". On évite de matcher les simples chapitres internes
    # à la Loi (ex: "CONVENTIONS COLLECTIVES DE TRAVAIL" ligne 2065).
    conv_re = re.compile(
        r'LA\s+CONVENTION COLLECTIVE INTERPROFESSIONNELLE',
        flags=re.IGNORECASE,
    )
    for chunk in splits:
        content = chunk.page_content

        # 0. Verrouillage du bloc Convention Collective
        if conv_re.search(content):
            in_convention = True

        if in_convention:
            # Dans la Convention : on reste étiqueté "Convention Collective", même
            # si le chunk mentionne "Loi n° 2015-532" (ce sont des renvois, pas un
            # nouvel en-tête). On ne change que si un VRAI nouvel en-tête de Décret
            # ou d'Arrêté apparaît (rare après la Convention).
            current_source = "Convention Collective Interprofessionnelle du 19 juillet 1977"
            m_decret = re.search(r'(?:^|\n)\s*#?\s*DECRET\s+N°\s*([\d-]+)', content)
            m_arrete = re.search(r'(?:^|\n)\s*#?\s*ARRETE\s+N°\s*([\d-]+)', content)
            if m_decret:
                current_source = f"Décret n° {m_decret.group(1)}"
                in_convention = False
            elif m_arrete:
                current_source = f"Arrêté n° {m_arrete.group(1)}"
                in_convention = False
        else:
            # 1. En-tête officiel LOI/DECRET/ARRETE avec numéro + date (priorité)
            m = header_re.search(content)
            if m:
                kind = m.group(1).upper()
                num = m.group(2)
                date = m.group(3).lower()
                kind_word = {"LOI": "Loi", "DECRET": "Décret", "ARRETE": "Arrêté"}[kind]
                current_source = f"{kind_word} n° {num} du {date}"

        # 3. Étiqueter : source propagée si rien de nouveau détecté
        chunk.metadata["source_ref"] = current_source or "Code du Travail (Loi n° 2015-532 du 20 juillet 2015)"


    print(f"✂️ Document découpé en {len(splits)} chunks avec métadonnées.")

    embeddings = MistralAIEmbeddings(model="mistral-embed")
    vectorstore = FAISS.from_documents(splits, embeddings)
    # MMR = Maximum Marginal Relevance : favorise la DIVERSITÉ des résultats.
    # On récupère un pool large (fetch_k=20) puis on sélectionne les 8 chunks les
    # plus pertinents ET les moins redondants. Cela évite que le retriever ne
    # renvoie 5 chunks quasi-identiques de la même Loi alors qu'un Décret plus
    # précis existe ailleurs (problème observé sur "période d'essai", "préavis").
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 6, "fetch_k": 20},
    )

    # Index BM25 pour la recherche par mots-clés (complément du sémantique).
    # Tokenisation simple : on découpe sur les non-mots, en minuscules.
    tokenized_corpus = [re.findall(r'\w+', doc.page_content.lower()) for doc in splits]
    bm25 = BM25Okapi(tokenized_corpus)

    llm = ChatMistralAI(model="mistral-large-latest", temperature=0, timeout=120, max_retries=3)

    print("✅ Moteur RAG initialisé avec succès !")
    return retriever, llm, {"bm25": bm25, "splits": splits}

def ask_legal_bot(query: str, retriever, llm, hybrid=None) -> dict:
    """Fonction simple et robuste pour interroger le RAG.

    Si ``hybrid`` (dict {bm25, splits}) est fourni, on fusionne les résultats
    du retriever sémantique (FAISS/MMR) et du BM25 (mots-clés) : c'est la
    recherche hybride, qui corrige le cas où le sémantique "manque" un Décret
    pertinent (ex. Décret 96-200 sur le préavis) à cause du bruit de la Loi.
    """
    print(f"🔍 Recherche pour : '{query}'")

    # 1. Récupération des documents (sémantique)
    docs = list(retriever.invoke(query))

    # 1.a Recherche hybride : ajouter les meilleurs chunks BM25 (mots-clés)
    if hybrid is not None and "bm25" in hybrid and "splits" in hybrid:
        bm25 = hybrid["bm25"]
        splits = hybrid["splits"]
        tokens = re.findall(r'\w+', query.lower())
        bm25_scores = bm25.get_scores(tokens)
        # Top 8 BM25 : on prend un pool plus large pour ne pas manquer le chunk
        # qui contient la valeur chiffrée exacte (ex. taux de prime d'ancienneté),
        # même quand le sémantique renvoie plusieurs chunks "voisins" moins précis.
        top_bm25_idx = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:8]
        existing_ids = {id(d) for d in docs}
        for idx in top_bm25_idx:
            doc = splits[idx]
            if id(doc) not in existing_ids and bm25_scores[idx] > 0:
                docs.append(doc)
                existing_ids.add(id(doc))
        # Limiter à 10 chunks au total après fusion (le reranking ci-dessous
        # remettra en tête les sources les plus pertinentes).
        docs = docs[:10]

    # 1.b Reranking par type de source (anti-hallucination)
    # Les valeurs chiffrées (taux, durées, barèmes) sont fixées par les DÉCRETS
    # et la CONVENTION COLLECTIVE, pas par la Loi (principes généraux). On place
    # donc les Décrets/Arrêtés/Conventions en TÊTE du contexte, car le LLM a
    # tendance à citer prioritairement les premiers extraits. Sans ce reranking,
    # le retriever renvoie majoritairement des chunks de la Loi 2015-532 (qui
    # couvre tous les sujets de façon générale) et le LLM cite la Loi à tort.
    def _source_rank(source_ref: str) -> int:
        s = source_ref.lower()
        if "décret" in s or "decret" in s:
            return 0   # priorité maximale : contient les valeurs chiffrées
        if "convention collective" in s:
            return 1
        if "arrêté" in s or "arrete" in s:
            return 2
        if "loi n° 2015-532" in s:
            return 3   # Code du Travail : principes généraux
        return 4       # autres lois

    docs_sorted = sorted(docs, key=lambda d: _source_rank(d.metadata.get("source_ref", "")))

    # 2. Construction du contexte
    context_parts = []
    sources_list = []

    for doc in docs_sorted:
        source_ref = doc.metadata.get("source_ref", "Non spécifié")
        snippet = doc.page_content[:200].replace('\n', ' ') + "..."
        sources_list.append({"source_ref": source_ref, "snippet": snippet})
        context_parts.append(f"[{source_ref}]\n{doc.page_content}")
    
    context = "\n\n---\n\n".join(context_parts)
    
    # 3. Prompt système
    system_prompt = f"""
Tu es un assistant juridique expert en Droit du Travail Ivoirien.
Tu réponds UNIQUEMENT en te basant sur le contexte fourni.

RÈGLES ABSOLUES :

1. RÔLE DES TEXTES (HIÉRARCHIE STRICTE) :
   - La Loi n° 2015-532 (Code du Travail) ne pose que les PRINCIPES GÉNÉRAUX.
   - Les modalités chiffrées (taux, durées, barèmes, montants) sont fixées par
     des DÉCRETS d'application ou par la CONVENTION COLLECTIVE.
   - RÈGLE DE PRIORITÉ : si le contexte contient un DÉCRET ou une CONVENTION
     qui fixe une valeur chiffrée, tu DOIS citer CE Décret/Cette Convention,
     et NON la Loi n° 2015-532 qui n'est qu'un principe général.

2. CITATIONS EXACTES OBLIGATOIRES (copie littérale) :
   Chaque extrait du contexte commence par une étiquette [source] indiquant
   l'ORIGINE EXACTE. Tu DOIS reprendre cette étiquette TELLE QUELLE.
   Exemples d'étiquettes valides dans ce contexte :
   - [Décret n° 96-203 du 7 mars 1996]
   - [Décret n° 2017-210 du 30 mars 2017]
   - [Convention Collective Interprofessionnelle du 19 juillet 1977]
   - [Loi n° 2015-532 du 20 juillet 2015]

3. INTERDICTION FORMELLE D'INVENTER :
   ❌ N'invente JAMAIS de numéro de Décret/Loi/Arrêté qui n'est pas dans une
      étiquette [source] du contexte.
   ❌ N'invente JAMAIS de date. Si le contexte dit "du 30 mars 2017", écris
      "du 30 mars 2017", pas une autre date.
   ❌ N'effectue JAMAIS de calcul ni d'addition pour déduire une durée. Si le
      contexte dit "3 mois renouvelables une fois", réponds "3 mois
      renouvelables une fois" — n'écris PAS "6 mois au total" ni aucune valeur
      résultant d'une addition que le contexte ne contient pas mot pour mot.
   ❌ Ne mentionne pas la "Loi n° 2015-532" pour citer un taux, une durée,
      un barème ou un montant (heures sup, durée du travail, travail de nuit,
      période d'essai, préavis, indemnité de licenciement, SMIG, saisie/cession).
   ✅ Pour ces sujets, cite UNIQUEMENT le DÉCRET ou la CONVENTION COLLECTIVE
      présents dans le contexte.

4. Si tu n'as pas l'information exacte dans le contexte, réponds :
   "Aucune disposition légale trouvée dans le Code actuel. Consultez un inspecteur du travail."

Contexte juridique :
{context}
"""
    
    # 4. Appel à Mistral
    print("🤖 Appel à Mistral AI...")
    messages = [("system", system_prompt), ("human", query)]
    response = llm.invoke(messages)
    print("✅ Réponse reçue de Mistral.")
    
    # 5. Vérification et correction automatique
    corrected_answer = verify_and_correct_citations(response.content, retrieved_docs=docs_sorted)
    
    print(f"\n📝 RÉPONSE CORRIGÉE :\n{corrected_answer}\n")
    
    # LOG CRITIQUE : Voir ce qui est retourné
    print(f"🔍 VALEUR QUI VA ÊTRE RETOURNÉE : {corrected_answer[:100]}...\n")
    
    # LOG ULTRA-PRÉCIS : Afficher exactement ce qui va être retourné
    print(f"🎯 VALEUR EXACTE RETOURNÉE (100 premiers chars) : '{corrected_answer[:100]}'")
    print(f"🎯 CONTIENT 'Décret n° 96-203' ? {'Article 24 du Décret n° 96-203' in corrected_answer}")
    print(f"🎯 CONTIENT 'Loi n° 2015-532' ? {'Article 24 de la Loi n° 2015-532' in corrected_answer}\n")
    

    return {
        "answer": corrected_answer,  # ← ✅ C'EST ÇA QU'IL FAUT !
        "sources": sources_list
    }