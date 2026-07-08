from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from monitoring import get_monitor
from hallucination_detector import HallucinationDetector
import json

app = FastAPI(title="JurisBot Feedback API", version="1.0")

# Initialiser le monitor et le détecteur
monitor = get_monitor()
detector = HallucinationDetector()

# ==========================================
# MODÈLES PYDANTIC
# ==========================================

class FeedbackRequest(BaseModel):
    """Modèle pour soumettre un feedback utilisateur"""
    response_id: str
    feedback: str  # "thumbs_up" | "thumbs_down"
    is_hallucination: bool = False
    details: Optional[str] = None
    user_id: Optional[str] = None


class AnalyzeRequest(BaseModel):
    """Modèle pour analyser une réponse"""
    answer: str
    sources: Optional[List[dict]] = None
    query: Optional[str] = None


class StatsResponse(BaseModel):
    """Modèle pour les statistiques"""
    total_responses: int
    total_feedback: int
    hallucinations_detected: int
    false_positive_rate: float
    recent_alerts: List[dict]


# ==========================================
# ENDPOINTS
# ==========================================

@app.post("/feedback/submit")
async def submit_feedback(request: FeedbackRequest):
    """
    Soumet un feedback utilisateur sur une réponse.

    Exemple:
    ```json
    {
        "response_id": "resp_20260708_120000_123456",
        "feedback": "thumbs_down",
        "is_hallucination": true,
        "details": "La réponse mentionne l'Article 999 qui n'existe pas"
    }
    ```
    """
    try:
        monitor.log_user_feedback(
            response_id=request.response_id,
            feedback=request.feedback,
            is_hallucination=request.is_hallucination,
            details=request.details or ""
        )
        return {
            "status": "success",
            "message": "Feedback enregistré avec succès",
            "response_id": request.response_id,
            "is_hallucination": request.is_hallucination
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/response")
async def analyze_response(request: AnalyzeRequest):
    """
    Analyse une réponse pour détecter les hallucinations.

    Exemple:
    ```json
    {
        "answer": "Selon l'Article 24 du Décret n° 96-203...",
        "sources": [{"source_ref": "Décret n° 96-203"}],
        "query": "Quel est le taux des heures supplémentaires?"
    }
    ```
    """
    try:
        sources = request.sources or []

        # Détection
        detection_results = detector.detect_hallucinations(request.answer, sources)

        # Afficher le rapport formaté
        report = detector.format_report(detection_results)
        print(report)

        return {
            "analysis": detection_results,
            "report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_statistics():
    """
    Retourne les statistiques globales de monitoring.
    """
    try:
        stats = monitor.get_stats()
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats/summary")
async def get_summary():
    """
    Retourne un résumé simple des statistiques.
    """
    try:
        stats = monitor.get_stats()
        return {
            "total_responses": stats["total_responses"],
            "total_feedback": stats["total_feedback"],
            "hallucinations_detected": stats["hallucinations_detected"],
            "hallucination_rate": f"{stats['false_positive_rate']:.2f}%",
            "recent_alerts_count": len(stats["alerts"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export/report")
async def export_report():
    """
    Exporte un rapport complet de monitoring.
    """
    try:
        report = monitor.export_report("monitoring_report_export.json")
        return {
            "status": "success",
            "message": "Rapport exporté avec succès",
            "file": "monitoring_report_export.json",
            "data": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """
    Vérifier que l'API fonctionne.
    """
    return {"status": "OK", "service": "JurisBot Feedback API"}


# ==========================================
# DÉMARRAGE
# ==========================================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Démarrage de l'API Feedback...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
