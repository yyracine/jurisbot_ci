import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Importation du moteur RAG
from old.bot_juridique_old2 import init_rag_engine, ask_legal_bot

# 1. Chargement des variables d'env
load_dotenv()

# 2. Configuration FastAPI
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🧠 Chargement du Code du Travail et indexation vectorielle...")
    app.state.retriever, app.state.llm = init_rag_engine()
    print("✅ Moteur RAG initialisé et prêt !")
    yield

app = FastAPI(
    title="JurisBot CI - API SaaS",
    description="API de droit du travail ivoirien propulsée par Mistral AI",
    version="1.0.0",
    lifespan=lifespan
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS (Autoriser le frontend à appeler l'API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Authentification et Quotas (Mode Mock pour le MVP)
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

# 4. Modèles de données (Pydantic)
class QuestionRequest(BaseModel):
    query: str

class SourceDocument(BaseModel):
    source_name: str
    snippet: str

class QuestionResponse(BaseModel):
    answer: str
    sources: list[SourceDocument]
    quota_remaining: int

# 5. Routes de l'API

@app.get("/")
def read_root():
    """Route racine - Vérification que l'API est en ligne"""
    return {
        "message": "Bienvenue sur l'API JurisBot CI",
        "status": "online",
        "docs": "http://127.0.0.1:8000/docs"
    }

@app.get("/health")
def health_check():
    """Route de vérification de santé de l'API"""
    return {"status": "healthy"}

@app.post("/api/v1/ask", response_model=QuestionResponse)
@limiter.limit("30/minute")
async def ask_legal_question(
    request: Request,
    payload: QuestionRequest,
    user_data: dict = Depends(verify_quota)
):
    """
    Route principale pour poser une question juridique.
    
    - **query**: La question juridique à poser
    - Retourne la réponse de l'IA avec les sources juridiques
    """
    try:
        # Appel de la fonction robuste du bot
        result = ask_legal_bot(
            query=payload.query, 
            retriever=request.app.state.retriever, 
            llm=request.app.state.llm
        )
        
        print(f"\n📤 RÉPONSE ENVOYÉE AU FRONTEND (COMPLÈTE) :\n{result['answer']}\n")
        print(f" FIN DE LA RÉPONSE ENVOYÉE\n")
        
        
        # Formatage des sources pour le frontend
        formatted_sources = [
            SourceDocument(source_name=src["source_ref"], snippet=src["snippet"]) 
            for src in result["sources"]
        ]
        
        # Mise à jour du quota
        api_key = request.headers.get("X-API-Key")
        MOCK_SAAS_DB[api_key]["quota"] -= 1
        
        return QuestionResponse(
            answer=result["answer"],
            sources=formatted_sources,
            quota_remaining=MOCK_SAAS_DB[api_key]["quota"]
        )
        
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE API : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur IA : {str(e)}")

@app.get("/api/v1/me")
async def get_my_profile(user_data: dict = Depends(verify_quota)):
    """Route pour récupérer les informations de l'utilisateur connecté"""
    return {
        "company": user_data["company"],
        "questions_remaining": user_data["quota"]
    }

@app.get("/api/v1/quota")
async def get_quota(user_data: dict = Depends(verify_quota)):
    """Route pour vérifier le quota restant"""
    return {
        "quota_remaining": user_data["quota"],
        "company": user_data["company"]
    }