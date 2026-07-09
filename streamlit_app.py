import streamlit as st
import json
from datetime import datetime
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

from bot_juridique import init_rag_engine, ask_legal_bot, verify_and_correct_citations
from monitoring import get_monitor
from hallucination_detector import HallucinationDetector

st.set_page_config(
    page_title="JurisBot CI - Legal AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .feedback-container {
        display: flex;
        gap: 1rem;
        margin-top: 1rem;
        padding: 1rem;
        background-color: #f0f2f6;
        border-radius: 0.5rem;
    }
    .response-box {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-left: 4px solid #1f77b4;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .stat-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_rag_engine():
    return init_rag_engine()

@st.cache_resource
def get_monitoring():
    return get_monitor()

@st.cache_resource
def get_detector():
    return HallucinationDetector()

class JurisBotMonitored:
    def __init__(self):
        self.retriever, self.llm = load_rag_engine()
        self.monitor = get_monitoring()
        self.detector = get_detector()

    def answer(self, query: str) -> tuple[str, str]:
        response = ask_legal_bot(query, self.retriever, self.llm)
        answer = response["answer"]
        sources = response["sources"]

        detection_results = self.detector.detect_hallucinations(answer, sources)

        response_id = self.monitor.log_response(
            query=query,
            answer=answer,
            sources=sources,
            detection_results=detection_results,
            metadata={
                "model": "mistral-large-latest",
                "retriever": "FAISS",
                "embedding_model": "mistral-embed"
            }
        )

        if detection_results["is_hallucinating"]:
            self.monitor.create_alert(
                response_id=response_id,
                hallucination_description=f"Score: {detection_results['hallucination_score']:.0%}"
            )

        return answer, response_id

def submit_feedback(response_id: str, feedback_type: str):
    monitor = get_monitoring()
    is_hallucination = feedback_type == "hallucination"
    monitor.log_user_feedback(
        response_id=response_id,
        feedback="thumbs_down" if feedback_type in ["negative", "hallucination"] else "thumbs_up",
        is_hallucination=is_hallucination,
        details=f"Feedback: {feedback_type}"
    )

def get_stats():
    monitor = get_monitoring()
    stats = monitor.get_stats()

    feedback_dist = {}
    feedback_log = monitor.feedback_log
    if feedback_log.exists():
        with open(feedback_log, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                fb_type = entry.get("feedback", "unknown")
                feedback_dist[fb_type] = feedback_dist.get(fb_type, 0) + 1

    return {
        **stats,
        "feedback_distribution": feedback_dist,
        "hallucination_count": stats.get("hallucinations_detected", 0)
    }

def main():
    with st.sidebar:
        st.header("📋 JurisBot CI")
        st.markdown("---")
        st.subheader("À propos")
        st.write("""
        Plateforme légale IA pour la Côte d'Ivoire.

        Réponses basées sur:
        - Loi n° 2015-532
        - Convention Collective Interprofessionnelle
        """)
        st.markdown("---")

        page = st.radio("Navigation", ["Chat", "Statistiques"])

    if page == "Chat":
        show_chat_page()
    else:
        show_stats_page()

def show_chat_page():
    st.title("⚖️ JurisBot - Droit du Travail Ivoirien")
    st.markdown("Posez vos questions sur le droit du travail ivoirien")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "bot" not in st.session_state:
        st.session_state.bot = JurisBotMonitored()

    if "feedback_submitted" not in st.session_state:
        st.session_state.feedback_submitted = {}

    with st.form(key="question_form", clear_on_submit=True):
        user_input = st.text_area(
            "Votre question:",
            placeholder="Ex: Quels sont les délais de préavis pour un licenciement?",
            height=100
        )
        submit_button = st.form_submit_button("📤 Envoyer", use_container_width=True)

    if submit_button and user_input.strip():
        with st.spinner("⏳ Analyse en cours..."):
            bot = st.session_state.bot
            response_text, response_id = bot.answer(user_input)

            st.session_state.chat_history.append({
                "question": user_input,
                "response": response_text,
                "response_id": response_id,
                "timestamp": datetime.now().isoformat()
            })

    if st.session_state.chat_history:
        msg = st.session_state.chat_history[-1]
        col1, col2 = st.columns([10, 2])

        with col1:
            st.markdown(f"**👤 Question:** {msg['question']}")
            with st.container(border=True):
                st.markdown(msg['response'])

        response_id = msg["response_id"]
        key_prefix = f"feedback_{response_id}"

        col_up, col_down, col_neutral = st.columns(3, gap="small")

        with col_up:
            if st.button("👍 Utile", key=f"{key_prefix}_up"):
                submit_feedback(response_id, "positive")
                st.session_state.feedback_submitted[response_id] = "positive"
                st.success("✅ Merci pour votre feedback positif!")

        with col_down:
            if st.button("👎 Pas utile", key=f"{key_prefix}_down"):
                submit_feedback(response_id, "negative")
                st.session_state.feedback_submitted[response_id] = "negative"
                st.warning("⚠️ Feedback négatif enregistré")

        with col_neutral:
            if st.button("🚫 Hallucination", key=f"{key_prefix}_hallucination"):
                submit_feedback(response_id, "hallucination")
                st.session_state.feedback_submitted[response_id] = "hallucination"
                st.error("🚨 Hallucination signalée à nos équipes!")

        feedback_status = st.session_state.feedback_submitted.get(response_id)
        if feedback_status:
            if feedback_status == "positive":
                st.caption("✅ Feedback positif enregistré")
            elif feedback_status == "negative":
                st.caption("⚠️ Feedback négatif enregistré")
            else:
                st.caption("🚨 Hallucination signalée")

        st.markdown("---")

def show_stats_page():
    st.title("📊 Statistiques & Monitoring - JurisBot CI")

    try:
        stats = get_stats()

        # KPIs en haut
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "📝 Réponses",
                stats.get("total_responses", 0),
                delta=None,
                label_visibility="visible"
            )

        with col2:
            st.metric(
                "💬 Feedbacks",
                stats.get("total_feedback", 0),
                delta=None
            )

        with col3:
            hallucination_rate = stats.get("hallucination_rate", 0.0)
            st.metric(
                "🎯 Taux Hallucination",
                f"{hallucination_rate:.1f}%",
                delta=None
            )

        with col4:
            avg_score = stats.get("average_hallucination_score", 0.0)
            st.metric(
                "📊 Score Moyen",
                f"{avg_score:.2f}",
                delta=None
            )

        st.markdown("---")

        # Tableau détaillé des réponses
        st.subheader("Détail par Réponse")

        responses_by_score = stats.get("responses_by_score", [])
        if responses_by_score:
            response_data = []
            for idx, score in enumerate(responses_by_score, 1):
                response_data.append({
                    "#": idx,
                    "Score Hallucination": f"{score:.2%}",
                    "Statut": "✅ Sain" if score < 0.5 else "⚠️ Risque",
                    "Confiance": "Haute" if score > 0.1 else "Basse"
                })

            df_responses = pd.DataFrame(response_data)
            st.dataframe(df_responses, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune réponse enregistrée pour le moment.")

        st.markdown("---")

        # Feedback utilisateur
        st.subheader("Feedback Utilisateur")
        col1, col2, col3 = st.columns(3)

        with col1:
            total_fb = stats.get("total_feedback", 0)
            halluc_fb = stats.get("hallucinations_detected", 0)
            st.metric("Total", total_fb)

        with col2:
            st.metric("Hallucinations signalées", halluc_fb)

        with col3:
            if total_fb > 0:
                positive_rate = ((total_fb - halluc_fb) / total_fb) * 100
                st.metric("Taux satisfait", f"{positive_rate:.0f}%")

        st.markdown("---")

        # Résumé exécutif
        st.subheader("Résumé Exécutif")

        summary_col1, summary_col2 = st.columns(2)

        with summary_col1:
            st.write("""
            ### 🔬 Détection Automatique
            - Basée sur les **scores d'hallucination** du modèle
            - Seuil: score ≥ 0.5 = hallucination
            - Indépendante du feedback utilisateur
            """)

        with summary_col2:
            st.write(f"""
            ### 👤 Feedback Utilisateur
            - **{total_fb}** feedbacks enregistrés
            - **{halluc_fb}** hallucinations signalées
            - Taux de satisfaction: **{positive_rate:.0f}%** si total > 0
            """)

    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des statistiques: {e}")
        st.info("Le système de monitoring n'est pas encore actif. Posez des questions pour générer des données.")

if __name__ == "__main__":
    main()
