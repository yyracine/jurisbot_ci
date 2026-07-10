"""
⚙️ Script de configuration et initialisation du système RAG

Exécuter une seule fois pour:
1. Vérifier les dépendances
2. Charger les documents Markdown
3. Créer les index FAISS
4. Générer les rapports d'initialisation

Usage:
    python setup_rag.py
    python setup_rag.py --rebuild  (force la reconstruction)
    python setup_rag.py --backend pgvector  (utiliser pgvector à la place)
    python setup_rag.py --docs ./path/to/docs  (chemin personnalisé)
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Set UTF-8 encoding for console output
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8')

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_dependencies() -> bool:
    """Vérifie que toutes les dépendances sont disponibles"""
    logger.info("🔍 Vérification des dépendances...")

    required_packages = [
        ("langchain", "langchain"),
        ("langchain_mistralai", "langchain_mistralai"),
        ("langchain_community", "langchain_community"),
        ("faiss", "faiss"),
        ("python-dotenv", "dotenv")
    ]

    missing = []
    for pkg_name, import_name in required_packages:
        try:
            __import__(import_name)
            logger.info(f"  ✅ {pkg_name}")
        except ImportError:
            logger.error(f"  ❌ {pkg_name}")
            missing.append(pkg_name)

    if missing:
        logger.error(f"\n❌ Dépendances manquantes: {', '.join(missing)}")
        logger.info("\nInstaller avec:")
        logger.info(f"  pip install {' '.join(missing)}")
        return False

    logger.info("✅ Toutes les dépendances disponibles\n")
    return True


def check_env() -> bool:
    """Vérifie les variables d'environnement"""
    logger.info("🔐 Vérification de la configuration...")

    from dotenv import load_dotenv
    load_dotenv()

    required_env = {
        "MISTRAL_API_KEY": "Clé API Mistral"
    }

    missing = []
    for var, desc in required_env.items():
        if os.getenv(var):
            logger.info(f"  ✅ {var}: configuré")
        else:
            logger.warning(f"  ⚠️ {var}: manquant")
            missing.append(f"{var} ({desc})")

    if missing:
        logger.error(f"\n❌ Configuration incomplète:")
        for item in missing:
            logger.error(f"  - {item}")
        logger.info("\nConfigurer dans .env ou variables d'environnement")
        return False

    logger.info("✅ Configuration complète\n")
    return True


def check_documents(doc_path: str = "code_du_travail_ci.md") -> bool:
    """Vérifie que les documents Markdown existent"""
    logger.info("📄 Vérification des documents...")

    if not os.path.exists(doc_path):
        logger.error(f"\n❌ Document not found: {doc_path}")
        logger.info(f"Créer le fichier Markdown et placer dans: {os.path.abspath(doc_path)}")
        return False

    file_size = os.path.getsize(doc_path) / 1024
    logger.info(f"  ✅ {doc_path} ({file_size:.1f} KB)")
    logger.info("✅ Documents disponibles\n")
    return True


def setup_rag(backend: str = "faiss", rebuild: bool = False, doc_path: str = "code_du_travail_ci.md"):
    """Initialise le système RAG"""
    logger.info("🚀 Initialisation du système RAG...\n")

    from rag_pipeline import RAGPipeline

    try:
        # Créer le pipeline
        logger.info(f"📦 Création du pipeline RAG (backend: {backend})...")
        pipeline = RAGPipeline(backend=backend)

        # Ingérer les documents
        if rebuild or not os.path.exists(f"./faiss_indexes/{pipeline.index_name}"):
            logger.info(f"📥 Ingestion du document: {doc_path}")
            result = pipeline.ingest_markdown(doc_path)

            if result["status"] != "success":
                logger.error(f"❌ Erreur lors de l'ingestion: {result.get('message')}")
                return False

            logger.info(f"✅ Ingestion réussie:")
            logger.info(f"   - Fichier: {result['file']}")
            logger.info(f"   - Documents: {result['documents']}")
            logger.info(f"   - Chunks: {result['chunks']}")
        else:
            logger.info(f"✅ Index existe déjà, chargement...")
            pipeline.retriever = pipeline.vectorstore.get_retriever(k=5, index_name=pipeline.index_name)

        # Afficher les stats
        logger.info("\n📊 Statistiques du système:")
        stats = pipeline.get_stats()

        if backend == "faiss":
            indexes = stats.get("vectorstore", {}).get("indexes", [])
            if indexes:
                idx = indexes[0]
                logger.info(f"  - Index: {idx['name']}")
                logger.info(f"  - Documents: {idx.get('document_count', 'N/A')}")
                logger.info(f"  - Types: {', '.join(idx.get('document_types', []))}")
        else:
            vs_stats = stats.get("vectorstore", {})
            logger.info(f"  - Documents: {vs_stats.get('total_documents', 'N/A')}")
            logger.info(f"  - Types: {vs_stats.get('document_types', {})}")

        # Test rapide
        logger.info("\n🧪 Test rapide du système...")
        test_query = "Quels sont les droits des travailleurs ?"
        test_result = pipeline.query(test_query, include_sources=False)

        if test_result["status"] == "success":
            logger.info(f"✅ Requête test réussie")
            logger.info(f"   Réponse (premiers 150 chars):")
            logger.info(f"   {test_result['answer'][:150]}...")
        else:
            logger.error(f"❌ Erreur test: {test_result.get('message')}")
            return False

        # Sauvegarder le rapport
        report = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "backend": backend,
            "ingestion": stats.get("ingestion", {}),
            "vectorstore": stats.get("vectorstore", {}),
            "test_passed": test_result["status"] == "success"
        }

        report_path = "setup_rag_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"\n✅ Configuration réussie!")
        logger.info(f"📋 Rapport sauvegardé: {report_path}")
        logger.info(f"\n💡 Prochaines étapes:")
        logger.info(f"   1. Importer RAGPipeline: from rag_pipeline import RAGPipeline")
        logger.info(f"   2. Créer un pipeline: pipeline = RAGPipeline()")
        logger.info(f"   3. Poser une question: pipeline.query('Votre question')")
        logger.info(f"\n📚 Voir aussi:")
        logger.info(f"   - rag_pipeline.py - Pipeline complet")
        logger.info(f"   - bot_juridique.py - Engine RAG original")
        logger.info(f"   - document_ingestion.py - Gestion des documents")
        logger.info(f"   - faiss_manager.py - Gestion des index FAISS")

        return True

    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(
        description="Configuration et initialisation du système RAG"
    )
    parser.add_argument(
        "--backend",
        choices=["faiss", "pgvector", "auto"],
        default="auto",
        help="Backend vectoriel à utiliser (défaut: auto-détection)"
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Forcer la reconstruction des index"
    )
    parser.add_argument(
        "--docs",
        default="code_du_travail_ci.md",
        help="Chemin vers le fichier de documents (défaut: code_du_travail_ci.md)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Mode rapide (skip tests)"
    )

    args = parser.parse_args()

    print("\n" + "="*60)
    print("🚀 INITIALISATION DU SYSTÈME RAG - JurisBot CI")
    print("="*60 + "\n")

    # Étape 1: Vérifier les dépendances
    if not check_dependencies():
        return False

    # Étape 2: Vérifier la configuration
    if not check_env():
        return False

    # Étape 3: Vérifier les documents
    if not check_documents(args.docs):
        return False

    # Étape 4: Configurer le RAG
    success = setup_rag(
        backend=args.backend,
        rebuild=args.rebuild,
        doc_path=args.docs
    )

    print("\n" + "="*60)
    if success:
        print("✅ INITIALISATION RÉUSSIE")
    else:
        print("❌ INITIALISATION ÉCHOUÉE")
    print("="*60 + "\n")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
