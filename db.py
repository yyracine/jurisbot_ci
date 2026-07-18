"""
Database module - Supabase PostgreSQL backend
Remplace SQLite par une base de données centralisée
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
import os

load_dotenv(override=True)

# Import Supabase client
from supabase import create_client, Client

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

supabase: Client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"⚠️ Warning: Could not connect to Supabase: {e}")
else:
    print("⚠️ Warning: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not configured")

LOG_FILE = Path("debug_db.log")

def log_action(action: str, details: str = ""):
    """Écrit un log dans le fichier de debug"""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            f.write(f"[{timestamp}] {action}: {details}\n")
    except:
        pass

def init_db():
    """Initialise la connexion à Supabase (les tables existent déjà)"""
    if supabase:
        log_action("INIT_DB", "✅ Supabase connection initialized")
    else:
        print("❌ Supabase not configured - database features will be limited")

def add_response(
    response_id: str,
    query: str,
    answer: str,
    sources: Optional[List] = None,
    hallucination_score: float = 0.0,
    is_hallucinating: bool = False,
    model: str = "mistral-large-latest",
    retriever: str = "FAISS",
    embedding_model: str = "mistral-embed"
) -> bool:
    """Ajoute une réponse à Supabase"""
    if not supabase:
        return True

    log_action("ADD_RESPONSE", f"ID: {response_id}, Query: {query[:50]}")

    try:
        data = {
            "id": response_id,
            "query": query,
            "answer": answer,
            "sources": sources or [],
            "hallucination_score": hallucination_score,
            "is_hallucinating": is_hallucinating,
            "model": model,
            "retriever": retriever,
            "embedding_model": embedding_model,
        }

        response = supabase.table("responses").insert(data).execute()

        log_action("ADD_RESPONSE", f"✅ SUCCESS - ID: {response_id}")
        return True
    except Exception as e:
        log_action("ADD_RESPONSE", f"❌ ERROR: {str(e)}")
        return False

def add_feedback(
    response_id: str,
    feedback_type: str = "quick",
    feedback: str = None,
    is_hallucination: bool = False,
    accuracy: int = None,
    clarity: int = None,
    citations: int = None,
    completeness: int = None,
    comments: str = None,
    email: str = None
) -> bool:
    """Ajoute un feedback à Supabase"""
    if not supabase:
        return True

    log_action("ADD_FEEDBACK", f"Type: {feedback_type}, ResponseID: {response_id}, Email: {email}")

    try:
        data = {
            "response_id": response_id,
            "feedback_type": feedback_type,
            "feedback": feedback,
            "is_hallucination": is_hallucination,
            "accuracy": accuracy,
            "clarity": clarity,
            "citations": citations,
            "completeness": completeness,
            "comments": comments,
            "email": email,
        }

        response = supabase.table("feedbacks").insert(data).execute()

        log_action("ADD_FEEDBACK", f"✅ SUCCESS - ResponseID: {response_id}")
        return True
    except Exception as e:
        log_action("ADD_FEEDBACK", f"❌ ERROR: {str(e)}")
        return False

def add_alert(response_id: str, hallucination_description: str) -> bool:
    """Ajoute une alerte à Supabase"""
    if not supabase:
        return True

    try:
        data = {
            "response_id": response_id,
            "hallucination_description": hallucination_description,
        }

        supabase.table("alerts").insert(data).execute()
        return True
    except Exception as e:
        print(f"Erreur lors de l'ajout de l'alerte: {e}")
        return False

def get_response(response_id: str) -> Optional[Dict[str, Any]]:
    """Récupère une réponse par son ID"""
    if not supabase:
        return None

    try:
        response = supabase.table("responses").select("*").eq("id", response_id).execute()

        if response.data:
            return dict(response.data[0])
        return None
    except Exception as e:
        print(f"Erreur lors de la récupération de la réponse: {e}")
        return None

def get_all_responses() -> List[Dict[str, Any]]:
    """Récupère toutes les réponses"""
    if not supabase:
        return []

    try:
        response = supabase.table("responses").select("*").order("created_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"Erreur lors de la récupération des réponses: {e}")
        return []

def get_all_feedbacks() -> List[Dict[str, Any]]:
    """Récupère tous les feedbacks"""
    if not supabase:
        return []

    try:
        response = supabase.table("feedbacks").select("*").order("created_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"Erreur lors de la récupération des feedbacks: {e}")
        return []

def get_feedbacks_for_response(response_id: str) -> List[Dict[str, Any]]:
    """Récupère les feedbacks pour une réponse spécifique"""
    if not supabase:
        return []

    try:
        response = supabase.table("feedbacks").select("*").eq("response_id", response_id).order("created_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"Erreur lors de la récupération des feedbacks: {e}")
        return []

def get_stats() -> Dict[str, Any]:
    """Récupère les statistiques générales"""
    if not supabase:
        return {
            "total_responses": 0,
            "hallucinations_detected": 0,
            "hallucination_rate": 0.0,
            "average_hallucination_score": 0.0,
            "responses_by_score": []
        }

    try:
        # Total responses
        responses_data = supabase.table("responses").select("id").execute()
        total_responses = len(responses_data.data or [])

        # Hallucinations detected
        hallucinations_data = supabase.table("responses").select("id").eq("is_hallucinating", True).execute()
        hallucinations_detected = len(hallucinations_data.data or [])

        # Average hallucination score
        all_responses = supabase.table("responses").select("hallucination_score").execute()
        scores = [r["hallucination_score"] for r in (all_responses.data or []) if r.get("hallucination_score")]
        avg_hallucination_score = sum(scores) / len(scores) if scores else 0.0

        hallucination_rate = (hallucinations_detected / total_responses * 100) if total_responses > 0 else 0

        return {
            "total_responses": total_responses,
            "hallucinations_detected": hallucinations_detected,
            "hallucination_rate": hallucination_rate,
            "average_hallucination_score": avg_hallucination_score,
            "responses_by_score": scores
        }
    except Exception as e:
        print(f"Erreur lors de la récupération des stats: {e}")
        return {
            "total_responses": 0,
            "hallucinations_detected": 0,
            "hallucination_rate": 0.0,
            "average_hallucination_score": 0.0,
            "responses_by_score": []
        }

def get_feedback_stats() -> Dict[str, Any]:
    """Récupère les statistiques des feedbacks"""
    if not supabase:
        return {}

    try:
        feedbacks_data = supabase.table("feedbacks").select("*").execute()
        feedbacks = feedbacks_data.data or []

        total_feedbacks = len(feedbacks)
        detailed_feedbacks = len([f for f in feedbacks if f.get("feedback_type") == "detailed"])

        # Calculate averages
        accuracies = [f["accuracy"] for f in feedbacks if f.get("accuracy")]
        clarities = [f["clarity"] for f in feedbacks if f.get("clarity")]
        citations_scores = [f["citations"] for f in feedbacks if f.get("citations")]
        completeness_scores = [f["completeness"] for f in feedbacks if f.get("completeness")]

        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
        avg_clarity = sum(clarities) / len(clarities) if clarities else 0
        avg_citations = sum(citations_scores) / len(citations_scores) if citations_scores else 0
        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0

        return {
            "total_feedbacks": total_feedbacks,
            "detailed_feedbacks": detailed_feedbacks,
            "avg_accuracy": avg_accuracy,
            "avg_clarity": avg_clarity,
            "avg_citations": avg_citations,
            "avg_completeness": avg_completeness
        }
    except Exception as e:
        print(f"Erreur lors de la récupération des stats feedbacks: {e}")
        return {}

def export_all_data() -> Dict[str, Any]:
    """Exporte toutes les données"""
    if not supabase:
        return {}

    try:
        responses_data = supabase.table("responses").select("*").order("created_at", desc=True).execute()
        feedbacks_data = supabase.table("feedbacks").select("*").order("created_at", desc=True).execute()
        alerts_data = supabase.table("alerts").select("*").order("created_at", desc=True).execute()

        return {
            "responses": responses_data.data or [],
            "feedbacks": feedbacks_data.data or [],
            "alerts": alerts_data.data or [],
            "export_timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Erreur lors de l'export: {e}")
        return {}

def check_user_quota(user_email: str, max_per_day: int = 100) -> bool:
    """Vérifie si l'utilisateur a atteint son quota quotidien"""
    if not supabase:
        return True

    try:
        from datetime import date
        today = date.today().isoformat()

        response = supabase.table("responses").select("id").eq("user_email", user_email).gte("created_at", today).execute()
        count = len(response.data) if response.data else 0

        if count >= max_per_day:
            log_action("QUOTA_EXCEEDED", f"User {user_email}: {count}/{max_per_day}")
            return False

        log_action("QUOTA_CHECK", f"User {user_email}: {count}/{max_per_day}")
        return True
    except Exception as e:
        log_action("QUOTA_CHECK_ERROR", f"Error checking quota for {user_email}: {str(e)}")
        return True

def clear_all_data() -> bool:
    """Purge toutes les données de Supabase"""
    if not supabase:
        return True

    try:
        # Delete in correct order (foreign keys)
        # Pour les tables avec IDs numériques (BIGSERIAL)
        supabase.table("feedbacks").delete().gte("id", 1).execute()
        supabase.table("alerts").delete().gte("id", 1).execute()
        supabase.table("chat_sessions").delete().gte("id", 1).execute()

        # Pour responses avec IDs TEXT, on utilise ilike
        supabase.table("responses").delete().ilike("id", "%").execute()

        log_action("CLEAR_ALL_DATA", "✅ SUCCESS - All data cleared")
        return True
    except Exception as e:
        log_action("CLEAR_ALL_DATA", f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    init_db()
    print("✅ Base de données Supabase configurée!")
