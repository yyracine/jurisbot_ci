import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import de votre moteur RAG mis à jour
from old.bot_juridique_old import build_rag_engine

# 1. Charger les variables d'environnement
load_dotenv()

# ==========================================
# 2. INITIALISATION FASTAPI & RATE LIMITER
# ==========================================
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(" Chargement du Code du Travail et indexation vectorielle...")
    app.state.rag_chain, app.state.retriever = build_rag_engine()
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 3. AUTHENTIFICATION & BASE DE DONNÉES (MOCK)
# ==========================================
# ==========================================
# 3. AUTHENTIFICATION & BASE DE DONNÉES (MOCK)
# ==========================================
from fastapi.security import APIKeyHeader

# FastAPI cherchera un header nommé "X-API-Key"
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

MOCK_SAAS_DB = {
    "token_pme_abidjan_123": {"user_id": "u_001", "company": "PME Abidjan", "quota_questions": 50},
    "token_cabinet_juridique_456": {"user_id": "u_002", "company": "Cabinet Avocats", "quota_questions": 500},
}

async def get_current_user(api_key: str = Depends(api_key_header)):
    if not api_key or api_key not in MOCK_SAAS_DB:
        raise HTTPException(status_code=401, detail="Clé API invalide ou manquante. Souscrivez un abonnement.")
    
    user_data = MOCK_SAAS_DB[api_key]
    if user_data["quota_questions"] <= 0:
        raise HTTPException(status_code=429, detail="Quota mensuel épuisé.")
    
    return user_data

# ==========================================
# 4. MODÈLES PYDANTIC
# ==========================================
class QuestionRequest(BaseModel):
    query: str

class SourceDocument(BaseModel):
    content_snippet: str
    article_reference: str

class QuestionResponse(BaseModel):
    answer: str
    sources: list[SourceDocument]
    quota_remaining: int

# ==========================================
# 5. ENDPOINT PRINCIPAL
# ==========================================
@app.post("/api/v1/ask", response_model=QuestionResponse)
@limiter.limit("30/minute")
async def ask_legal_question(
    request: Request,
    payload: QuestionRequest,
    user_data: dict = Depends(get_current_user)
):
    try:
        retriever = request.app.state.retriever
        rag_chain = request.app.state.rag_chain
        
        docs = retriever.invoke(payload.query)
        sources = []
        
        for doc in docs:
            source_ref = doc.metadata.get("source_ref", "Non spécifié")
            article_ref = "Non spécifié"
            for line in doc.page_content.split('\n'):
                if "Art." in line or "ARTICLE" in line or "ART." in line or "Décret" in line:
                    article_ref = line.strip()[:80]
                    break
            
            full_ref = f"{source_ref} | {article_ref}"
            snippet = doc.page_content[:200].replace('\n', ' ') + "..."
            sources.append(SourceDocument(content_snippet=snippet, article_reference=full_ref))

        answer = rag_chain.invoke(payload.query)
        
        MOCK_SAAS_DB[user_data["user_id"]]["quota_questions"] -= 1
        
        return QuestionResponse(
            answer=answer,
            sources=sources,
            quota_remaining=MOCK_SAAS_DB[user_data["user_id"]]["quota_questions"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement juridique : {str(e)}")

@app.get("/")
def read_root():
    return {
        "message": "Bienvenue sur l'API JurisBot CI",
        "status": "online",
        "docs": "http://127.0.0.1:8000/docs",
        "endpoints": {
            "POST /api/v1/ask": "Poser une question juridique",
            "GET /api/v1/quota": "Vérifier le quota restant"
        }
    }