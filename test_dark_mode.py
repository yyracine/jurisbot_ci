import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv(override=True)

st.set_page_config(page_title="Dark Mode Test", layout="wide")

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

def apply_theme():
    dark = st.session_state.dark_mode
    
    css = f"""
    <style>
        :root {{
            color-scheme: {'dark' if dark else 'light'};
        }}
        
        body, [data-testid="stAppViewContainer"] {{
            background-color: {'#0e1117' if dark else '#ffffff'} !important;
            color: {'#e6edf3' if dark else '#000000'} !important;
        }}
        
        [data-testid="stSidebar"] {{
            background-color: {'#161b22' if dark else '#f6f8fa'} !important;
        }}
        
        /* Force text color */
        div, p, span, h1, h2, h3, h4, h5, h6 {{
            color: {'#e6edf3' if dark else '#000000'} !important;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

apply_theme()

st.title("🌙 Dark Mode Test")

col1, col2 = st.columns([3, 1])
with col1:
    st.write("Toggle le dark mode dans la colonne de droite")
with col2:
    st.session_state.dark_mode = st.toggle("🌙 Dark", st.session_state.dark_mode)

st.markdown("---")
st.info(f"Mode: {'Dark 🌙' if st.session_state.dark_mode else 'Light ☀️'}")
st.success("Test réussi!")
