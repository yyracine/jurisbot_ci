"""
📄 Système d'ingestion de documents Markdown pour le RAG

Support pour:
- Chargement de fichiers Markdown individuels
- Chargement batch de documents
- Métadonnées enrichies (source, date, type de document)
- Détection automatique de la structure juridique
- Versioning et tracking d'ingestion
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_core.documents import Document

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class IngestionMetadata:
    """Métadonnées d'un document ingéré"""
    file_path: str
    file_name: str
    ingestion_date: str
    file_size_kb: float
    chunk_count: int
    source_ref: str
    document_type: str  # "loi", "decret", "arrete", "convention", "autre"


class DocumentIngestor:
    """
    Gestionnaire central d'ingestion de documents Markdown.

    Fonctionnalités:
    - Chargement de fichiers Markdown
    - Détection automatique du type de document
    - Gestion des métadonnées
    - Suivi d'ingestion (tracking)
    """

    def __init__(self, ingestion_dir: str = "./ingestion_logs"):
        """
        Args:
            ingestion_dir: Répertoire pour stocker les logs d'ingestion
        """
        self.ingestion_dir = ingestion_dir
        os.makedirs(ingestion_dir, exist_ok=True)
        self.ingestion_log = os.path.join(ingestion_dir, "ingestion_history.json")
        self.ingestion_history = self._load_history()

    def _load_history(self) -> List[Dict]:
        """Charge l'historique d'ingestion depuis le fichier JSON"""
        if os.path.exists(self.ingestion_log):
            try:
                with open(self.ingestion_log, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Impossible de charger l'historique: {e}")
        return []

    def _save_history(self):
        """Sauvegarde l'historique d'ingestion"""
        with open(self.ingestion_log, 'w', encoding='utf-8') as f:
            json.dump(self.ingestion_history, f, indent=2, ensure_ascii=False)

    def _detect_document_type(self, content: str, file_name: str) -> Tuple[str, str]:
        """
        Détecte le type de document et extrait la source de référence.

        Returns:
            Tuple (document_type, source_ref)
        """
        content_upper = content.upper()

        # Chercher les patterns dans le contenu
        if "# LOI N°" in content_upper:
            doc_type = "loi"
            match = self._extract_ref(content, "# LOI")
        elif "# DECRET N°" in content_upper:
            doc_type = "decret"
            match = self._extract_ref(content, "# DECRET")
        elif "# ARRETE N°" in content_upper:
            doc_type = "arrete"
            match = self._extract_ref(content, "# ARRETE")
        elif "CONVENTION COLLECTIVE" in content_upper:
            doc_type = "convention"
            match = "Convention Collective Interprofessionnelle du 19 juillet 1977"
        else:
            doc_type = "autre"
            match = file_name

        return doc_type, match

    def _extract_ref(self, content: str, pattern: str) -> str:
        """Extrait la référence du document du contenu"""
        lines = content.split('\n')
        for line in lines:
            if line.startswith(pattern):
                return line.lstrip("# ").strip()
        return pattern

    def load_markdown_file(self, file_path: str) -> Tuple[List[Document], IngestionMetadata]:
        """
        Charge un fichier Markdown unique.

        Args:
            file_path: Chemin vers le fichier Markdown

        Returns:
            Tuple (documents, metadata)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"❌ Fichier non trouvé: {file_path}")

        logger.info(f"📄 Chargement du fichier: {file_path}")

        # Charger le fichier
        loader = TextLoader(file_path, encoding="utf-8")
        documents = loader.load()

        if not documents:
            raise ValueError(f"❌ Fichier vide ou invalide: {file_path}")

        # Détecter le type et la source
        content = documents[0].page_content
        doc_type, source_ref = self._detect_document_type(content, Path(file_path).name)

        # Enrichir les métadonnées
        for doc in documents:
            doc.metadata["source_ref"] = source_ref
            doc.metadata["document_type"] = doc_type
            doc.metadata["file_path"] = file_path
            doc.metadata["ingestion_date"] = datetime.now().isoformat()

        # Créer les métadonnées d'ingestion
        file_size_kb = os.path.getsize(file_path) / 1024
        metadata = IngestionMetadata(
            file_path=file_path,
            file_name=Path(file_path).name,
            ingestion_date=datetime.now().isoformat(),
            file_size_kb=file_size_kb,
            chunk_count=len(documents),
            source_ref=source_ref,
            document_type=doc_type
        )

        logger.info(f"✅ {file_path} chargé ({len(documents)} chunks, {file_size_kb:.1f} KB)")

        return documents, metadata

    def load_markdown_directory(self, directory: str, pattern: str = "*.md") -> Tuple[List[Document], List[IngestionMetadata]]:
        """
        Charge tous les fichiers Markdown d'un répertoire.

        Args:
            directory: Chemin du répertoire
            pattern: Pattern pour les fichiers (défaut: *.md)

        Returns:
            Tuple (all_documents, all_metadata)
        """
        if not os.path.isdir(directory):
            raise NotADirectoryError(f"❌ Répertoire non trouvé: {directory}")

        logger.info(f"📁 Chargement du répertoire: {directory}")

        all_documents = []
        all_metadata = []

        md_files = sorted(Path(directory).glob(pattern))
        logger.info(f"🔍 {len(md_files)} fichiers Markdown trouvés")

        for file_path in md_files:
            try:
                docs, metadata = self.load_markdown_file(str(file_path))
                all_documents.extend(docs)
                all_metadata.append(metadata)
            except Exception as e:
                logger.error(f"⚠️ Erreur en chargeant {file_path}: {e}")

        logger.info(f"✅ {len(all_metadata)} fichiers chargés, {len(all_documents)} documents totaux")

        return all_documents, all_metadata

    def load_batch(self, file_paths: List[str]) -> Tuple[List[Document], List[IngestionMetadata]]:
        """
        Charge une liste spécifique de fichiers.

        Args:
            file_paths: Liste de chemins vers les fichiers

        Returns:
            Tuple (all_documents, all_metadata)
        """
        logger.info(f"📚 Chargement batch de {len(file_paths)} fichiers")

        all_documents = []
        all_metadata = []

        for file_path in file_paths:
            try:
                docs, metadata = self.load_markdown_file(file_path)
                all_documents.extend(docs)
                all_metadata.append(metadata)
            except Exception as e:
                logger.error(f"⚠️ Erreur en chargeant {file_path}: {e}")

        return all_documents, all_metadata

    def record_ingestion(self, metadata_list: List[IngestionMetadata]):
        """Enregistre les métadonnées d'ingestion dans l'historique"""
        for metadata in metadata_list:
            record = {
                **asdict(metadata),
                "timestamp": datetime.now().isoformat()
            }
            self.ingestion_history.append(record)
        self._save_history()
        logger.info(f"📋 {len(metadata_list)} ingestions enregistrées")

    def get_ingestion_summary(self) -> Dict:
        """Retourne un résumé de tous les documents ingérés"""
        if not self.ingestion_history:
            return {"total_files": 0, "total_chunks": 0, "files": []}

        total_chunks = sum(record["chunk_count"] for record in self.ingestion_history)
        total_size = sum(record["file_size_kb"] for record in self.ingestion_history)

        doc_types = {}
        for record in self.ingestion_history:
            dt = record["document_type"]
            doc_types[dt] = doc_types.get(dt, 0) + 1

        return {
            "total_files": len(self.ingestion_history),
            "total_chunks": total_chunks,
            "total_size_kb": total_size,
            "document_types": doc_types,
            "last_ingestion": self.ingestion_history[-1]["ingestion_date"] if self.ingestion_history else None,
            "files": [
                {
                    "name": record["file_name"],
                    "type": record["document_type"],
                    "chunks": record["chunk_count"],
                    "size_kb": record["file_size_kb"],
                    "date": record["ingestion_date"]
                }
                for record in self.ingestion_history[-10:]  # Derniers 10
            ]
        }


# ==========================================
# UTILITAIRES DE CHUNKING
# ==========================================

from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_documents_legal(
    documents: List[Document],
    chunk_size: int = 2000,
    chunk_overlap: int = 400
) -> List[Document]:
    """
    Découpe les documents en chunks optimisés pour le contexte juridique.

    Args:
        documents: Liste de documents à découper
        chunk_size: Taille maximale d'un chunk
        chunk_overlap: Chevauchement entre chunks

    Returns:
        Liste de documents découpés
    """
    logger.info(f"✂️ Découpage de {len(documents)} documents ({chunk_size} taille, {chunk_overlap} chevauchement)")

    # Séparateurs optimisés pour textes juridiques
    legal_separators = [
        "\n## ",      # Sous-titres
        "\n### ",     # Sous-sous-titres
        "\nArt. ",    # Articles (abrégé)
        "\nARTICLE ", # Articles (complet)
        "\nCHAPITRE ",
        "\nSECTION ",
        "\nTITRE ",
        "\n\n",       # Paragraphes
        "\n",         # Lignes
        " ",          # Mots
        ""            # Caractères
    ]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=legal_separators
    )

    chunks = splitter.split_documents(documents)
    logger.info(f"✅ {len(chunks)} chunks créés")

    return chunks


if __name__ == "__main__":
    # Exemple d'utilisation
    ingestor = DocumentIngestor()

    # Charger le fichier principal
    code_path = "code_du_travail_ci.md"
    if os.path.exists(code_path):
        docs, metadata = ingestor.load_markdown_file(code_path)
        ingestor.record_ingestion([metadata])

        # Afficher le résumé
        summary = ingestor.get_ingestion_summary()
        print("\n" + "="*50)
        print("📊 RÉSUMÉ D'INGESTION")
        print("="*50)
        print(json.dumps(summary, indent=2, ensure_ascii=False))
