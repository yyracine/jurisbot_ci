import streamlit as st
import json
from datetime import datetime
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv(override=True)

from bot_juridique import init_rag_engine, ask_legal_bot, verify_and_correct_citations
from monitoring import get_monitor
from hallucination_detector import HallucinationDetector
from db import (
    init_db, add_response, add_feedback,
    get_all_feedbacks, get_feedback_stats, export_all_data
)
from db import get_stats as get_db_stats
from analysis import FeedbackAnalyzer
from recommendations import RecommendationEngine

init_db()

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
        from pathlib import Path
        log_file = Path("debug_db.log")

        def log_action(action, details=""):
            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    f.write(f"[{timestamp}] {action}: {details}\n")
            except:
                pass

        log_action("BOT_ANSWER", f"Processing query: {query[:50]}")

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

        log_action("BOT_ANSWER", f"Generated response_id: {response_id}")

        add_response(
            response_id=response_id,
            query=query,
            answer=answer,
            sources=sources,
            hallucination_score=detection_results.get("hallucination_score", 0.0),
            is_hallucinating=detection_results.get("is_hallucinating", False),
            model="mistral-large-latest",
            retriever="FAISS",
            embedding_model="mistral-embed"
        )

        if detection_results["is_hallucinating"]:
            self.monitor.create_alert(
                response_id=response_id,
                hallucination_description=f"Score: {detection_results['hallucination_score']:.0%}"
            )

        log_action("BOT_ANSWER", f"✅ Response saved to database")
        return answer, response_id

def submit_feedback(response_id: str, feedback_type: str, detailed_feedback: dict = None):
    """Soumet le feedback à la base de données SQLite"""
    import sys
    log_msg = f"[FEEDBACK LOG] Type: {feedback_type}, ResponseID: {response_id}"
    print(log_msg, file=sys.stderr)

    try:
        if feedback_type == "positive":
            result = add_feedback(
                response_id=response_id,
                feedback_type="quick",
                feedback="thumbs_up",
                is_hallucination=False
            )
            print(f"[FEEDBACK LOG] ✅ Positive feedback saved: {result}", file=sys.stderr)
        elif feedback_type == "negative":
            result = add_feedback(
                response_id=response_id,
                feedback_type="quick",
                feedback="thumbs_down",
                is_hallucination=False
            )
            print(f"[FEEDBACK LOG] ✅ Negative feedback saved: {result}", file=sys.stderr)
        elif feedback_type == "hallucination":
            result = add_feedback(
                response_id=response_id,
                feedback_type="quick",
                feedback="hallucination",
                is_hallucination=True
            )
            print(f"[FEEDBACK LOG] ✅ Hallucination feedback saved: {result}", file=sys.stderr)
        elif feedback_type == "detailed" and detailed_feedback:
            result = add_feedback(
                response_id=response_id,
                feedback_type="detailed",
                accuracy=detailed_feedback.get("accuracy"),
                clarity=detailed_feedback.get("clarity"),
                citations=detailed_feedback.get("citations"),
                completeness=detailed_feedback.get("completeness"),
                comments=detailed_feedback.get("comments"),
                email=detailed_feedback.get("email", "anonymous")
            )
            print(f"[FEEDBACK LOG] ✅ Detailed feedback saved: {result}", file=sys.stderr)
        else:
            print(f"[FEEDBACK LOG] ⚠️ No matching feedback type or missing data", file=sys.stderr)
    except Exception as e:
        print(f"[FEEDBACK LOG] ❌ ERROR: {str(e)}", file=sys.stderr)
        st.error(f"❌ Erreur lors de l'enregistrement du feedback: {str(e)}")

def load_detailed_feedback():
    """Charge tous les feedbacks depuis SQLite"""
    feedbacks = get_all_feedbacks()

    formatted_feedbacks = []
    for fb in feedbacks:
        formatted_feedbacks.append({
            "response_id": fb["response_id"],
            "timestamp": fb["created_at"],
            "feedback_type": fb["feedback_type"],
            "feedback_data": {
                "accuracy": fb["accuracy"],
                "clarity": fb["clarity"],
                "citations": fb["citations"],
                "completeness": fb["completeness"],
                "comments": fb["comments"],
                "email": fb["email"] or "Anonyme"
            }
        })

    return formatted_feedbacks

def get_stats():
    """Récupère les statistiques depuis SQLite"""
    stats = get_db_stats()
    feedback_stats = get_feedback_stats()

    return {
        **stats,
        **feedback_stats,
        "hallucination_count": stats.get("hallucinations_detected", 0)
    }

def init_session_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    if "user_email" not in st.session_state:
        st.session_state.user_email = None

def authenticate_user():
    st.set_page_config(
        page_title="JurisBot CI - Authentification",
        page_icon="⚖️",
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 JurisBot CI")
        st.markdown("---")
        st.markdown("### Accès à la plateforme")

        email = st.text_input(
            "📧 Votre adresse email:",
            placeholder="exemple@mail.com",
            key="login_email"
        )

        password = st.text_input(
            "🔑 Mot de passe d'accès:",
            type="password",
            placeholder="Entrez votre mot de passe"
        )

        if st.button("Accéder", use_container_width=True):
            if not email or "@" not in email:
                st.error("❌ Veuillez entrer une adresse email valide")
                return

            admin_password = os.getenv("ADMIN_PASSWORD", "")

            if password and admin_password and password == admin_password:
                st.session_state.authenticated = True
                st.session_state.is_admin = True
                st.session_state.user_email = email
                st.success("✅ Accès administrateur activé!")
                st.rerun()
            else:
                st.session_state.authenticated = True
                st.session_state.is_admin = False
                st.session_state.user_email = email
                st.success("✅ Accès testeur activé!")
                st.rerun()

    st.stop()

def main():
    init_session_state()

    if not st.session_state.authenticated:
        authenticate_user()
        return

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

        if st.session_state.is_admin:
            page = st.radio("Navigation", ["Chat", "Statistiques", "Feedbacks", "Analyse & Recommandations", "⚙️ Admin"])
            st.markdown("---")
            st.info(f"👤 Mode: **Admin**")
        else:
            page = "Chat"
            st.info(f"👤 Mode: **Testeur**\n\nVous accédez uniquement au formulaire de feedback.")

        st.markdown("---")
        if st.button("🔒 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.is_admin = False
            st.session_state.user_email = None
            st.session_state.chat_history = []
            st.session_state.feedback_submitted = {}
            st.success("✅ Déconnecté!")
            st.rerun()

    if page == "Chat":
        show_chat_page()
    elif page == "Statistiques":
        show_stats_page()
    elif page == "Feedbacks":
        show_feedback_page()
    elif page == "Analyse & Recommandations":
        show_analysis_page()
    else:
        show_admin_panel()

def show_chat_page():
    st.title("⚖️ JurisBot - Droit du Travail Ivoirien")
    st.markdown("Posez vos questions sur le droit du travail ivoirien")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "bot" not in st.session_state:
        st.session_state.bot = JurisBotMonitored()

    if "feedback_submitted" not in st.session_state:
        st.session_state.feedback_submitted = {}

    col_form_left, col_form_right = st.columns([4, 1])

    with col_form_left:
        with st.form(key="question_form", clear_on_submit=True):
            user_input = st.text_area(
                "Votre question:",
                placeholder="Ex: Quels sont les délais de préavis pour un licenciement?",
                height=100
            )
            submit_button = st.form_submit_button("📤 Envoyer", use_container_width=True)

    with col_form_right:
        st.write("")
        st.write("")
        if st.button("🔄 Réinitialiser", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.feedback_submitted = {}
            st.success("✅ Chat réinitialisé!")
            st.rerun()

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

        # Detailed feedback form
        st.markdown("### 📝 Feedback détaillé")
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

            email = st.session_state.user_email or "anonymous"
            st.info(f"📧 **Email:** {email}")

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
                    "email": email
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
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "📝 Réponses Générées",
                stats.get("total_responses", 0),
                delta=None,
                label_visibility="visible"
            )

        with col2:
            hallucination_rate = stats.get("hallucination_rate", 0.0)
            st.metric(
                "🚨 Taux Hallucination",
                f"{hallucination_rate:.1f}%",
                delta=None
            )

        with col3:
            avg_score = stats.get("average_hallucination_score", 0.0)
            st.metric(
                "📊 Score Hallucination Moyen",
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

        # Résumé exécutif
        st.subheader("📋 Résumé Exécutif")

        st.info("""
        **💡 Feedback des utilisateurs?**
        Les feedbacks détaillés sont maintenant gérés dans l'onglet **"Feedbacks"**.
        Cette page affiche uniquement les statistiques du système RAG.
        """)

        st.write("""
        ### 🔬 Détection Automatique des Hallucinations
        - Basée sur les **scores d'hallucination** du modèle
        - Seuil: score ≥ 0.5 = hallucination détectée
        - Système indépendant et automatisé
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
        avg_accuracy = sum((r.get("accuracy") or 0) for r in detailed_ratings) / len(detailed_ratings)
        avg_clarity = sum((r.get("clarity") or 0) for r in detailed_ratings) / len(detailed_ratings)
        avg_citations = sum((r.get("citations") or 0) for r in detailed_ratings) / len(detailed_ratings)
        avg_completeness = sum((r.get("completeness") or 0) for r in detailed_ratings) / len(detailed_ratings)

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

    col_json, col_csv, col_all = st.columns(3)

    with col_json:
        if st.button("📥 JSON Feedbacks"):
            json_data = json.dumps(feedbacks, ensure_ascii=False, indent=2, default=str)
            st.download_button(
                label="Télécharger",
                data=json_data,
                file_name="jurisbot_feedbacks.json",
                mime="application/json",
                use_container_width=True
            )

    with col_csv:
        if st.button("📊 CSV Feedbacks"):
            csv_data = []
            for fb in feedbacks:
                data = fb.get("feedback_data", {})
                csv_data.append({
                    "Date": fb.get("timestamp", "").split("T")[0],
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
                mime="text/csv",
                use_container_width=True
            )

    with col_all:
        if st.button("📦 Export Complet"):
            all_data = export_all_data()
            json_data = json.dumps(all_data, ensure_ascii=False, indent=2, default=str)
            st.download_button(
                label="Télécharger",
                data=json_data,
                file_name="jurisbot_complete_export.json",
                mime="application/json",
                use_container_width=True
            )

def show_analysis_page():
    st.title("📊 Analyse & Recommandations - JurisBot CI")
    st.markdown("Analyse intelligente des données pour améliorer l'application")

    try:
        analyzer = FeedbackAnalyzer()
        engine = RecommendationEngine()

        tab1, tab2, tab3, tab4 = st.tabs(["📈 Satisfaction", "⚠️ Problèmes", "✅ Quick Wins", "🗺️ Roadmap"])

        with tab1:
            st.subheader("Score de Satisfaction Global")
            satisfaction = analyzer.get_user_satisfaction()

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Score Satisfaction", f"{satisfaction['satisfaction_score']:.1f}/5", satisfaction['interpretation'])
            with col2:
                st.metric("Total Feedbacks", satisfaction["total_feedbacks"])
            with col3:
                st.metric("Feedbacks Détaillés", satisfaction["detailed_feedbacks"])
            with col4:
                st.metric("Réponses Analysées", len(analyzer.responses))

            st.markdown("---")

            col1, col2 = st.columns(2)
            with col1:
                st.write("**Scores détaillés**")
                metrics_df = pd.DataFrame({
                    "Métrique": ["Précision", "Clarté", "Citations", "Complétude"],
                    "Score": [
                        analyzer.feedback_stats.get("avg_accuracy", 0),
                        analyzer.feedback_stats.get("avg_clarity", 0),
                        analyzer.feedback_stats.get("avg_citations", 0),
                        analyzer.feedback_stats.get("avg_completeness", 0)
                    ]
                })
                st.bar_chart(metrics_df.set_index("Métrique"), height=300)

            with col2:
                st.write("**Hallucinations & Qualité**")
                quality_df = pd.DataFrame({
                    "Métrique": ["Hallucination Rate", "Avg Hallucination Score"],
                    "Valeur": [
                        analyzer.response_stats.get("hallucination_rate", 0),
                        analyzer.response_stats.get("average_hallucination_score", 0) * 100
                    ]
                })
                st.bar_chart(quality_df.set_index("Métrique"), height=300)

            strengths = analyzer.get_strengths()
            if strengths:
                st.markdown("---")
                st.subheader("✨ Forces du Système")
                for strength in strengths:
                    with st.container(border=True):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{strength['area']}**")
                            st.write(strength["description"])
                        with col2:
                            st.metric("Score", f"{strength['score']:.1f}")

        with tab2:
            st.subheader("⚠️ Zones Problématiques")
            problems = analyzer.get_problem_areas()

            if not problems:
                st.success("✅ Aucun problème détecté! Système en bonne santé.")
            else:
                for problem in problems:
                    severity_icon = {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "📌"}.get(problem["severity"], "ℹ️")
                    with st.container(border=True):
                        st.markdown(f"{severity_icon} **{problem['area']}** - {problem['severity']}")
                        st.write(problem["description"])
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"📊 {problem['impact']}")
                        with col2:
                            st.write(f"💡 {problem['recommendation']}")

        with tab3:
            st.subheader("⚡ Quick Wins - Actions Rapides")
            quick_wins = engine.get_quick_wins()

            if not quick_wins:
                st.success("✅ Système optimisé! Pas de quick wins nécessaires.")
            else:
                for win in quick_wins:
                    with st.expander(f"**{win['title']}** - {win['effort']} ({win['estimated_time']})"):
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.write(win["description"])
                            st.markdown("**Actions:**")
                            for action in win["actions"]:
                                st.write(f"- {action}")
                        with col2:
                            st.metric("Priorité", win["priority"])
                            st.metric("Impact", win["expected_impact"])
                        st.info(f"✓ Succès: {win['success_metric']}")

        with tab4:
            st.subheader("🗺️ Roadmap Personnalisée")
            roadmap = engine.get_personalized_roadmap()

            st.write(f"**État actuel:** Satisfaction = {roadmap['current_state']['satisfaction_score']:.1f}/5")
            st.write(f"**Focus:** {roadmap['priority_focus']}")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📋 Moyen Terme (1-2 semaines)")
                for improvement in roadmap["medium_term"]:
                    with st.container(border=True):
                        st.markdown(f"**{improvement['title']}**")
                        st.caption(f"{improvement['timeline']} | {improvement['effort']}")
                        st.write(improvement["description"])

            with col2:
                st.subheader("🚀 Long Terme (1-3 mois)")
                for phase in roadmap["long_term"]:
                    with st.container(border=True):
                        st.markdown(f"**{phase['phase']}**")
                        st.caption(phase["timeline"])
                        for initiative in phase["initiatives"]:
                            st.write(f"- {initiative}")

        st.markdown("---")
        st.subheader("📥 Exporter les Rapports")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📊 Export Analyse Markdown"):
                satisfaction = analyzer.get_user_satisfaction()
                markdown_content = f"""# 📊 Analyse Détaillée - JurisBot CI

## 🎯 Résumé Exécutif

- **Score de Satisfaction Global:** {satisfaction['satisfaction_score']:.1f}/5
- **Total Feedbacks:** {satisfaction["total_feedbacks"]}
- **Feedbacks Détaillés:** {satisfaction["detailed_feedbacks"]}
- **Réponses Analysées:** {len(analyzer.responses)}

## 📈 Scores Détaillés

| Métrique | Score | Interprétation |
|----------|-------|-----------------|
| Précision | {analyzer.feedback_stats.get("avg_accuracy", 0):.2f}/5 | {("✅ Excellent" if analyzer.feedback_stats.get("avg_accuracy", 0) >= 4.5 else "⚠️ À améliorer")} |
| Clarté | {analyzer.feedback_stats.get("avg_clarity", 0):.2f}/5 | {("✅ Excellent" if analyzer.feedback_stats.get("avg_clarity", 0) >= 4.5 else "⚠️ À améliorer")} |
| Citations | {analyzer.feedback_stats.get("avg_citations", 0):.2f}/5 | {("✅ Excellent" if analyzer.feedback_stats.get("avg_citations", 0) >= 4.5 else "⚠️ À améliorer")} |
| Complétude | {analyzer.feedback_stats.get("avg_completeness", 0):.2f}/5 | {("✅ Excellent" if analyzer.feedback_stats.get("avg_completeness", 0) >= 4.5 else "⚠️ À améliorer")} |

## 🚨 Qualité & Hallucinations

- **Taux d'Hallucination:** {analyzer.response_stats.get("hallucination_rate", 0):.1f}%
- **Score Hallucination Moyen:** {analyzer.response_stats.get("average_hallucination_score", 0):.2f}

## ✨ Forces du Système

"""
                strengths = analyzer.get_strengths()
                if strengths:
                    for strength in strengths:
                        markdown_content += f"\n### {strength['area']}\n\n{strength['description']}\n\n**Score:** {strength['score']:.1f}/5\n"
                else:
                    markdown_content += "\n✅ Système stable et performant!\n"

                markdown_content += "\n## ⚠️ Zones Problématiques\n\n"
                problems = analyzer.get_problem_areas()
                if not problems:
                    markdown_content += "✅ Aucun problème détecté!\n"
                else:
                    for problem in problems:
                        severity_icon = {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "📌"}.get(problem["severity"], "ℹ️")
                        markdown_content += f"\n### {severity_icon} {problem['area']} [{problem['severity']}]\n\n{problem['description']}\n\n**Impact:** {problem['impact']}\n\n**Recommandation:** {problem['recommendation']}\n"

                st.download_button(
                    "📥 Télécharger Analyse",
                    markdown_content,
                    file_name=f"analyse_jurisbot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )

        with col2:
            if st.button("🗺️ Export Recommandations Markdown"):
                roadmap = engine.get_personalized_roadmap()
                markdown_rec = f"""# 🗺️ Recommandations & Roadmap - JurisBot CI

## 📊 État Actuel

- **Score de Satisfaction:** {roadmap['current_state']['satisfaction_score']:.1f}/5
- **Focus Prioritaire:** {roadmap['priority_focus']}

## ⚡ Quick Wins (Actions Rapides)

"""
                quick_wins = engine.get_quick_wins()
                if quick_wins:
                    for i, win in enumerate(quick_wins, 1):
                        markdown_rec += f"\n### {i}. {win['title']}\n\n**Priorité:** {win['priority']} | **Effort:** {win['effort']} ({win['estimated_time']})\n\n{win['description']}\n\n**Actions:**\n"
                        for action in win["actions"]:
                            markdown_rec += f"- {action}\n"
                        markdown_rec += f"\n**Impact Attendu:** {win['expected_impact']}\n\n**Métrique de Succès:** {win['success_metric']}\n"
                else:
                    markdown_rec += "\n✅ Système optimisé, pas de quick wins nécessaires.\n"

                markdown_rec += "\n## 📋 Moyen Terme (1-2 semaines)\n\n"
                for improvement in roadmap["medium_term"]:
                    markdown_rec += f"\n### {improvement['title']}\n\n**Timeline:** {improvement['timeline']} | **Effort:** {improvement['effort']}\n\n{improvement['description']}\n"

                markdown_rec += "\n## 🚀 Long Terme (1-3 mois)\n\n"
                for phase in roadmap["long_term"]:
                    markdown_rec += f"\n### {phase['phase']}\n\n**Timeline:** {phase['timeline']}\n\n"
                    for initiative in phase["initiatives"]:
                        markdown_rec += f"- {initiative}\n"

                st.download_button(
                    "📥 Télécharger Recommandations",
                    markdown_rec,
                    file_name=f"recommandations_jurisbot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )

    except Exception as e:
        st.error(f"❌ Erreur lors de l'analyse: {e}")
        st.info("Assurez-vous d'avoir assez de données pour l'analyse (au moins 5 feedbacks)")

def generate_analysis_html(analyzer, engine):
    """Génère un rapport HTML d'analyse des feedbacks"""
    satisfaction = analyzer.get_user_satisfaction()
    problems = analyzer.get_problem_areas()
    strengths = analyzer.get_strengths()
    quick_wins = engine.get_quick_wins()
    roadmap = engine.get_personalized_roadmap()

    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>JurisBot CI - Analyse des Feedbacks</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                border-radius: 8px;
                margin-bottom: 30px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 2.5em;
            }}
            .timestamp {{
                opacity: 0.9;
                font-size: 0.9em;
            }}
            .metrics {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
                margin-bottom: 30px;
            }}
            .metric-card {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .metric-value {{
                font-size: 2em;
                font-weight: bold;
                color: #667eea;
                margin: 10px 0;
            }}
            .metric-label {{
                color: #666;
                font-size: 0.9em;
            }}
            .section {{
                background: white;
                padding: 30px;
                margin-bottom: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .section h2 {{
                border-bottom: 3px solid #667eea;
                padding-bottom: 10px;
                margin-top: 0;
            }}
            .problem {{
                border-left: 4px solid #dc3545;
                padding: 15px;
                margin-bottom: 15px;
                background: #f8f9fa;
                border-radius: 4px;
            }}
            .problem.HIGH {{
                border-left-color: #fd7e14;
            }}
            .problem.MEDIUM {{
                border-left-color: #ffc107;
            }}
            .severity {{
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 0.85em;
                margin-bottom: 10px;
            }}
            .severity.CRITICAL {{
                background: #dc3545;
                color: white;
            }}
            .severity.HIGH {{
                background: #fd7e14;
                color: white;
            }}
            .severity.MEDIUM {{
                background: #ffc107;
                color: #333;
            }}
            .strength {{
                border-left: 4px solid #28a745;
                padding: 15px;
                margin-bottom: 15px;
                background: #f8f9fa;
                border-radius: 4px;
            }}
            .quick-win {{
                border-left: 4px solid #667eea;
                padding: 15px;
                margin-bottom: 15px;
                background: #f8f9fa;
                border-radius: 4px;
            }}
            .actions {{
                background: #f0f4ff;
                padding: 10px;
                border-radius: 4px;
                margin: 10px 0;
                font-size: 0.9em;
            }}
            @media print {{
                body {{
                    background: white;
                }}
                .section {{
                    page-break-inside: avoid;
                    box-shadow: none;
                    border: 1px solid #ddd;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 JurisBot CI - Analyse des Feedbacks</h1>
            <p class="timestamp">Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</p>
        </div>

        <div class="metrics">
            <div class="metric-card">
                <div class="metric-label">Score Satisfaction</div>
                <div class="metric-value">{satisfaction['satisfaction_score']:.1f}/5</div>
                <div style="color: #667eea;">{satisfaction['interpretation']}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Réponses</div>
                <div class="metric-value">{analyzer.response_stats.get('total_responses', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Taux Hallucination</div>
                <div class="metric-value">{analyzer.response_stats.get('hallucination_rate', 0):.1f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Feedbacks</div>
                <div class="metric-value">{satisfaction['total_feedbacks']}</div>
            </div>
        </div>

        <div class="section">
            <h2>✨ Forces du Système</h2>
    """

    if strengths:
        for strength in strengths:
            html += f"""
            <div class="strength">
                <strong>{strength['area']}</strong> (Score: {strength['score']:.1f}/5)
                <p>{strength['description']}</p>
            </div>
            """
    else:
        html += "<p>✅ Système stable et performant!</p>"

    html += """
        </div>

        <div class="section">
            <h2>📊 Distribution des Scores Détaillée</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 2px solid #667eea;">
                    <th style="padding: 12px; text-align: left;">Catégorie</th>
                    <th style="padding: 12px; text-align: center;">Score Moyen</th>
                    <th style="padding: 12px; text-align: center;">Évaluation</th>
                </tr>
    """

    metrics_scores = {
        "Précision": analyzer.feedback_stats.get("avg_accuracy", 0),
        "Clarté": analyzer.feedback_stats.get("avg_clarity", 0),
        "Citations": analyzer.feedback_stats.get("avg_citations", 0),
        "Complétude": analyzer.feedback_stats.get("avg_completeness", 0)
    }

    for category, score in metrics_scores.items():
        evaluation = "✅ Excellent" if score >= 4.5 else ("⚠️ Bon" if score >= 3.5 else "📌 À améliorer")
        html += f"""
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 12px;">{category}</td>
                    <td style="padding: 12px; text-align: center;"><strong>{score:.2f}/5</strong></td>
                    <td style="padding: 12px; text-align: center;">{evaluation}</td>
                </tr>
        """

    html += """
            </table>
        </div>
    """

    problems_list = analyzer.get_problem_areas()
    if problems_list:
        html += """
        <div class="section">
            <h2>⚠️ Zones Problématiques</h2>
        """
        for problem in problems_list:
            html += f"""
            <div class="problem {problem['severity']}">
                <span class="severity {problem['severity']}">{problem['severity']}</span>
                <strong>{problem['area']}</strong>
                <p>{problem['description']}</p>
                <p><strong>Impact:</strong> {problem['impact']}</p>
                <p><strong>Recommandation:</strong> {problem['recommendation']}</p>
            </div>
            """
        html += """
        </div>
        """

    if quick_wins:
        html += """
        <div class="section">
            <h2>⚡ Quick Wins - Actions Rapides</h2>
        """
        for win in quick_wins:
            html += f"""
            <div class="quick-win">
                <strong>{win['title']}</strong> - {win['effort']} ({win['estimated_time']})
                <p>{win['description']}</p>
                <div class="actions">
                    <strong>Actions:</strong><br>
                    {'<br>'.join(win['actions'])}
                </div>
                <p><strong>Priorité:</strong> {win['priority']} | <strong>Impact:</strong> {win['expected_impact']}</p>
                <p><strong>✓ Succès:</strong> {win['success_metric']}</p>
            </div>
            """
        html += """
        </div>
        """

    html += """
        <div class="section" style="background: #f8f9fa; border-top: 3px solid #667eea;">
            <p style="text-align: center; color: #666; margin: 0;">
                <em>Rapport généré automatiquement par JurisBot CI Analytics</em>
            </p>
        </div>
    </body>
    </html>
    """

    return html

def show_admin_panel():
    st.title("⚙️ Panneau Administrateur - JurisBot CI")
    st.markdown("Gérez les données et générez les rapports")

    st.markdown("---")
    st.subheader("🛠️ Actions Administrateur")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 📊 Analyser les Feedbacks")
        st.write("Génère une analyse HTML détaillée de tous les feedbacks")
        if st.button("🔍 Analyser", key="btn_analyze", use_container_width=True):
            try:
                with st.spinner("⏳ Analyse en cours..."):
                    from analysis import FeedbackAnalyzer
                    from recommendations import RecommendationEngine

                    analyzer = FeedbackAnalyzer()
                    engine = RecommendationEngine()

                    # Génération du rapport HTML
                    html_content = generate_analysis_html(analyzer, engine)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                    st.success("✅ Analyse générée!")
                    st.download_button(
                        "📥 Télécharger l'analyse en HTML",
                        html_content,
                        file_name=f"analyse_jurisbot_{timestamp}.html",
                        mime="text/html",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"❌ Erreur: {e}")

    with col2:
        st.markdown("### 📄 Rapport Détaillé")
        st.write("Télécharge le rapport HTML avec tous les KPIs")
        if st.button("📥 Télécharger", key="btn_rapport", use_container_width=True):
            try:
                rapport_files = list(Path(".").glob("rapport_jurisbot_*.html"))
                if rapport_files:
                    latest_rapport = sorted(rapport_files)[-1]

                    with open(latest_rapport, "rb") as f:
                        st.download_button(
                            "💾 Télécharger le rapport",
                            f,
                            file_name=latest_rapport.name,
                            mime="text/html",
                            use_container_width=True
                        )
                    st.caption(f"Fichier: {latest_rapport.name}")
                else:
                    st.warning("⚠️ Aucun rapport trouvé. Générez d'abord une analyse.")
            except Exception as e:
                st.error(f"❌ Erreur: {e}")

    with col3:
        st.markdown("### 🗑️ Purger les Données")
        st.write("Supprime TOUTES les données stockées (irréversible)")

        with st.form(key="purge_form"):
            st.warning("⚠️ **ATTENTION:** Cette action est irréversible!")
            confirmation = st.text_input(
                "Tapez 'CONFIRMER' pour purger:",
                placeholder="CONFIRMER"
            )
            submit_purge = st.form_submit_button("🚨 Purger les données", use_container_width=True)

            if submit_purge:
                if confirmation.upper() == "CONFIRMER":
                    try:
                        with st.spinner("🗑️ Suppression en cours..."):
                            from db import clear_all_data
                            export_all_data()
                            result = clear_all_data()
                            if result:
                                st.success("✅ Données purgées avec succès!")
                                st.balloons()
                            else:
                                st.error("❌ Erreur lors de la purge")
                    except Exception as e:
                        st.error(f"❌ Erreur: {str(e)}")
                else:
                    st.error("❌ Confirmation invalide. Tapez 'CONFIRMER'")

    st.markdown("---")
    st.subheader("📋 Résumé des Données")

    try:
        feedbacks = get_all_feedbacks()
        stats = get_feedback_stats()
        responses = get_db_stats()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📝 Réponses", responses.get("total_responses", 0))

        with col2:
            st.metric("💬 Feedbacks", len(feedbacks))

        with col3:
            detailed = [f for f in feedbacks if f.get("feedback_type") == "detailed"]
            st.metric("📊 Feedbacks Détaillés", len(detailed))

        with col4:
            st.metric("🚨 Hallucinations", responses.get("hallucination_rate", 0.0))

        st.markdown("---")
        st.subheader("📥 Export Données Brutes")

        col_export1, col_export2 = st.columns(2)

        with col_export1:
            if st.button("💾 Export Feedbacks JSON", use_container_width=True):
                try:
                    export_data = export_all_data()
                    total_items = len(export_data.get("responses", [])) + len(export_data.get("feedbacks", [])) + len(export_data.get("alerts", []))

                    if total_items == 0:
                        st.warning("⚠️ Base de données vide. Générez des données avant d'exporter.")
                    else:
                        json_content = json.dumps(export_data, indent=2, ensure_ascii=False)
                        st.download_button(
                            "📥 Télécharger Feedbacks",
                            json_content,
                            file_name=f"feedbacks_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                        st.success(f"✅ Export prêt! ({total_items} éléments)")
                except Exception as e:
                    st.error(f"Erreur: {e}")

        with col_export2:
            if st.button("📊 Export Analyse JSON", use_container_width=True):
                try:
                    analysis_file = "feedback_analysis.json"
                    if Path(analysis_file).exists():
                        with open(analysis_file, "r", encoding="utf-8") as f:
                            analysis_data = f.read()
                        st.download_button(
                            "📥 Télécharger Analyse",
                            analysis_data,
                            file_name=f"analyse_jurisbot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                        st.success("✅ Export prêt!")
                    else:
                        st.warning("⚠️ Fichier d'analyse non trouvé. Lancez d'abord une analyse.")
                except Exception as e:
                    st.error(f"Erreur: {e}")

    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des données: {e}")

if __name__ == "__main__":
    main()
