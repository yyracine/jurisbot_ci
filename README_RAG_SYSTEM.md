# 🚀 Système RAG - Intégration Markdown → FAISS/pgvector

**JurisBot CI** - Assistant juridique IA pour le droit du travail ivoirien

---

## ⚡ Démarrage rapide (2 minutes)

### 1. Initialiser le système

```bash
python setup_rag.py
```

### 2. Utiliser dans votre code Python

```python
from rag_pipeline import RAGPipeline

# Initialiser
pipeline = RAGPipeline()

# Poser une question
result = pipeline.query("Quels sont les droits en cas de licenciement ?")

print(result['answer'])
```

### 3. Voir les sources

```python
for src in result['sources']:
    print(f"Source: {src['ref']}")
    print(f"Extrait: {src['snippet']}")
```

---

## 📦 Qu'est-ce que vous avez

✅ **Système RAG complet** (Retrieval-Augmented Generation)  
✅ **Index FAISS** prêt à l'emploi  
✅ **Support pgvector** pour production  
✅ **Pipeline intégré** pour ingestion → indexation → query  
✅ **Documentation exhaustive** (600+ lignes)  

---

## 🎯 Architecture

```
Fichiers Markdown (.md)
    ↓ DocumentIngestor
Chunks + Métadonnées
    ↓ FAISS / pgvector
Index Vectoriel
    ↓ RAGPipeline
Recherche + LLM
    ↓ ChatMistralAI
Réponses avec citations
```

---

## 📂 Fichiers de ce système

### Modules (à importer)

| Fichier | Utilité |
|---------|---------|
| `document_ingestion.py` | Charger les fichiers Markdown |
| `faiss_manager.py` | Gérer l'index FAISS |
| `pgvector_manager.py` | Support Supabase pgvector |
| `rag_pipeline.py` | **Pipeline RAG complet** ⭐ |

### Scripts (à exécuter)

| Script | Utilité |
|--------|---------|
| `setup_rag.py` | **Initialisation complète** ⭐ |
| `demo_rag.py` | Démonstration interactive |

### Documentation

| Fichier | Contenu |
|---------|---------|
| `RAG_INTEGRATION_GUIDE.md` | **Guide complet** (600+ lignes) ⭐ |
| `INTEGRATION_SUMMARY.md` | Résumé exécutif |
| `README_RAG_SYSTEM.md` | Ce fichier |

---

## 🔥 Cas d'usage courants

### ✅ Query simple

```python
from rag_pipeline import RAGPipeline

pipeline = RAGPipeline()
result = pipeline.query("Ma question")
print(result['answer'])
```

### ✅ Ajouter un nouveau document

```python
pipeline.ingest_markdown("nouveau_decret.md", add_to_existing=True)
```

### ✅ Utiliser dans Streamlit

```python
import streamlit as st
from rag_pipeline import RAGPipeline

if "pipeline" not in st.session_state:
    st.session_state.pipeline = RAGPipeline()

question = st.text_input("Question:")
if question:
    result = st.session_state.pipeline.query(question)
    st.write(result['answer'])
```

### ✅ Utiliser dans une API FastAPI

```python
from fastapi import FastAPI
from rag_pipeline import RAGPipeline

app = FastAPI()
pipeline = RAGPipeline()

@app.post("/ask")
def ask(query: str):
    return pipeline.query(query)
```

### ✅ Migrer vers pgvector (production)

```bash
# 1. Configurer les variables d'environnement
export SUPABASE_URL=https://xxx.supabase.co
export SUPABASE_KEY=your-key

# 2. Utiliser pgvector
python -c "from rag_pipeline import RAGPipeline; p = RAGPipeline(backend='pgvector'); p.ingest_markdown('code_du_travail_ci.md')"
```

---

## 📊 Statistiques

| Métrique | Valeur |
|----------|--------|
| **Total code** | 2000+ lignes |
| **Modules** | 6 |
| **Documentation** | 1000+ lignes |
| **Temps setup initial** | ~30 secondes |
| **Temps par query** | ~2-3 secondes |
| **Chunks indexés** | ~300-400 |
| **Type de Backend MVP** | FAISS |

---

## 🔍 Vérifier que tout fonctionne

```bash
# Option 1: Setup complet
python setup_rag.py

# Option 2: Demo interactive
python demo_rag.py

# Option 3: Test rapide en Python
python -c "
from rag_pipeline import RAGPipeline
p = RAGPipeline()
p.ingest_markdown('code_du_travail_ci.md')
r = p.query('Quels sont les droits ?')
print('✅ OK' if r['status'] == 'success' else '❌ ERREUR')
"
```

---

## 🛠️ Configuration

### Variables d'environnement obligatoires

```bash
# .env
MISTRAL_API_KEY=your-api-key
```

### Variables optionnelles (pgvector)

```bash
# .env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-anon-key
```

---

## 📚 Documentations disponibles

### Pour démarrer rapidement
→ **Ce fichier** (README_RAG_SYSTEM.md)

### Pour comprendre le système
→ **INTEGRATION_SUMMARY.md** (comparaison avant/après)

### Pour tous les détails
→ **RAG_INTEGRATION_GUIDE.md** (600+ lignes)

### Pour explorer interactivement
→ **demo_rag.py** (démonstration pas à pas)

---

## 🐛 Troubleshooting rapide

### ❌ "MISTRAL_API_KEY manquante"
```bash
echo "MISTRAL_API_KEY=your-key" > .env
```

### ❌ "Module not found"
```bash
pip install langchain langchain-mistralai langchain-community faiss-cpu python-dotenv
```

### ❌ "Index not found"
```python
# Recréer l'index
python setup_rag.py --rebuild
```

### ❌ "pgvector connection error"
```bash
# Vérifier les clés Supabase
export SUPABASE_URL=https://xxx.supabase.co
export SUPABASE_KEY=your-key
```

---

## 💡 Points importants

1. **FAISS est MVP** - Local, rapide, aucune config cloud
2. **Métadonnées conservées** - Chaque chunk garde la source
3. **Historique tracké** - JSON enregistre les ingestions
4. **Interface unifiée** - Même API pour FAISS et pgvector
5. **Logging complet** - Facile de déboguer

---

## 🎓 Exemples complets

### Exemple 1: Setup initial

```python
from rag_pipeline import RAGPipeline
from document_ingestion import chunk_documents_legal

# Initialiser
pipeline = RAGPipeline()

# Ingérer le document principal
result = pipeline.ingest_markdown("code_du_travail_ci.md")

print(f"✅ {result['chunks']} chunks indexés")
```

### Exemple 2: Ajouter plusieurs documents

```python
pipeline = RAGPipeline()

docs = [
    "code_du_travail_ci.md",
    "convention_collective.md",
    "arretes_2024.md"
]

for doc in docs:
    pipeline.ingest_markdown(doc, add_to_existing=True)
    print(f"✅ {doc} ajouté")
```

### Exemple 3: Chat simple avec Streamlit

```python
import streamlit as st
from rag_pipeline import RAGPipeline

st.title("⚖️ JurisBot CI")

if "pipeline" not in st.session_state:
    with st.spinner("Chargement..."):
        st.session_state.pipeline = RAGPipeline()

question = st.text_input("Votre question sur le droit du travail:")

if question:
    with st.spinner("Recherche..."):
        result = st.session_state.pipeline.query(question)
    
    st.write(result['answer'])
    
    with st.expander("Voir les sources"):
        for src in result['sources']:
            st.write(f"**{src['ref']}**")
```

### Exemple 4: API FastAPI

```python
from fastapi import FastAPI
from rag_pipeline import RAGPipeline

app = FastAPI(title="JurisBot CI API")
pipeline = RAGPipeline()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ask")
def ask(query: str):
    result = pipeline.query(query)
    return {
        "answer": result['answer'],
        "sources": result.get('sources', [])
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 📖 API Rapide

### RAGPipeline

```python
# Initialiser
pipeline = RAGPipeline(backend="auto", index_name="droit_travail_ci")

# Ingérer
pipeline.ingest_markdown("file.md")
pipeline.ingest_directory("./docs/")

# Query
result = pipeline.query("Votre question")

# Stats
stats = pipeline.get_stats()
status = pipeline.get_status()
```

### DocumentIngestor

```python
from document_ingestion import DocumentIngestor, chunk_documents_legal

ingestor = DocumentIngestor()

# Charger
docs, meta = ingestor.load_markdown_file("file.md")
docs, metas = ingestor.load_markdown_directory("./docs/")

# Chunking
chunks = chunk_documents_legal(docs, chunk_size=2000, chunk_overlap=400)

# Stats
summary = ingestor.get_ingestion_summary()
```

### FAISSManager

```python
from faiss_manager import FAISSManager

mgr = FAISSManager()

# Index
mgr.create_index(documents, "my_index")
mgr.load_index("my_index")
mgr.add_documents(docs, "my_index")

# Recherche
results = mgr.search("query", k=5)

# Retriever
retriever = mgr.get_retriever(k=5)
```

---

## ✨ Prochaines étapes

1. **Immédiat:** Exécuter `python setup_rag.py`
2. **Court terme:** Intégrer RAGPipeline dans streamlit_app.py
3. **Moyen terme:** Mettre à jour api.py
4. **Long terme:** Configurer pgvector pour production

---

## 📞 Besoin d'aide ?

1. Vérifier `RAG_INTEGRATION_GUIDE.md` (section Troubleshooting)
2. Lancer `python demo_rag.py` pour une démo interactive
3. Vérifier les logs: `setup_rag_report.json`
4. Consulter les fichiers de configuration: `faiss_indexes/*_metadata.json`

---

**Version:** 1.0 MVP  
**Date:** 2026-07-09  
**Contact:** racine.yao@gmail.com

---

🚀 **Prêt à démarrer?** → `python setup_rag.py`
