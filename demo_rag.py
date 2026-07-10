"""
🎬 Démonstration du système RAG intégré

Script simple pour tester et démontrer le système complet:
- Ingestion de documents
- Indexation FAISS
- Requêtes et retrieval
- Affichage des résultats

Usage:
    python demo_rag.py
"""

import os
import sys
import json
from pathlib import Path

# Vérifier que les modules existent
try:
    from document_ingestion import DocumentIngestor, chunk_documents_legal
    from faiss_manager import FAISSManager
    from rag_pipeline import RAGPipeline
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("Assurez-vous que tous les modules sont dans le même répertoire")
    sys.exit(1)


def print_header(title: str):
    """Affiche un header formaté"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_document_ingestion():
    """Démontre le chargement de documents"""
    print_header("1️⃣ INGESTION DE DOCUMENTS")

    doc_path = "code_du_travail_ci.md"

    if not os.path.exists(doc_path):
        print(f"⚠️ Document non trouvé: {doc_path}")
        return None

    print(f"📄 Chargement de {doc_path}...")

    ingestor = DocumentIngestor()
    docs, metadata = ingestor.load_markdown_file(doc_path)
    ingestor.record_ingestion([metadata])

    print(f"✅ Chargement réussi:")
    print(f"   - Documents: {len(docs)}")
    print(f"   - Taille: {metadata.file_size_kb:.1f} KB")
    print(f"   - Type: {metadata.document_type}")
    print(f"   - Source: {metadata.source_ref}")

    # Afficher les stats d'ingestion
    summary = ingestor.get_ingestion_summary()
    print(f"\n📊 Résumé d'ingestion:")
    print(f"   - Fichiers ingérés: {summary['total_files']}")
    print(f"   - Chunks totaux: {summary['total_chunks']}")
    print(f"   - Taille totale: {summary['total_size_kb']:.1f} KB")

    return docs


def demo_chunking(docs):
    """Démontre le découpage en chunks"""
    print_header("2️⃣ DÉCOUPAGE EN CHUNKS")

    print(f"Découpage de {len(docs)} documents...")

    chunks = chunk_documents_legal(docs, chunk_size=2000, chunk_overlap=400)

    print(f"✅ Chunking réussi:")
    print(f"   - Total chunks: {len(chunks)}")
    print(f"   - Taille moyenne: ~2000 caractères")
    print(f"   - Chevauchement: 400 caractères")

    # Afficher les métadonnées des premiers chunks
    print(f"\n📋 Exemple de chunks:")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n   Chunk {i+1}:")
        print(f"   - Type: {chunk.metadata.get('document_type', 'unknown')}")
        print(f"   - Source: {chunk.metadata.get('source_ref', 'unknown')}")
        print(f"   - Extrait: {chunk.page_content[:80]}...")

    return chunks


def demo_indexing(chunks):
    """Démontre la création d'index FAISS"""
    print_header("3️⃣ CRÉATION D'INDEX FAISS")

    print("Création de l'index FAISS...")

    faiss_mgr = FAISSManager()

    # Créer l'index
    index_path = faiss_mgr.create_index(chunks, "droit_travail_ci_demo")

    print(f"✅ Index créé:")
    print(f"   - Chemin: {index_path}")
    print(f"   - Chunks indexés: {len(chunks)}")
    print(f"   - Modèle embeddings: mistral-embed")

    # Afficher les stats
    stats = faiss_mgr.get_index_stats("droit_travail_ci_demo")
    print(f"\n📊 Statistiques de l'index:")
    print(f"   - Documents: {stats.get('document_count', 'N/A')}")
    print(f"   - Types: {stats.get('document_types', [])}")
    print(f"   - Taille: {stats.get('size_kb', 'N/A'):.1f} KB")

    return faiss_mgr


def demo_search(faiss_mgr):
    """Démontre la recherche vectorielle"""
    print_header("4️⃣ RECHERCHE VECTORIELLE")

    query = "heures supplémentaires"
    print(f"🔍 Requête: '{query}'")

    results = faiss_mgr.search(query, k=3, index_name="droit_travail_ci_demo")

    print(f"\n✅ Résultats trouvés: {len(results)}")

    for i, (doc, score) in enumerate(results, 1):
        print(f"\n   Résultat {i} (score: {score:.2f}):")
        print(f"   - Source: {doc.metadata.get('source_ref', 'unknown')}")
        print(f"   - Type: {doc.metadata.get('document_type', 'unknown')}")
        print(f"   - Extrait: {doc.page_content[:100]}...")


def demo_rag_pipeline():
    """Démontre le pipeline RAG complet"""
    print_header("5️⃣ PIPELINE RAG COMPLET")

    doc_path = "code_du_travail_ci.md"

    if not os.path.exists(doc_path):
        print(f"⚠️ Document non trouvé: {doc_path}")
        return

    print("Initialisation du RAG Pipeline...")

    try:
        pipeline = RAGPipeline(backend="faiss")

        # Ingérer
        print(f"\n📥 Ingestion...")
        result = pipeline.ingest_markdown(doc_path)

        if result['status'] != 'success':
            print(f"❌ Erreur: {result['message']}")
            return

        print(f"✅ Ingestion réussie ({result['chunks']} chunks)")

        # Tester plusieurs requêtes
        test_queries = [
            "Quels sont les droits en cas de licenciement ?",
            "Combien de jours de congé annuel ?",
            "Quelles sont les heures supplémentaires ?",
        ]

        print(f"\n🤖 Tests de requêtes:\n")

        for q in test_queries:
            print(f"   ❓ {q}")

            result = pipeline.query(q)

            if result['status'] == 'success':
                # Afficher les premiers 200 caractères de la réponse
                answer = result['answer']
                print(f"   ✅ {answer[:150]}...")

                # Afficher les sources
                if result.get('sources'):
                    print(f"   📚 Sources: {len(result['sources'])} document(s)")
                    for src in result['sources'][:2]:
                        print(f"      - {src['ref']}")
            else:
                print(f"   ❌ Erreur: {result['message']}")

            print()

        # Afficher les stats
        print(f"\n📊 Statistiques du pipeline:")
        stats = pipeline.get_stats()

        if 'ingestion' in stats:
            ing = stats['ingestion']
            print(f"   - Fichiers ingérés: {ing.get('total_files', 0)}")
            print(f"   - Chunks: {ing.get('total_chunks', 0)}")
            print(f"   - Taille: {ing.get('total_size_kb', 0):.1f} KB")

        if 'vectorstore' in stats:
            vs = stats['vectorstore']
            if 'indexes' in vs:
                for idx in vs['indexes']:
                    print(f"   - Index '{idx['name']}': {idx.get('document_count', 0)} docs")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Point d'entrée principal"""
    print("\n" + "="*60)
    print("🎬 DÉMONSTRATION DU SYSTÈME RAG INTÉGRÉ")
    print("="*60)

    # Vérifier que les fichiers existent
    doc_path = "code_du_travail_ci.md"
    if not os.path.exists(doc_path):
        print(f"\n❌ ERREUR: Document manquant: {doc_path}")
        print(f"   Assurez-vous que le fichier existe dans le répertoire courant")
        return False

    # Vérifier les variables d'environnement
    from dotenv import load_dotenv
    load_dotenv()

    if not os.getenv("MISTRAL_API_KEY"):
        print(f"\n❌ ERREUR: MISTRAL_API_KEY manquante")
        print(f"   Configurez la clé API Mistral dans .env")
        return False

    try:
        # Exécuter les démos
        docs = demo_document_ingestion()
        if not docs:
            return False

        chunks = demo_chunking(docs)

        faiss_mgr = demo_indexing(chunks)

        demo_search(faiss_mgr)

        demo_rag_pipeline()

        # Résumé final
        print_header("✅ DÉMONSTRATION TERMINÉE")
        print("Le système RAG est opérationnel!")
        print("\n💡 Prochaines étapes:")
        print("   1. Voir RAG_INTEGRATION_GUIDE.md pour la documentation")
        print("   2. Utiliser RAGPipeline dans votre code")
        print("   3. Intégrer dans streamlit_app.py")
        print("   4. (Optionnel) Configurer pgvector pour production")

        return True

    except Exception as e:
        print(f"\n❌ ERREUR FATALE: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
