# 🤖 CLAUDE.md - JurisBot CI SaaS Context & Rules

## 🎯 PROJECT OVERVIEW
**JurisBot CI** is a B2B LegalTech SaaS designed for HR managers, lawyers, and employees in Côte d'Ivoire. 
It provides accurate, cited answers regarding the Ivorian Labor Law (Loi n° 2015-532) and the Interprofessional Collective Agreement.
The core engine is a RAG (Retrieval-Augmented Generation) system.

## 🛠️ TECH STACK (MVP Phase)
- **Backend / API:** Python 3.11+, FastAPI, Pydantic.
- **AI / RAG Orchestration:** LangChain (LCEL syntax), Mistral AI (`mistral-large-latest` for generation, `mistral-embed` for embeddings).
- **Vector Database:** FAISS (Local for MVP, must be easily swappable to Supabase pgvector later).
- **Frontend MVP:** Streamlit (Fast iteration, built-in chat UI).
- **Database (Future):** Supabase (PostgreSQL + Auth).
- **Payments (Future):** Paystack (Mobile Money / Card).

## ⚖️ DOMAIN RULES & GUARDRAILS (CRITICAL)
1. **NO HALLUCINATIONS:** The AI must answer STRICTLY based on the retrieved chunks from the Ivorian Labor Law.
2. **MANDATORY CITATIONS:** Every answer MUST end with the exact reference of the Article or Decree used (e.g., "Conformément à l'article 15.8...").
3. **FALLBACK PROTOCOL:** If the answer is not in the provided context, the AI must reply: *"Aucune disposition légale trouvée dans le Code actuel. Consultez un inspecteur du travail."*
4. **TONE:** Professional, neutral, pedagogical, and strictly legal. No moral or emotional advice.

## 📁 PROJECT STRUCTURE
```text
jurisbot-ci/
├── CLAUDE.md                 # This file
├── .env                      # Local secrets (gitignored)
├── .env.example              # Template
├── data/
│   └── code_du_travail_ci.md # The Knowledge Base
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI entrypoint
│   ├── core/
│   │   ├── config.py         # Pydantic settings
│   │   └── rag_engine.py     # LangChain LCEL pipeline
│   ├── api/
│   │   └── routes.py         # FastAPI endpoints
│   └── models/
│       └── schemas.py        # Pydantic request/response models
├── ui/
│   └── streamlit_app.py      # Streamlit MVP interface
└── requirements.txt