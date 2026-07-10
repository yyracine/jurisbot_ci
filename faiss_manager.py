"""
🔍 Gestionnaire FAISS pour le RAG - MVP

Fonctionnalités:
- Créer/charger des index FAISS
- Ajouter des documents (ingestion)
- Sauvegarder/charger des index persistants
- Recherche vectorielle
- Support pour plusieurs index (multi-source)
"""

import os
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path

from langchain_core.documents import Document
from langchain_mistralai import MistralAIEmbeddings
from langchain_community.vectorstores import FAISS
import faiss

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FAISSManager:
    """
    Gestionnaire pour les index vectoriels FAISS.

    Support:
    - Création d'index
    - Ajout/suppression de documents
    - Persistance (sauvegarde/chargement)
    - Recherche multi-requête
    - Métadonnées enrichies
    """

    def __init__(
        self,
        embedding_model: str = "mistral-embed",
        index_dir: str = "./faiss_indexes",
        api_key: Optional[str] = None
    ):
        """
        Args:
            embedding_model: Modèle pour les embeddings
            index_dir: Répertoire pour stocker les index FAISS
            api_key: Clé API Mistral (optionnel si dans .env)
        """
        self.embedding_model_name = embedding_model
        self.index_dir = index_dir
        os.makedirs(index_dir, exist_ok=True)

        # Initialiser les embeddings
        if api_key:
            os.environ["MISTRAL_API_KEY"] = api_key

        self.embeddings = MistralAIEmbeddings(model=embedding_model)
        self.vectorstore = None
        self.index_metadata = {}
        self._load_index_metadata()

        logger.info(f"🚀 FAISSManager initialisé (modèle: {embedding_model})")

    def _get_index_path(self, index_name: str) -> str:
        """Retourne le chemin complet d'un index"""
        return os.path.join(self.index_dir, index_name)

    def _get_metadata_path(self, index_name: str) -> str:
        """Retourne le chemin du fichier de métadonnées"""
        return os.path.join(self.index_dir, f"{index_name}_metadata.json")

    def _load_index_metadata(self):
        """Charge tous les métadonnées d'index existants"""
        metadata_files = Path(self.index_dir).glob("*_metadata.json")
        for mf in metadata_files:
            try:
                with open(mf, 'r', encoding='utf-8') as f:
                    index_name = mf.stem.replace("_metadata", "")
                    self.index_metadata[index_name] = json.load(f)
            except Exception as e:
                logger.warning(f"⚠️ Erreur en chargeant {mf}: {e}")

    def _save_index_metadata(self, index_name: str, metadata: Dict):
        """Sauvegarde les métadonnées d'un index"""
        path = self._get_metadata_path(index_name)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        self.index_metadata[index_name] = metadata

    def create_index(self, documents: List[Document], index_name: str = "main") -> str:
        """
        Crée un nouvel index FAISS à partir de documents.

        Args:
            documents: Documents à indexer
            index_name: Nom de l'index

        Returns:
            Chemin vers l'index créé
        """
        logger.info(f"🏗️ Création d'un nouvel index '{index_name}' avec {len(documents)} documents")

        if not documents:
            raise ValueError("❌ Aucun document à indexer")

        # Créer l'index FAISS
        self.vectorstore = FAISS.from_documents(documents, self.embeddings)

        # Sauvegarder
        index_path = self._get_index_path(index_name)
        self.vectorstore.save_local(index_path)
        logger.info(f"✅ Index sauvegardé: {index_path}")

        # Sauvegarder les métadonnées
        metadata = {
            "name": index_name,
            "created_at": datetime.now().isoformat(),
            "document_count": len(documents),
            "embedding_model": self.embedding_model_name,
            "document_types": list(set(
                doc.metadata.get("document_type", "unknown") for doc in documents
            ))
        }
        self._save_index_metadata(index_name, metadata)
        logger.info(f"📋 Métadonnées sauvegardées")

        return index_path

    def load_index(self, index_name: str = "main") -> bool:
        """
        Charge un index FAISS existant.

        Args:
            index_name: Nom de l'index

        Returns:
            True si succès, False sinon
        """
        index_path = self._get_index_path(index_name)

        if not os.path.exists(index_path):
            logger.error(f"❌ Index non trouvé: {index_path}")
            return False

        try:
            logger.info(f"📂 Chargement de l'index '{index_name}'...")
            self.vectorstore = FAISS.load_local(index_path, self.embeddings)
            logger.info(f"✅ Index chargé: {index_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur en chargeant l'index: {e}")
            return False

    def add_documents(self, documents: List[Document], index_name: str = "main") -> bool:
        """
        Ajoute des documents à un index existant.

        Args:
            documents: Documents à ajouter
            index_name: Nom de l'index

        Returns:
            True si succès
        """
        if not self.vectorstore:
            if not self.load_index(index_name):
                raise ValueError(f"❌ Index '{index_name}' non trouvé")

        try:
            logger.info(f"➕ Ajout de {len(documents)} documents à '{index_name}'")
            self.vectorstore.add_documents(documents)

            # Sauvegarder l'index mis à jour
            index_path = self._get_index_path(index_name)
            self.vectorstore.save_local(index_path)

            # Mettre à jour les métadonnées
            if index_name in self.index_metadata:
                self.index_metadata[index_name]["document_count"] += len(documents)
                self.index_metadata[index_name]["last_updated"] = datetime.now().isoformat()
                self._save_index_metadata(index_name, self.index_metadata[index_name])

            logger.info(f"✅ Documents ajoutés et sauvegardés")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur en ajoutant les documents: {e}")
            return False

    def search(
        self,
        query: str,
        k: int = 5,
        index_name: str = "main"
    ) -> List[Tuple[Document, float]]:
        """
        Recherche des documents similaires.

        Args:
            query: Requête de recherche
            k: Nombre de résultats
            index_name: Nom de l'index

        Returns:
            Liste de tuples (document, score_similarité)
        """
        if not self.vectorstore:
            if not self.load_index(index_name):
                raise ValueError(f"❌ Index '{index_name}' non trouvé")

        logger.info(f"🔍 Recherche: '{query}' (k={k})")

        # Recherche avec scores
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        logger.info(f"✅ {len(results)} résultats trouvés")

        return results

    def get_retriever(self, k: int = 5, index_name: str = "main"):
        """
        Retourne un retriever LangChain pour utilisation dans un RAG.

        Args:
            k: Nombre de documents à récupérer
            index_name: Nom de l'index

        Returns:
            Retriever LangChain
        """
        if not self.vectorstore:
            self.load_index(index_name)

        return self.vectorstore.as_retriever(search_kwargs={"k": k})

    def get_index_stats(self, index_name: str = "main") -> Dict:
        """
        Retourne les statistiques d'un index.

        Args:
            index_name: Nom de l'index

        Returns:
            Dictionnaire avec les stats
        """
        if index_name not in self.index_metadata:
            return {"error": f"Index '{index_name}' non trouvé"}

        stats = self.index_metadata[index_name].copy()

        # Récupérer la taille du répertoire
        index_path = self._get_index_path(index_name)
        if os.path.exists(index_path):
            size_kb = sum(
                os.path.getsize(os.path.join(dp, f)) / 1024
                for dp, dn, filenames in os.walk(index_path)
                for f in filenames
            )
            stats["size_kb"] = round(size_kb, 2)

        return stats

    def list_indexes(self) -> List[Dict]:
        """
        Liste tous les index disponibles.

        Returns:
            Liste des index avec métadonnées
        """
        indexes = []
        for index_name, metadata in self.index_metadata.items():
            indexes.append({
                "name": index_name,
                **metadata
            })
        logger.info(f"📚 {len(indexes)} index(es) trouvé(s)")
        return indexes

    def delete_index(self, index_name: str) -> bool:
        """
        Supprime un index FAISS.

        Args:
            index_name: Nom de l'index

        Returns:
            True si succès
        """
        import shutil
        index_path = self._get_index_path(index_name)

        try:
            if os.path.exists(index_path):
                shutil.rmtree(index_path)
                logger.info(f"🗑️ Index supprimé: {index_path}")

            # Supprimer les métadonnées
            metadata_path = self._get_metadata_path(index_name)
            if os.path.exists(metadata_path):
                os.remove(metadata_path)

            if index_name in self.index_metadata:
                del self.index_metadata[index_name]

            logger.info(f"✅ Index '{index_name}' complètement supprimé")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur en supprimant l'index: {e}")
            return False

    def rebuild_index(self, documents: List[Document], index_name: str = "main") -> str:
        """
        Reconstruit complètement un index (supprime puis crée).

        Args:
            documents: Documents à indexer
            index_name: Nom de l'index

        Returns:
            Chemin vers l'index
        """
        logger.info(f"🔄 Reconstruction de l'index '{index_name}'...")
        self.delete_index(index_name)
        return self.create_index(documents, index_name)

    def get_index_info(self) -> Dict:
        """Retourne l'état général de tous les index"""
        return {
            "embedding_model": self.embedding_model_name,
            "index_dir": self.index_dir,
            "indexes": self.list_indexes(),
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Exemple d'utilisation
    from document_ingestion import DocumentIngestor, chunk_documents_legal

    # 1. Ingérer les documents
    ingestor = DocumentIngestor()
    docs, metadata = ingestor.load_markdown_file("code_du_travail_ci.md")
    ingestor.record_ingestion(metadata)

    # 2. Découper en chunks
    chunks = chunk_documents_legal(docs)

    # 3. Créer l'index FAISS
    faiss_mgr = FAISSManager()
    index_path = faiss_mgr.create_index(chunks, "droit_travail_ci")

    # 4. Afficher les stats
    print("\n" + "="*50)
    print("📊 STATS DU FAISS")
    print("="*50)
    print(json.dumps(faiss_mgr.get_index_info(), indent=2, ensure_ascii=False))
