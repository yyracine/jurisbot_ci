"""
🚀 Pipeline RAG complet et intégré

Combines:
- Document Ingestion (document_ingestion.py)
- FAISS/pgvector Management (faiss_manager.py, pgvector_manager.py)
- RAG Query Engine (bot_juridique.py)

Utilisation simple:
    from rag_pipeline import RAGPipeline

    # 1. Initialiser
    pipeline = RAGPipeline()

    # 2. Ingérer les documents
    pipeline.ingest_markdown("code_du_travail_ci.md")

    # 3. Répondre aux questions
    result = pipeline.query("Quels sont les droits en cas de licenciement ?")
"""

import os
import json
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from langchain_core.documents import Document
from langchain_mistralai import ChatMistralAI

from document_ingestion import DocumentIngestor, chunk_documents_legal
from faiss_manager import FAISSManager
from pgvector_manager import PGVectorManager, VectorStoreFactory

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Pipeline RAG complet et intégré.

    Gère:
    1. Ingestion de documents Markdown
    2. Indexation vectorielle (FAISS/pgvector)
    3. Recherche et génération de réponses
    """

    def __init__(
        self,
        backend: str = "auto",  # "faiss", "pgvector", ou "auto"
        index_name: str = "droit_travail_ci",
        chunk_size: int = 2000,
        chunk_overlap: int = 400
    ):
        """
        Args:
            backend: Backend vectoriel à utiliser
            index_name: Nom de l'index
            chunk_size: Taille des chunks
            chunk_overlap: Chevauchement entre chunks
        """
        self.index_name = index_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Déterminer le backend
        if backend == "auto":
            backend = VectorStoreFactory.get_backend_from_env()
            logger.info(f"🔍 Backend auto-détecté: {backend}")

        self.backend = backend

        # Initialiser les composants
        self.ingestor = DocumentIngestor()
        self.vectorstore = VectorStoreFactory.create(backend)
        self.llm = self._init_llm()
        self.retriever = None

        logger.info(f"🚀 RAGPipeline initialisé (backend: {backend})")

    def _init_llm(self) -> ChatMistralAI:
        """Initialise le modèle de langage"""
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("❌ MISTRAL_API_KEY manquante dans .env")

        return ChatMistralAI(
            model="mistral-large-latest",
            temperature=0,
            timeout=120,
            max_retries=3
        )

    def ingest_markdown(
        self,
        file_path: str,
        add_to_existing: bool = False
    ) -> Dict:
        """
        Ingère un fichier Markdown.

        Args:
            file_path: Chemin vers le fichier
            add_to_existing: Ajouter à l'index existant (True) ou créer nouveau (False)

        Returns:
            Dictionnaire avec les résultats
        """
        logger.info(f"📄 Ingestion de: {file_path}")

        try:
            # 1. Charger le fichier
            docs, metadata = self.ingestor.load_markdown_file(file_path)
            self.ingestor.record_ingestion([metadata])

            # 2. Découper en chunks
            chunks = chunk_documents_legal(docs, self.chunk_size, self.chunk_overlap)

            # 3. Indexer
            if add_to_existing and self.backend == "faiss":
                # Ajouter à l'index existant
                success = self.vectorstore.add_documents(chunks, self.index_name)
                logger.info(f"✅ Documents ajoutés à l'index existant")
            else:
                # Créer ou reconstruire l'index
                if self.backend == "pgvector":
                    ids = self.vectorstore.add_documents(chunks)
                    logger.info(f"✅ Documents ingérés dans pgvector ({len(ids)} IDs)")
                else:
                    path = self.vectorstore.create_index(chunks, self.index_name)
                    logger.info(f"✅ Index FAISS créé: {path}")

            # 4. Obtenir un retriever
            self.retriever = self.vectorstore.get_retriever(k=5, index_name=self.index_name)

            return {
                "status": "success",
                "file": file_path,
                "documents": len(docs),
                "chunks": len(chunks),
                "metadata": metadata.__dict__ if hasattr(metadata, '__dict__') else metadata
            }

        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            return {"status": "error", "message": str(e)}

    def ingest_directory(
        self,
        directory: str,
        pattern: str = "*.md",
        add_to_existing: bool = False
    ) -> Dict:
        """
        Ingère tous les fichiers Markdown d'un répertoire.

        Args:
            directory: Chemin du répertoire
            pattern: Pattern pour les fichiers
            add_to_existing: Ajouter à l'index existant

        Returns:
            Dictionnaire avec les résultats
        """
        logger.info(f"📁 Ingestion du répertoire: {directory}")

        try:
            docs, metadata_list = self.ingestor.load_markdown_directory(directory, pattern)
            self.ingestor.record_ingestion(metadata_list)

            # Découper et indexer
            chunks = chunk_documents_legal(docs, self.chunk_size, self.chunk_overlap)

            if add_to_existing and self.backend == "faiss":
                self.vectorstore.add_documents(chunks, self.index_name)
            else:
                if self.backend == "pgvector":
                    self.vectorstore.add_documents(chunks)
                else:
                    self.vectorstore.create_index(chunks, self.index_name)

            self.retriever = self.vectorstore.get_retriever(k=5, index_name=self.index_name)

            return {
                "status": "success",
                "directory": directory,
                "files": len(metadata_list),
                "documents": len(docs),
                "chunks": len(chunks)
            }

        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            return {"status": "error", "message": str(e)}

    def query(self, query: str, include_sources: bool = True) -> Dict:
        """
        Pose une question et obtient une réponse avec citations.

        Args:
            query: Question
            include_sources: Inclure les sources

        Returns:
            Dictionnaire avec réponse et sources
        """
        if not self.retriever:
            raise ValueError("❌ Aucun index chargé. Utilisez ingest_markdown() d'abord")

        logger.info(f"🔍 Requête: {query}")

        try:
            # 1. Récupérer les documents pertinents
            docs = self.retriever.invoke(query)

            # 2. Construire le contexte
            context_parts = []
            sources = []

            for doc in docs:
                source_ref = doc.metadata.get("source_ref", "Non spécifié")
                sources.append({
                    "ref": source_ref,
                    "type": doc.metadata.get("document_type", "unknown"),
                    "snippet": doc.page_content[:150].replace('\n', ' ') + "..."
                })
                context_parts.append(f"[{source_ref}]\n{doc.page_content}")

            context = "\n\n---\n\n".join(context_parts)

            # 3. Prompt système
            system_prompt = f"""
Tu es un assistant juridique expert en Droit du Travail Ivoirien.
Tu réponds UNIQUEMENT en te basant sur le contexte fourni.

RÈGLES CRITIQUES:
1. CITATIONS EXACTES: Citer le numéro d'article et la source complète
2. INTERDICTION: Ne JAMAIS halluciner des références
3. FALLBACK: Si la réponse n'existe pas, répondre: "Aucune disposition légale trouvée. Consultez un inspecteur du travail."
4. TON: Professionnel, neutre, pédagogique et strictement légal

Contexte juridique:
{context}
"""

            # 4. Appel au LLM
            logger.info("🤖 Appel au LLM...")
            messages = [("system", system_prompt), ("human", query)]
            response = self.llm.invoke(messages)
            answer = response.content

            logger.info("✅ Réponse reçue")

            return {
                "status": "success",
                "query": query,
                "answer": answer,
                "sources": sources if include_sources else None,
                "doc_count": len(docs)
            }

        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            return {"status": "error", "message": str(e)}

    def get_stats(self) -> Dict:
        """Retourne les statistiques du pipeline"""
        stats = {
            "backend": self.backend,
            "index_name": self.index_name,
            "ingestion": self.ingestor.get_ingestion_summary()
        }

        if self.backend == "faiss":
            stats["vectorstore"] = self.vectorstore.get_index_info()
        else:
            stats["vectorstore"] = self.vectorstore.get_stats()

        return stats

    def get_status(self) -> Dict:
        """Retourne l'état du pipeline"""
        return {
            "backend": self.backend,
            "retriever_loaded": self.retriever is not None,
            "llm_available": self.llm is not None,
            "ingestion_history": self.ingestor.get_ingestion_summary()
        }


if __name__ == "__main__":
    import sys

    # Exemple d'utilisation
    print("🚀 RAG Pipeline - Démo\n")

    # 1. Initialiser
    pipeline = RAGPipeline()

    # 2. Ingérer
    code_path = "code_du_travail_ci.md"
    if os.path.exists(code_path):
        result = pipeline.ingest_markdown(code_path)
        print("\n📊 Résultat d'ingestion:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # 3. Interroger
        test_queries = [
            "Quels sont les droits en cas de licenciement ?",
            "Combien de jours de congé annuel ?",
            "Quel est le salaire minimum ?",
        ]

        for q in test_queries:
            print(f"\n{'='*60}")
            result = pipeline.query(q)
            print(f"❓ Question: {q}")
            print(f"✅ Réponse:\n{result['answer']}")
            if result.get('sources'):
                print(f"\n📚 Sources ({len(result['sources'])}):")
                for src in result['sources'][:2]:
                    print(f"  - {src['ref']}")

        # 4. Stats
        print(f"\n{'='*60}")
        print("📊 Stats du pipeline:")
        stats = pipeline.get_stats()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    else:
        print(f"❌ Fichier non trouvé: {code_path}")
        sys.exit(1)
