# 🚀 Guide d'Intégration Markdown → FAISS/pgvector

## Vue d'ensemble

Ce guide explique comment **intégrer vos fichiers Markdown dans FAISS (MVP) ou pgvector (production)** pour le système RAG JurisBot CI.

### Architecture

```
Fichiers Markdown (.md)
        ↓
DocumentIngestor (chargement + chunking)
        ↓
    FAISS (MVP)  ←→  pgvector (Production)
        ↓
   RAGPipeline (query + retrieval)
        ↓
  ChatMistralAI (LLM generation)
        ↓
    Réponses avec citations
```

---

## 🚀 Démarrage rapide

### 1️⃣ Installation initiale (une seule fois)

```bash
# Vérifier les dépendances et créer les index FAISS
python setup_rag.py
```

**Résultat attendu:**
```
✅ Configuration réussie!
📋 Rapport sauvegardé: setup_rag_report.json
```

### 2️⃣ Utiliser le RAG en Python

```python
from rag_pipeline import RAGPipeline

# Initialiser
pipeline = RAGPipeline()

# Poser une question
result = pipeline.query("Quels sont les droits en cas de licenciement ?")

print(result['answer'])
# Sources: result['sources']
```

### 3️⃣ Utiliser dans Streamlit

```python
import streamlit as st
from rag_pipeline import RAGPipeline

# Initialiser une seule fois
if "pipeline" not in st.session_state:
    st.session_state.pipeline = RAGPipeline()

# Afficher le chat
st.title("🤖 JurisBot CI")
question = st.text_input("Votre question:")
if question:
    result = st.session_state.pipeline.query(question)
    st.write(result['answer'])
    st.write(f"Sources: {len(result['sources'])} documents")
```

---

## 📁 Structure des fichiers créés

### Modules principaux

| Fichier | Utilité | Priorité |
|---------|---------|----------|
| `document_ingestion.py` | Charger/gérer les Markdown | 🔴 HAUTE |
| `faiss_manager.py` | Gérer les index FAISS | 🔴 HAUTE |
| `pgvector_manager.py` | Support pgvector (optionnel) | 🟠 MOYENNE |
| `rag_pipeline.py` | Pipeline RAG complet | 🔴 HAUTE |
| `setup_rag.py` | Script d'initialisation | 🟠 MOYENNE |

### Structure des répertoires créés

```
C:\Users\PC\Documents\Dev\Vibe Coding\CodeTravail\
├── faiss_indexes/          # Index FAISS sauvegardés
│   ├── droit_travail_ci/   # Index principal
│   └── droit_travail_ci_metadata.json
├── ingestion_logs/         # Logs d'ingestion
│   └── ingestion_history.json
└── hallucination_logs/     # Logs des hallucinations
```

---

## 💾 Charger des documents Markdown

### 1. Charger un fichier unique

```python
from document_ingestion import DocumentIngestor, chunk_documents_legal
from faiss_manager import FAISSManager

# 1. Ingérer le fichier
ingestor = DocumentIngestor()
docs, metadata = ingestor.load_markdown_file("code_du_travail_ci.md")

# 2. Découper en chunks
chunks = chunk_documents_legal(docs)

# 3. Créer l'index FAISS
faiss_mgr = FAISSManager()
faiss_mgr.create_index(chunks, "droit_travail_ci")

print(f"✅ {len(chunks)} chunks indexés")
```

### 2. Charger un répertoire complet

```python
from rag_pipeline import RAGPipeline

pipeline = RAGPipeline()

# Charger tous les .md d'un répertoire
result = pipeline.ingest_directory("./documents/")

print(f"✅ {result['chunks']} chunks ingérés")
```

### 3. Ajouter des documents à un index existant

```python
from rag_pipeline import RAGPipeline

pipeline = RAGPipeline()

# Ajouter sans détruire l'existant
result = pipeline.ingest_markdown("nouveau_document.md", add_to_existing=True)
```

---

## 🔍 Recherche et Query

### Recherche simple

```python
from faiss_manager import FAISSManager

faiss_mgr = FAISSManager()
faiss_mgr.load_index("droit_travail_ci")

# Rechercher
results = faiss_mgr.search("heures supplémentaires", k=5)

for doc, score in results:
    print(f"[{doc.metadata['source_ref']}] Score: {score:.2f}")
    print(doc.page_content[:200])
```

### Query complète avec RAG

```python
from rag_pipeline import RAGPipeline

pipeline = RAGPipeline()
result = pipeline.query("Combien de jours de congé ?")

# Réponse
print("Question:", result['query'])
print("Réponse:", result['answer'])

# Sources
for src in result['sources']:
    print(f"  - {src['ref']}")
```

---

## 🌊 Utiliser pgvector (Production)

### Configuration Supabase

1. **Créer une base PostgreSQL avec pgvector:**

```bash
# Via Supabase Dashboard:
# 1. Créer un projet Supabase
# 2. Activer l'extension pgvector
# 3. Récupérer les clés API
```

2. **Configurer les variables d'environnement:**

```bash
# .env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJhbGc...
MISTRAL_API_KEY=xxxxx
```

3. **Migrer les données:**

```python
from rag_pipeline import RAGPipeline

# Charger depuis FAISS
pipeline_faiss = RAGPipeline(backend="faiss")
pipeline_faiss.ingest_markdown("code_du_travail_ci.md")

# Migrer vers pgvector
pipeline_pg = RAGPipeline(backend="pgvector")
# Les mêmes documents seront ajoutés à pgvector
```

### Utilisation pgvector

```python
from rag_pipeline import RAGPipeline

# Auto-détection (utilise pgvector si SUPABASE_URL est configuré)
pipeline = RAGPipeline(backend="auto")

# Ou spécifier explicitement
pipeline = RAGPipeline(backend="pgvector")

# Utilisation identique à FAISS
result = pipeline.query("Votre question")
```

---

## 📊 Gestion des index FAISS

### Créer un nouvel index

```python
from faiss_manager import FAISSManager

faiss_mgr = FAISSManager()

# Créer avec un autre nom
faiss_mgr.create_index(chunks, "index_2024")
```

### Lister tous les index

```python
faiss_mgr = FAISSManager()
indexes = faiss_mgr.list_indexes()

for idx in indexes:
    print(f"{idx['name']}: {idx['document_count']} docs")
```

### Obtenir les statistiques

```python
stats = faiss_mgr.get_index_stats("droit_travail_ci")
print(f"Documents: {stats['document_count']}")
print(f"Taille: {stats['size_kb']:.1f} KB")
print(f"Types: {stats['document_types']}")
```

### Supprimer un index

```python
faiss_mgr.delete_index("ancien_index")
```

### Reconstruire un index

```python
# Supprime et crée un nouvel index
faiss_mgr.rebuild_index(new_chunks, "droit_travail_ci")
```

---

## 📋 Suivi de l'ingestion

### Voir l'historique d'ingestion

```python
from document_ingestion import DocumentIngestor

ingestor = DocumentIngestor()
summary = ingestor.get_ingestion_summary()

print(f"Fichiers ingérés: {summary['total_files']}")
print(f"Total chunks: {summary['total_chunks']}")
print(f"Taille totale: {summary['total_size_kb']:.1f} KB")

for file in summary['files']:
    print(f"  - {file['name']}: {file['chunks']} chunks")
```

### Exporter l'historique

```python
import json

ingestor = DocumentIngestor()
summary = ingestor.get_ingestion_summary()

with open("ingestion_report.json", "w") as f:
    json.dump(summary, f, indent=2)
```

---

## 🎯 Optimisation du Chunking

### Taille de chunk par défaut

```python
# Par défaut: 2000 caractères avec 400 de chevauchement
pipeline = RAGPipeline(chunk_size=2000, chunk_overlap=400)
```

### Personnaliser selon le type de document

```python
from document_ingestion import chunk_documents_legal

# Chunks plus petits (meilleure précision)
chunks = chunk_documents_legal(docs, chunk_size=1000, chunk_overlap=200)

# Chunks plus grands (plus de contexte)
chunks = chunk_documents_legal(docs, chunk_size=4000, chunk_overlap=800)
```

### Séparateurs utilisés

```python
legal_separators = [
    "\n## ",      # Sous-titres
    "\n### ",     # Sous-sous-titres
    "\nArt. ",    # Articles
    "\nARTICLE ",
    "\nCHAPITRE ",
    "\nSECTION ",
    "\nTITRE ",
    "\n\n",       # Paragraphes
    "\n",         # Lignes
    " ",          # Mots
    ""            # Caractères
]
```

---

## 🧪 Tests et validation

### Test rapide après initialisation

```bash
python setup_rag.py --quick
```

### Test complet du pipeline

```python
from rag_pipeline import RAGPipeline

pipeline = RAGPipeline()

# Ingérer
pipeline.ingest_markdown("code_du_travail_ci.md")

# Tester plusieurs queries
test_queries = [
    "Quels sont les droits en cas de licenciement ?",
    "Combien de jours de congé annuel ?",
    "Quel est le salaire minimum ?",
    "Quelles sont les règles sur les heures supplémentaires ?",
]

for q in test_queries:
    result = pipeline.query(q)
    print(f"Q: {q}")
    print(f"A: {result['answer'][:100]}...\n")
```

### Vérifier les hallucinations

```python
from rag_pipeline import RAGPipeline

pipeline = RAGPipeline()

result = pipeline.query("Question arbitraire")

# Vérifier les sources réelles
if result['sources']:
    for src in result['sources']:
        print(f"Source vérifiée: {src['ref']}")
else:
    print("⚠️ Aucune source trouvée - possible hallucination")
```

---

## 🔧 Troubleshooting

### Erreur: "MISTRAL_API_KEY manquante"

```bash
# Solution
echo "MISTRAL_API_KEY=your-key-here" > .env
```

### Erreur: "Index not found"

```python
# Vérifier quels index existent
faiss_mgr = FAISSManager()
indexes = faiss_mgr.list_indexes()
print([idx['name'] for idx in indexes])

# Recréer l'index
pipeline = RAGPipeline()
pipeline.ingest_markdown("code_du_travail_ci.md")
```

### Performances lentes

```python
# Augmenter le nombre de workers (si disponible)
# Réduire la taille de k (nombre de résultats)
results = retriever.invoke(query)  # Défaut: k=5

# Ou réduire la taille des chunks
pipeline = RAGPipeline(chunk_size=1000)
```

### pgvector: "Table not found"

```python
# Créer la table
from pgvector_manager import PGVectorManager

pg_mgr = PGVectorManager()
pg_mgr.create_table()
```

---

## 📚 API Reference

### DocumentIngestor

```python
ingestor = DocumentIngestor()

# Charger un fichier
docs, metadata = ingestor.load_markdown_file("file.md")

# Charger un répertoire
docs, metadata_list = ingestor.load_markdown_directory("./docs/")

# Charger plusieurs fichiers
docs, metadata_list = ingestor.load_batch(["file1.md", "file2.md"])

# Voir les stats
summary = ingestor.get_ingestion_summary()
```

### FAISSManager

```python
faiss_mgr = FAISSManager()

# Créer un index
path = faiss_mgr.create_index(documents, "index_name")

# Charger un index
faiss_mgr.load_index("index_name")

# Rechercher
results = faiss_mgr.search(query, k=5)

# Ajouter des docs
faiss_mgr.add_documents(docs, "index_name")

# Obtenir un retriever
retriever = faiss_mgr.get_retriever(k=5)

# Stats
stats = faiss_mgr.get_index_stats("index_name")
```

### RAGPipeline

```python
pipeline = RAGPipeline(backend="auto")

# Ingérer
result = pipeline.ingest_markdown("file.md")
result = pipeline.ingest_directory("./docs/")

# Query
result = pipeline.query("Your question")

# Stats
stats = pipeline.get_stats()
status = pipeline.get_status()
```

---

## 🎓 Exemple complet: Intégration avec Streamlit

```python
import streamlit as st
from rag_pipeline import RAGPipeline

st.set_page_config(page_title="JurisBot CI", layout="wide")

# Initialiser
if "pipeline" not in st.session_state:
    with st.spinner("Chargement du RAG..."):
        st.session_state.pipeline = RAGPipeline()

st.title("⚖️ JurisBot CI - Assistant Juridique Ivoirien")

# Sidebar
with st.sidebar:
    st.header("ℹ️ Informations")
    stats = st.session_state.pipeline.get_status()
    st.write(f"Backend: {stats['backend']}")
    st.write(f"Retriever: {'Chargé ✅' if stats['retriever_loaded'] else 'Non chargé'}")

# Chat
col1, col2 = st.columns([3, 1])

with col1:
    question = st.text_input("Posez votre question sur le droit du travail ivoirien:")

if question:
    with st.spinner("Recherche en cours..."):
        result = st.session_state.pipeline.query(question)

    if result['status'] == 'success':
        st.write("### 📝 Réponse")
        st.write(result['answer'])

        with st.expander("📚 Sources"):
            for i, src in enumerate(result['sources'], 1):
                st.write(f"**{i}. {src['ref']}**")
                st.text(src['snippet'])
    else:
        st.error(f"Erreur: {result['message']}")
```

---

## 📞 Support et questions

Pour des questions ou problèmes:
1. Vérifier le fichier log: `setup_rag_report.json`
2. Consulter les fichiers dans `ingestion_logs/`
3. Vérifier les métadonnées: `faiss_indexes/*_metadata.json`

---

## 📝 Notes importantes

1. **FAISS est MVP**, pgvector est recommandé pour la production
2. **Chunking optimal** pour textes juridiques déjà configuré
3. **Métadonnées enrichies** conservent les références sources
4. **Auto-détection backend** basée sur variables d'environnement
5. **Historique d'ingestion** suivi automatiquement

---

**Créé pour:** JurisBot CI  
**Dernière mise à jour:** 2026-07-09  
**Version:** 1.0 - MVP
