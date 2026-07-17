import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

DB_PATH = Path("jurisbot_ci.db")
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
    """Initialise la base de données SQLite avec les tables nécessaires"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            id TEXT PRIMARY KEY,
            query TEXT NOT NULL,
            answer TEXT NOT NULL,
            sources TEXT,
            hallucination_score REAL,
            is_hallucinating INTEGER,
            model TEXT,
            retriever TEXT,
            embedding_model TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            response_id TEXT NOT NULL,
            feedback_type TEXT,
            feedback TEXT,
            is_hallucination INTEGER,
            accuracy INTEGER,
            clarity INTEGER,
            citations INTEGER,
            completeness INTEGER,
            comments TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (response_id) REFERENCES responses(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            response_id TEXT NOT NULL,
            hallucination_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (response_id) REFERENCES responses(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_role TEXT,
            user_email TEXT,
            session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_end TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

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
    """Ajoute une réponse à la base de données"""
    log_action("ADD_RESPONSE", f"ID: {response_id}, Query: {query[:50]}")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        sources_json = json.dumps(sources or [])

        cursor.execute("""
            INSERT INTO responses (
                id, query, answer, sources, hallucination_score,
                is_hallucinating, model, retriever, embedding_model
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            response_id, query, answer, sources_json,
            hallucination_score, 1 if is_hallucinating else 0,
            model, retriever, embedding_model
        ))

        conn.commit()
        conn.close()
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
    """Ajoute un feedback utilisateur à la base de données"""
    log_action("ADD_FEEDBACK", f"Type: {feedback_type}, ResponseID: {response_id}, Email: {email}")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO feedbacks (
                response_id, feedback_type, feedback, is_hallucination,
                accuracy, clarity, citations, completeness, comments, email
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            response_id, feedback_type, feedback, 1 if is_hallucination else 0,
            accuracy, clarity, citations, completeness, comments, email
        ))

        conn.commit()
        conn.close()

        log_action("ADD_FEEDBACK", f"✅ SUCCESS - ResponseID: {response_id}")
        return True
    except Exception as e:
        log_action("ADD_FEEDBACK", f"❌ ERROR: {str(e)}")
        return False

def add_alert(response_id: str, hallucination_description: str) -> bool:
    """Ajoute une alerte pour une hallucination détectée"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO alerts (response_id, hallucination_description)
            VALUES (?, ?)
        """, (response_id, hallucination_description))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur lors de l'ajout de l'alerte: {e}")
        return False

def get_response(response_id: str) -> Optional[Dict[str, Any]]:
    """Récupère une réponse par son ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM responses WHERE id = ?", (response_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None
    except Exception as e:
        print(f"Erreur lors de la récupération de la réponse: {e}")
        return None

def get_all_responses() -> List[Dict[str, Any]]:
    """Récupère toutes les réponses"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM responses ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Erreur lors de la récupération des réponses: {e}")
        return []

def get_all_feedbacks() -> List[Dict[str, Any]]:
    """Récupère tous les feedbacks"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM feedbacks ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Erreur lors de la récupération des feedbacks: {e}")
        return []

def get_feedbacks_for_response(response_id: str) -> List[Dict[str, Any]]:
    """Récupère les feedbacks pour une réponse spécifique"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM feedbacks WHERE response_id = ? ORDER BY created_at DESC",
            (response_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Erreur lors de la récupération des feedbacks: {e}")
        return []

def get_stats() -> Dict[str, Any]:
    """Récupère les statistiques générales"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM responses")
        total_responses = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) as total FROM responses WHERE is_hallucinating = 1")
        hallucinations_detected = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(hallucination_score) as avg FROM responses")
        avg_hallucination_score = cursor.fetchone()[0] or 0.0

        cursor.execute("SELECT hallucination_score FROM responses ORDER BY created_at DESC")
        responses_scores = [row[0] for row in cursor.fetchall()]

        hallucination_rate = (hallucinations_detected / total_responses * 100) if total_responses > 0 else 0

        conn.close()

        return {
            "total_responses": total_responses,
            "hallucinations_detected": hallucinations_detected,
            "hallucination_rate": hallucination_rate,
            "average_hallucination_score": avg_hallucination_score,
            "responses_by_score": responses_scores
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
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM feedbacks")
        total_feedbacks = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) as total FROM feedbacks WHERE feedback_type = 'detailed'")
        detailed_feedbacks = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(accuracy) FROM feedbacks WHERE accuracy IS NOT NULL")
        avg_accuracy = cursor.fetchone()[0] or 0

        cursor.execute("SELECT AVG(clarity) FROM feedbacks WHERE clarity IS NOT NULL")
        avg_clarity = cursor.fetchone()[0] or 0

        cursor.execute("SELECT AVG(citations) FROM feedbacks WHERE citations IS NOT NULL")
        avg_citations = cursor.fetchone()[0] or 0

        cursor.execute("SELECT AVG(completeness) FROM feedbacks WHERE completeness IS NOT NULL")
        avg_completeness = cursor.fetchone()[0] or 0

        conn.close()

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
    """Exporte toutes les données (responses + feedbacks + alerts)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM responses ORDER BY created_at DESC")
        responses = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM feedbacks ORDER BY created_at DESC")
        feedbacks = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM alerts ORDER BY created_at DESC")
        alerts = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return {
            "responses": responses,
            "feedbacks": feedbacks,
            "alerts": alerts,
            "export_timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Erreur lors de l'export: {e}")
        return {}

def clear_all_data() -> bool:
    """Purge toutes les données de la base de données"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM feedbacks")
        cursor.execute("DELETE FROM alerts")
        cursor.execute("DELETE FROM responses")
        cursor.execute("DELETE FROM chat_sessions")

        conn.commit()
        conn.close()

        return True
    except Exception as e:
        print(f"Erreur lors de la purge: {e}")
        return False

if __name__ == "__main__":
    init_db()
    print("✅ Base de données SQLite initialisée!")
