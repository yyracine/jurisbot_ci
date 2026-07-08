# app.py
import streamlit as st
import requests

# ==========================================
# CONFIGURATION DE L'API
# ==========================================
API_URL = "http://localhost:8000/api/v1/ask"
# Clé API de test (correspond à la MOCK_SAAS_DB dans api.py)
API_KEY = "sk-pme-abidjan-123" 

# ==========================================
# INTERFACE STREAMLIT
# ==========================================
st.set_page_config(page_title="JurisBot CI", page_icon="⚖️", layout="centered")
st.title("⚖️ JurisBot CI")
st.caption("Assistant Droit du Travail Ivoirien - Propulsé par Mistral AI")

# Bouton pour vider l'historique
if st.sidebar.button("🗑️ Nouvelle discussion"):
    st.session_state.messages = []
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("💡 Quota restant : {quota} questions")

# Gestion de l'historique
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage de l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Afficher les sources si c'est une réponse de l'assistant
        if message["role"] == "assistant" and "sources" in message:
            with st.expander("📚 Voir les sources juridiques"):
                for src in message["sources"]:
                    st.markdown(f"**{src['source_name']}**")
                    st.caption(src['snippet'])

# Zone de saisie
if prompt := st.chat_input("Posez votre question sur le Code du Travail..."):
    # 1. Afficher la question
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Appeler l'API FastAPI
    with st.chat_message("assistant"):
        with st.spinner("🔍 Recherche dans le Code du Travail..."):
            try:
                response = requests.post(
                    API_URL,
                    headers={"X-API-Key": "token_pme_abidjan_123", "Content-Type": "application/json"}, # ✅ Correct
                    json={"query": prompt},
                    timeout=120
                )
                
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data["answer"]
                    sources = data["sources"]
                    quota = data["quota_remaining"]
                    
                    # ✅ LOG DE DEBUG : Voir ce que le frontend reçoit
                    print(f"\n📥 FRONTEND A REÇU (RÉPONSE COMPLÈTE) :\n{answer}\n")
                    print(f" FIN DE LA RÉPONSE\n")
    
                    # Afficher la réponse
                    st.markdown(answer)
                    
                    # Sauvegarder dans l'historique avec les sources
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": answer,
                        "sources": sources
                    })
                    
                    # Afficher le quota restant en bas
                    st.caption(f"💡 Quota restant : {quota} questions")
                    
                else:
                    error_msg = response.json().get("detail", "Erreur inconnue")
                    st.error(f"❌ Erreur API : {error_msg}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Impossible de contacter le serveur API. Assurez-vous que `api.py` est lancé sur le port 8000.")
            except Exception as e:
                st.error(f"❌ Une erreur s'est produite : {str(e)}")