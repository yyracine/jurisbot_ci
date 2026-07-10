"""
🌊 Gestionnaire pgvector pour le RAG - Production Ready

Support pour Supabase pgvector:
- Connexion à PostgreSQL avec pgvector
- Ingestion d'embeddings
- Recherche vectorielle
- Métadonnées enrichies
- Compatible avec l'interface FAISSManager (swap facile)
"""

import os
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

try:
    from langchain_community.vectorstores import SupabaseVectorStore
    from langchain_mistralai import MistralAIEmbeddings
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ Supabase/pgvector non disponible. Installer: pip install supabase langchain-community")

from langchain_core.documents import Document

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PGVectorManager:
    """
    Gestionnaire pour pgvector dans Supabase.

    Interface compatible avec FAISSManager pour swap facile:
    - Créer/charger des espaces vectoriels
    - Ajouter des documents
    - Recherche vectorielle
    - Métadonnées enrichies
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        embedding_model: str = "mistral-embed",
        table_name: str = "documents"
    ):
        """
        Args:
            supabase_url: URL Supabase (ou SUPABASE_URL env var)
            supabase_key: Clé API Supabase (ou SUPABASE_KEY env var)
            embedding_model: Modèle pour les embeddings
            table_name: Nom de la table dans PostgreSQL
        """
        if not SUPABASE_AVAILABLE:
            raise ImportError(
                "❌ Supabase/pgvector non disponible.\n"
                "Installer: pip install supabase langchain-community python-postgrest"
            )

        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
        self.embedding_model_name = embedding_model
        self.table_name = table_name

        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "❌ Clés Supabase manquantes.\n"
                "Configurer: SUPABASE_URL et SUPABASE_KEY"
            )

        # Initialiser les embeddings
        if "MISTRAL_API_KEY" not in os.environ:
            raise ValueError("❌ MISTRAL_API_KEY manquante dans .env")

        self.embeddings = MistralAIEmbeddings(model=embedding_model)

        try:
            from supabase import create_client
            self.client = create_client(self.supabase_url, self.supabase_key)
            self.vectorstore = None
            logger.info(f"🚀 PGVectorManager initialisé (table: {table_name})")
        except Exception as e:
            raise ConnectionError(f"❌ Erreur de connexion Supabase: {e}")

    def _init_vectorstore(self):
        """Initialise le vectorstore Supabase"""
        if self.vectorstore is None:
            self.vectorstore = SupabaseVectorStore(
                client=self.client,
                embedding=self.embeddings,
                table_name=self.table_name
            )

    def create_table(self) -> bool:
        """
        Crée la table pgvector dans Supabase PostgreSQL.

        SQL pour exécuter manuellement si nécessaire:
        ```sql
        CREATE EXTENSION IF NOT EXISTS vector;

        CREATE TABLE documents (
            id BIGSERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            metadata JSONB,
            embedding VECTOR(1024),
            source_ref TEXT,
            document_type TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);
        ```
        """
        try:
            logger.info("📋 Création de la table pgvector...")

            # Exécuter via Supabase REST API (RPC)
            self.client.rpc(
                "create_documents_table_if_not_exists",
                {}
            ).execute()

            logger.info("✅ Table créée (ou déjà existante)")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Impossible de créer la table: {e}")
            logger.info("💡 Créer manuellement via: supabase_url/admin/schemas")
            return False

    def add_documents(self, documents: List[Document], batch_size: int = 100) -> List[str]:
        """
        Ajoute des documents à pgvector.

        Args:
            documents: Documents à ajouter
            batch_size: Nombre de documents par batch

        Returns:
            Liste des IDs créés
        """
        self._init_vectorstore()

        logger.info(f"➕ Ajout de {len(documents)} documents à pgvector")

        try:
            ids = self.vectorstore.add_documents(documents)
            logger.info(f"✅ {len(ids)} documents ajoutés")
            return ids
        except Exception as e:
            logger.error(f"❌ Erreur en ajoutant les documents: {e}")
            raise

    def search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Tuple[Document, float]]:
        """
        Recherche des documents similaires.

        Args:
            query: Requête de recherche
            k: Nombre de résultats
            filter_dict: Filtres optionnels (ex: {"document_type": "loi"})

        Returns:
            Liste de tuples (document, score_similarité)
        """
        self._init_vectorstore()

        logger.info(f"🔍 Recherche: '{query}' (k={k})")

        try:
            # Recherche simple
            results = self.vectorstore.similarity_search_with_score(query, k=k)

            # Filtrer les résultats si nécessaire
            if filter_dict:
                filtered = []
                for doc, score in results:
                    if all(
                        doc.metadata.get(k) == v
                        for k, v in filter_dict.items()
                    ):
                        filtered.append((doc, score))
                results = filtered[:k]

            logger.info(f"✅ {len(results)} résultats trouvés")
            return results
        except Exception as e:
            logger.error(f"❌ Erreur en recherchant: {e}")
            raise

    def get_retriever(self, k: int = 5):
        """
        Retourne un retriever LangChain.

        Args:
            k: Nombre de documents

        Returns:
            Retriever LangChain
        """
        self._init_vectorstore()
        return self.vectorstore.as_retriever(search_kwargs={"k": k})

    def delete_document(self, doc_id: str) -> bool:
        """
        Supprime un document par ID.

        Args:
            doc_id: ID du document

        Returns:
            True si succès
        """
        try:
            logger.info(f"🗑️ Suppression du document {doc_id}...")
            self.client.table(self.table_name).delete().eq("id", doc_id).execute()
            logger.info(f"✅ Document supprimé")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur en supprimant: {e}")
            return False

    def update_document_metadata(self, doc_id: str, metadata: Dict) -> bool:
        """
        Met à jour les métadonnées d'un document.

        Args:
            doc_id: ID du document
            metadata: Nouvelles métadonnées

        Returns:
            True si succès
        """
        try:
            logger.info(f"📝 Mise à jour des métadonnées du document {doc_id}...")
            self.client.table(self.table_name).update({
                "metadata": metadata,
                "updated_at": datetime.now().isoformat()
            }).eq("id", doc_id).execute()
            logger.info(f"✅ Métadonnées mises à jour")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur en mettant à jour: {e}")
            return False

    def get_documents_by_type(self, doc_type: str, limit: int = 100) -> List[Document]:
        """
        Récupère tous les documents d'un type spécifique.

        Args:
            doc_type: Type de document (loi, decret, etc.)
            limit: Limite du nombre de résultats

        Returns:
            Liste de documents
        """
        try:
            logger.info(f"📚 Récupération des documents type={doc_type}...")
            data = self.client.table(self.table_name).select(
                "id,content,metadata"
            ).eq(
                "document_type", doc_type
            ).limit(limit).execute()

            documents = []
            for record in data.data:
                doc = Document(
                    page_content=record["content"],
                    metadata=record.get("metadata", {})
                )
                documents.append(doc)

            logger.info(f"✅ {len(documents)} documents trouvés")
            return documents
        except Exception as e:
            logger.error(f"❌ Erreur en récupérant les documents: {e}")
            return []

    def get_stats(self) -> Dict:
        """
        Retourne des statistiques sur la base vectorielle.

        Returns:
            Dictionnaire avec les stats
        """
        try:
            logger.info("📊 Récupération des statistiques...")

            # Compter les documents
            count_data = self.client.table(self.table_name).select(
                "id"
            ).execute()
            total_docs = len(count_data.data)

            # Compter par type
            all_data = self.client.table(self.table_name).select(
                "document_type"
            ).execute()
            doc_types = {}
            for record in all_data.data:
                dt = record.get("document_type", "unknown")
                doc_types[dt] = doc_types.get(dt, 0) + 1

            stats = {
                "total_documents": total_docs,
                "document_types": doc_types,
                "embedding_model": self.embedding_model_name,
                "table_name": self.table_name,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"✅ Stats calculées")
            return stats
        except Exception as e:
            logger.error(f"❌ Erreur en récupérant les stats: {e}")
            return {}


class VectorStoreFactory:
    """
    Factory pour créer facilement le bon gestionnaire vectoriel.

    Permet de switcher entre FAISS (dev) et pgvector (prod) facilement.
    """

    @staticmethod
    def create(backend: str = "faiss", **kwargs):
        """
        Crée un gestionnaire vectoriel.

        Args:
            backend: "faiss" ou "pgvector"
            **kwargs: Arguments passés au gestionnaire

        Returns:
            FAISSManager ou PGVectorManager
        """
        if backend.lower() == "faiss":
            from faiss_manager import FAISSManager
            return FAISSManager(**kwargs)
        elif backend.lower() == "pgvector":
            return PGVectorManager(**kwargs)
        else:
            raise ValueError(f"❌ Backend inconnu: {backend}")

    @staticmethod
    def get_backend_from_env() -> str:
        """
        Détecte le backend depuis les variables d'environnement.

        Returns:
            "faiss" ou "pgvector"
        """
        if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"):
            return "pgvector"
        return "faiss"


if __name__ == "__main__":
    # Exemple: créer la table pgvector
    # (À exécuter après avoir configuré SUPABASE_URL et SUPABASE_KEY)

    print("💡 Pour utiliser pgvector avec Supabase:")
    print("1. Configurer les variables d'environnement:")
    print("   SUPABASE_URL=https://xxxx.supabase.co")
    print("   SUPABASE_KEY=your-anon-key")
    print("2. Créer la table PostgreSQL (voir create_table())")
    print("3. Utiliser avec: VectorStoreFactory.create('pgvector')")
