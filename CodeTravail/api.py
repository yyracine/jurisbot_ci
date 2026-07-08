import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Importation du moteur RAG
from bot_juridique import init_rag_engine, ask_legal_bot

# ==========================================
# 1. CONFIGURATION & ENVIRONNEMENT
# ==========================================
load_dotenv()

# ==========================================
# 2. POST-PROCESSING ANTI-HALLUCINATION
# ==========================================
# La correction est désormais centralisée dans bot_juridique.verify_and_correct_citations,
# qui dispose du CONTEXTE RÉELLEMENT RÉCUPÉRÉ (liste blanche des numéros officiels,
# neutralisation des attributions parasites). L'API ne doit PAS re-corriger une
# seconde fois avec l'ancienne logique en dur : cela doublonnait et pouvait
# réintroduire des erreurs. Voir RAPPORT_ANALYSE.md (Correction 5).
def correct_citations_in_answer(answer: str) -> str:
    """Deprecated : conservée par compatibilité. Ne fait rien (no-op)."""
    return answer

# ==========================================
# 3. INITIALISATION FASTAPI
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🧠 Chargement du Code du Travail et indexation vectorielle...")
    app.state.retriever, app.state.llm, app.state.hybrid = init_rag_engine()
    print("✅ Moteur RAG initialisé et prêt !")
    yield

app = FastAPI(
    title="JurisBot CI - API SaaS",
    description="API de droit du travail ivoirien propulsée par Mistral AI",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 4. AUTHENTIFICATION & BASE DE DONNÉES (MOCK)
# ==========================================
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

MOCK_SAAS_DB = {
    "token_pme_abidjan_123": {"user_id": "u_001", "company": "PME Abidjan", "quota": 50},
    "token_cabinet_juridique_456": {"user_id": "u_002", "company": "Cabinet Avocats", "quota": 500},
}

async def verify_quota(api_key: str = Depends(api_key_header)):
    if not api_key or api_key not in MOCK_SAAS_DB:
        raise HTTPException(status_code=401, detail="Clé API invalide ou manquante.")
    if MOCK_SAAS_DB[api_key]["quota"] <= 0:
        raise HTTPException(status_code=429, detail="Quota mensuel épuisé.")
    return MOCK_SAAS_DB[api_key]

# ==========================================
# 5. MODÈLES PYDANTIC
# ==========================================
class QuestionRequest(BaseModel):
    query: str

class SourceDocument(BaseModel):
    source_name: str
    snippet: str

class QuestionResponse(BaseModel):
    answer: str
    sources: list[SourceDocument]
    quota_remaining: int

# ==========================================
# 6. ENDPOINTS
# ==========================================
@app.get("/")
def read_root():
    return {
        "message": "Bienvenue sur l'API JurisBot CI",
        "status": "online",
        "docs": "http://127.0.0.1:8000/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/v1/ask", response_model=QuestionResponse)
async def ask_legal_question(
    request: Request,
    payload: QuestionRequest,
    user_data: dict = Depends(verify_quota)
):
    """Route principale pour poser une question juridique."""
    try:
        # 1. Appel du bot
        result = ask_legal_bot(
            query=payload.query,
            retriever=request.app.state.retriever,
            llm=request.app.state.llm,
            hybrid=request.app.state.hybrid,
        )
        
        # 2. ✅ CORRECTION DIRECTE DANS API.PY
        final_answer = correct_citations_in_answer(result["answer"])
        
        print(f"\n📤 RÉPONSE FINALE ENVOYÉE AU FRONTEND :\n{final_answer}\n")
        print(f"📤 FIN DE LA RÉPONSE\n")
        
        # 3. Formatage des sources
        formatted_sources = [
            SourceDocument(source_name=src["source_ref"], snippet=src["snippet"]) 
            for src in result["sources"]
        ]
        
        # 4. Mise à jour du quota
        api_key = request.headers.get("X-API-Key")
        MOCK_SAAS_DB[api_key]["quota"] -= 1
        
        # 5. ✅ Retourner final_answer (la version corrigée)
        return QuestionResponse(
            answer=final_answer,
            sources=formatted_sources,
            quota_remaining=MOCK_SAAS_DB[api_key]["quota"]
        )
        
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE API : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

@app.get("/api/v1/me")
async def get_my_profile(user_data: dict = Depends(verify_quota)):
    return {
        "company": user_data["company"],
        "questions_remaining": user_data["quota"]
    }

@app.get("/api/v1/quota")
async def get_quota(user_data: dict = Depends(verify_quota)):
    return {
        "quota_remaining": user_data["quota"],
        "company": user_data["company"]
    }