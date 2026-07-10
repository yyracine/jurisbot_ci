import streamlit as st
import json
from datetime import datetime
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

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
    .feedback-form {
        background-color: #e8f5e9;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #4caf50;
    }
    .rating-stars {
        font-size: 2rem;
        cursor: pointer;
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

def submit_feedback(response_id: str, feedback_type: str, detailed_feedback: dict = None):
    monitor = get_monitoring()
    is_hallucination = feedback_type == "hallucination"

    details = f"Feedback: {feedback_type}"
    if detailed_feedback:
        details = json.dumps(detailed_feedback, ensure_ascii=False)

    monitor.log_user_feedback(
        response_id=response_id,
        feedback="thumbs_down" if feedback_type in ["negative", "hallucination"] else "thumbs_up",
        is_hallucination=is_hallucination,
        details=details
    )

    save_detailed_feedback(response_id, feedback_type, detailed_feedback)

def save_detailed_feedback(response_id: str, feedback_type: str, feedback_data: dict = None):
    """Sauvegarde le feedback détaillé dans un fichier JSON"""
    feedback_dir = Path("feedback_logs")
    feedback_dir.mkdir(exist_ok=True)

    feedback_file = feedback_dir / "detailed_feedback.jsonl"

    entry = {
        "response_id": response_id,
        "timestamp": datetime.now().isoformat(),
        "feedback_type": feedback_type,
        "feedback_data": feedback_data or {}
    }

    with open(feedback_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def load_detailed_feedback():
    """Charge tous les feedbacks détaillés"""
    feedback_file = Path("feedback_logs/detailed_feedback.jsonl")

    if not feedback_file.exists():
        return []

    feedbacks = []
    with open(feedback_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                feedbacks.append(json.loads(line))

    return feedbacks

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

        page = st.radio("Navigation", ["Chat", "Statistiques", "Feedbacks"])

    if page == "Chat":
        show_chat_page()
    elif page == "Statistiques":
        show_stats_page()
    else:
        show_feedback_page()

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

        st.markdown(f"**👤 Question:** {msg['question']}")
        with st.container(border=True):
            st.markdown(msg['response'])

        response_id = msg["response_id"]

        # Quick feedback buttons
        st.markdown("### Feedback rapide")
        col_up, col_down, col_neutral = st.columns(3, gap="small")

        quick_feedback_submitted = st.session_state.feedback_submitted.get(response_id)

        with col_up:
            if st.button("👍 Utile", key=f"quick_up_{response_id}", disabled=quick_feedback_submitted is not None):
                submit_feedback(response_id, "positive")
                st.session_state.feedback_submitted[response_id] = "positive"
                st.rerun()

        with col_down:
            if st.button("👎 Pas utile", key=f"quick_down_{response_id}", disabled=quick_feedback_submitted is not None):
                submit_feedback(response_id, "negative")
                st.session_state.feedback_submitted[response_id] = "negative"
                st.rerun()

        with col_neutral:
            if st.button("🚫 Hallucination", key=f"quick_halluc_{response_id}", disabled=quick_feedback_submitted is not None):
                submit_feedback(response_id, "hallucination")
                st.session_state.feedback_submitted[response_id] = "hallucination"
                st.rerun()

        if quick_feedback_submitted:
            if quick_feedback_submitted == "positive":
                st.success("✅ Feedback positif enregistré")
            elif quick_feedback_submitted == "negative":
                st.warning("⚠️ Feedback négatif enregistré")
            else:
                st.error("🚨 Hallucination signalée!")

        # Detailed feedback form
        st.markdown("---")
        st.markdown("### 📝 Feedback détaillé (optionnel)")
        st.caption("Aidez-nous à améliorer JurisBot en répondant à quelques questions")

        with st.form(key=f"detailed_feedback_{response_id}"):
            col1, col2 = st.columns(2)

            with col1:
                accuracy = st.slider(
                    "📌 Précision juridique",
                    min_value=1, max_value=5, value=3,
                    help="La réponse est-elle juridiquement exacte?"
                )
                clarity = st.slider(
                    "💬 Clarté de la réponse",
                    min_value=1, max_value=5, value=3,
                    help="La réponse est-elle compréhensible?"
                )

            with col2:
                citations = st.slider(
                    "📖 Qualité des citations",
                    min_value=1, max_value=5, value=3,
                    help="Les sources sont-elles correctes et pertinentes?"
                )
                completeness = st.slider(
                    "✅ Complétude",
                    min_value=1, max_value=5, value=3,
                    help="La réponse couvre-t-elle votre question?"
                )

            st.markdown("---")

            comments = st.text_area(
                "💭 Commentaires supplémentaires",
                placeholder="Décrivez votre expérience, erreurs détectées, suggestions...",
                height=100,
                label_visibility="visible"
            )

            email = st.text_input(
                "📧 Email (pour suivi)",
                placeholder="votre.email@example.com",
                label_visibility="visible"
            )

            col_submit, col_cancel = st.columns(2)
            with col_submit:
                submit_detail = st.form_submit_button("✅ Envoyer le feedback détaillé", use_container_width=True)

            if submit_detail:
                detailed_data = {
                    "accuracy": accuracy,
                    "clarity": clarity,
                    "citations": citations,
                    "completeness": completeness,
                    "comments": comments,
                    "email": email if email else "anonymous"
                }
                submit_feedback(response_id, "detailed", detailed_data)
                st.session_state.feedback_submitted[response_id] = "detailed"
                st.success("🎉 Merci pour votre feedback détaillé!")
                st.balloons()

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

def show_feedback_page():
    st.title("💬 Feedback des Testeurs - JurisBot CI")
    st.markdown("Analysez les retours des utilisateurs beta")

    feedbacks = load_detailed_feedback()

    if not feedbacks:
        st.info("Aucun feedback détaillé reçu pour le moment. Commencez à utiliser l'application et partagez votre feedback!")
        return

    # KPIs
    col1, col2, col3, col4 = st.columns(4)

    detailed_ratings = [f["feedback_data"] for f in feedbacks if f.get("feedback_data")]

    if detailed_ratings:
        avg_accuracy = sum(r.get("accuracy", 0) for r in detailed_ratings) / len(detailed_ratings)
        avg_clarity = sum(r.get("clarity", 0) for r in detailed_ratings) / len(detailed_ratings)
        avg_citations = sum(r.get("citations", 0) for r in detailed_ratings) / len(detailed_ratings)
        avg_completeness = sum(r.get("completeness", 0) for r in detailed_ratings) / len(detailed_ratings)

        with col1:
            st.metric("📌 Précision (moy.)", f"{avg_accuracy:.1f}/5")

        with col2:
            st.metric("💬 Clarté (moy.)", f"{avg_clarity:.1f}/5")

        with col3:
            st.metric("📖 Citations (moy.)", f"{avg_citations:.1f}/5")

        with col4:
            st.metric("✅ Complétude (moy.)", f"{avg_completeness:.1f}/5")

        st.markdown("---")

        # Distribution des évaluations
        st.subheader("📊 Distribution des évaluations")

        ratings_df = pd.DataFrame({
            "Catégorie": ["Précision", "Clarté", "Citations", "Complétude"],
            "Score moyen": [avg_accuracy, avg_clarity, avg_citations, avg_completeness]
        })

        st.bar_chart(
            ratings_df.set_index("Catégorie"),
            height=300,
            use_container_width=True
        )

    st.markdown("---")

    # Commentaires détaillés
    st.subheader("📝 Commentaires des Testeurs")

    with st.expander(f"👥 Afficher tous les commentaires ({len(feedbacks)})"):
        for idx, fb in enumerate(feedbacks, 1):
            with st.container(border=True):
                timestamp = datetime.fromisoformat(fb.get("timestamp", "")).strftime("%d/%m/%Y %H:%M")
                email = fb.get("feedback_data", {}).get("email", "Anonyme")

                col_header = st.columns([3, 1])
                with col_header[0]:
                    st.markdown(f"**#{idx}** — {email}")
                with col_header[1]:
                    st.caption(timestamp)

                if fb.get("feedback_type") == "detailed":
                    data = fb.get("feedback_data", {})
                    st.markdown(f"""
                    - **Précision:** {data.get("accuracy", "N/A")}/5
                    - **Clarté:** {data.get("clarity", "N/A")}/5
                    - **Citations:** {data.get("citations", "N/A")}/5
                    - **Complétude:** {data.get("completeness", "N/A")}/5
                    """)

                comments = fb.get("feedback_data", {}).get("comments", "")
                if comments:
                    st.write(f"💭 *{comments}*")

    st.markdown("---")

    # Export des feedbacks
    st.subheader("📥 Export des données")

    if st.button("📥 Télécharger tous les feedbacks (JSON)"):
        json_data = json.dumps(feedbacks, ensure_ascii=False, indent=2)
        st.download_button(
            label="Télécharger",
            data=json_data,
            file_name="jurisbot_feedbacks.json",
            mime="application/json"
        )

    if st.button("📊 Télécharger en CSV"):
        csv_data = []
        for fb in feedbacks:
            data = fb.get("feedback_data", {})
            csv_data.append({
                "Date": datetime.fromisoformat(fb.get("timestamp", "")).strftime("%d/%m/%Y %H:%M"),
                "Email": data.get("email", "Anonyme"),
                "Précision": data.get("accuracy", ""),
                "Clarté": data.get("clarity", ""),
                "Citations": data.get("citations", ""),
                "Complétude": data.get("completeness", ""),
                "Commentaires": data.get("comments", "")
            })

        df = pd.DataFrame(csv_data)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Télécharger",
            data=csv,
            file_name="jurisbot_feedbacks.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
