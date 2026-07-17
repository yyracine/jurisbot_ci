import streamlit as st
import json
from datetime import datetime
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

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

        return answer, response_id

def submit_feedback(response_id: str, feedback_type: str, detailed_feedback: dict = None):
    """Soumet le feedback à la base de données SQLite"""
    if feedback_type == "positive":
        add_feedback(
            response_id=response_id,
            feedback_type="quick",
            feedback="thumbs_up",
            is_hallucination=False
        )
    elif feedback_type == "negative":
        add_feedback(
            response_id=response_id,
            feedback_type="quick",
            feedback="thumbs_down",
            is_hallucination=False
        )
    elif feedback_type == "hallucination":
        add_feedback(
            response_id=response_id,
            feedback_type="quick",
            feedback="hallucination",
            is_hallucination=True
        )
    elif feedback_type == "detailed" and detailed_feedback:
        add_feedback(
            response_id=response_id,
            feedback_type="detailed",
            accuracy=detailed_feedback.get("accuracy"),
            clarity=detailed_feedback.get("clarity"),
            citations=detailed_feedback.get("citations"),
            completeness=detailed_feedback.get("completeness"),
            comments=detailed_feedback.get("comments"),
            email=detailed_feedback.get("email", "anonymous")
        )

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

        password = st.text_input(
            "Mot de passe d'accès:",
            type="password",
            placeholder="Entrez votre mot de passe"
        )

        if st.button("Accéder", use_container_width=True):
            admin_password = os.getenv("ADMIN_PASSWORD", "")

            if not admin_password:
                st.error("❌ Configuration manquante: ADMIN_PASSWORD non défini dans .env")
                st.stop()

            if password == admin_password:
                st.session_state.authenticated = True
                st.session_state.is_admin = True
                st.success("✅ Accès administrateur activé!")
                st.rerun()
            else:
                st.session_state.authenticated = True
                st.session_state.is_admin = False
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
            page = st.radio("Navigation", ["Chat", "Statistiques", "Feedbacks", "Analyse & Recommandations"])
            st.markdown("---")
            st.info(f"👤 Mode: **Admin**")
        else:
            page = "Chat"
            st.info(f"👤 Mode: **Testeur**\n\nVous accédez uniquement au formulaire de feedback.")

        st.markdown("---")
        if st.button("🔒 Déconnexion", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.is_admin = False
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
    else:
        show_analysis_page()

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
            if st.button("📊 Export Analyse JSON"):
                filepath = analyzer.export_report_json()
                with open(filepath, "r", encoding="utf-8") as f:
                    json_data = f.read()
                st.download_button("Télécharger Analyse", json_data, file_name=filepath.split("/")[-1], mime="application/json")

        with col2:
            if st.button("🗺️ Export Recommandations JSON"):
                filepath = engine.export_recommendations()
                with open(filepath, "r", encoding="utf-8") as f:
                    json_data = f.read()
                st.download_button("Télécharger Recommandations", json_data, file_name=filepath.split("/")[-1], mime="application/json")

    except Exception as e:
        st.error(f"❌ Erreur lors de l'analyse: {e}")
        st.info("Assurez-vous d'avoir assez de données pour l'analyse (au moins 5 feedbacks)")

if __name__ == "__main__":
    main()
