"""
Interface Streamlit pour l'assistant RH.
Interface utilisateur web intuitive.
"""
import sys
import os

# Ajouter le dossier src au path pour que Python trouve les modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import streamlit as st
from datetime import datetime
from typing import List, Dict

from src.agents.rh_agent import get_rh_agent
from src.core.models import UserQuery
from src.config.settings import settings


# ============================================
# CONFIGURATION DE LA PAGE
# ============================================

st.set_page_config(
    page_title="Assistant RH Safran",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================
# STYLES CSS PERSONNALISÉS
# ============================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
    }
    .sidebar-info {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)


# ============================================
# INITIALISATION DE LA SESSION
# ============================================

def initialize_session():
    """Initialise les variables de session"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if "agent" not in st.session_state:
        with st.spinner("🔧 Initialisation de l'assistant RH..."):
            st.session_state.agent = get_rh_agent()
    
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = None


# ============================================
# SIDEBAR - CONFIGURATION
# ============================================

def render_sidebar():
    """Affiche la barre latérale avec la configuration"""
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # Sélection du profil
        st.markdown("### 👤 Votre Profil")
        profile = st.selectbox(
            "Type de contrat",
            options=settings.VALID_PROFILES,
            index=0 if st.session_state.user_profile is None else settings.VALID_PROFILES.index(st.session_state.user_profile),
            help="Sélectionnez votre type de contrat pour des réponses personnalisées"
        )
        st.session_state.user_profile = profile
        
        # Sélection du domaine (optionnel)
        st.markdown("### 📋 Domaine RH")
        domaine = st.selectbox(
            "Domaine concerné (optionnel)",
            options=["Tous les domaines"] + settings.VALID_DOMAINS,
            help="Sélectionnez un domaine spécifique ou laissez sur 'Tous'"
        )
        st.session_state.domaine = None if domaine == "Tous les domaines" else domaine
        
        st.markdown("---")
        
        # Informations
        st.markdown("### ℹ️ Informations")
        st.markdown(f"""
        <div class="sidebar-info">
        <strong>Session ID:</strong><br/>
        <code>{st.session_state.thread_id}</code><br/><br/>
        <strong>Messages:</strong> {len(st.session_state.messages)}<br/>
        <strong>Modèle:</strong> {settings.LLM_MODEL}
        </div>
        """, unsafe_allow_html=True)
        
        # Bouton reset
        if st.button("🔄 Nouvelle conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.thread_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.rerun()
        
        # Aide
        with st.expander("❓ Aide"):
            st.markdown("""
            **Comment utiliser l'assistant RH ?**
            
            1. Sélectionnez votre profil (CDI, CDD, etc.)
            2. Optionnellement, choisissez un domaine RH
            3. Posez votre question dans le chat
            4. L'assistant vous répondra avec des informations personnalisées
            
            **Exemples de questions :**
            - Combien de jours de congés payés ?
            - Comment poser un arrêt maladie ?
            - Quels sont les avantages transport ?
            - Comment consulter ma fiche de paie ?
            """)


# ============================================
# ZONE DE CHAT
# ============================================

def render_chat_history():
    """Affiche l'historique des messages"""
    for message in st.session_state.messages:
        role = message["role"]
        content = message["content"]
        
        if role == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>👤 Vous ({message.get('profile', 'N/A')}):</strong><br/>
                {content}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>🤖 Assistant RH:</strong><br/>
                {content}
            </div>
            """, unsafe_allow_html=True)


def send_message(user_input: str):
    """Envoie un message à l'agent et affiche la réponse"""
    if not st.session_state.user_profile:
        st.error("⚠️ Veuillez sélectionner votre profil dans la barre latérale")
        return
    
    # Ajouter le message utilisateur
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "profile": st.session_state.user_profile,
        "timestamp": datetime.now().isoformat()
    })
    
    # Afficher le message immédiatement
    st.markdown(f"""
    <div class="chat-message user-message">
        <strong>👤 Vous ({st.session_state.user_profile}):</strong><br/>
        {user_input}
    </div>
    """, unsafe_allow_html=True)
    
    # Appeler l'agent
    with st.spinner("🤔 L'assistant réfléchit..."):
        try:
            query = UserQuery(
                query=user_input,
                user_profile=st.session_state.user_profile,
                domaine=st.session_state.domaine,
                thread_id=st.session_state.thread_id
            )
            
            response = st.session_state.agent.invoke(query)
            
            # Ajouter la réponse
            st.session_state.messages.append({
                "role": "assistant",
                "content": response.response,
                "sources_used": response.sources_used,
                "timestamp": datetime.now().isoformat()
            })
            
            # Afficher la réponse
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>🤖 Assistant RH:</strong><br/>
                {response.response}
            </div>
            """, unsafe_allow_html=True)
            
            # Afficher un indicateur si pas de sources
            if not response.sources_used:
                st.warning("ℹ️ Aucune source spécifique trouvée pour votre question")
            
        except Exception as e:
            st.error(f"❌ Erreur: {str(e)}")


# ============================================
# MAIN APP
# ============================================

def main():
    """Fonction principale de l'application"""
    
    # Initialisation
    initialize_session()
    
    # Header
    st.markdown('<div class="main-header">🤖 Assistant RH Safran</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    render_sidebar()
    
    # Zone principale
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 💬 Conversation")
        
        # Conteneur pour le chat
        chat_container = st.container()
        
        with chat_container:
            # Afficher l'historique
            if st.session_state.messages:
                render_chat_history()
            else:
                st.info("👋 Bonjour ! Je suis votre assistant RH. Comment puis-je vous aider aujourd'hui ?")
        
        # Zone de saisie (toujours en bas)
        st.markdown("---")
        
        # Formulaire de message
        with st.form(key="message_form", clear_on_submit=True):
            user_input = st.text_input(
                "Votre question",
                placeholder="Ex: Combien de jours de congés j'ai ?",
                label_visibility="collapsed"
            )
            
            col_send, col_clear = st.columns([4, 1])
            
            with col_send:
                submit = st.form_submit_button("📤 Envoyer", use_container_width=True)
            
            if submit and user_input:
                send_message(user_input)
                st.rerun()
    
    with col2:
        st.markdown("### 📚 Suggestions")
        
        suggestions = [
            "💼 Congés payés",
            "🏥 Arrêt maladie",
            "🚗 Transport",
            "💰 Fiche de paie",
            "⏰ Temps de travail",
            "🎁 Avantages"
        ]
        
        for suggestion in suggestions:
            if st.button(suggestion, use_container_width=True):
                send_message(suggestion.split(" ", 1)[1])
                st.rerun()
        
        st.markdown("---")
        
        # Statistiques
        st.markdown("### 📊 Statistiques")
        st.metric("Messages échangés", len(st.session_state.messages))
        
        if st.session_state.messages:
            user_msgs = sum(1 for m in st.session_state.messages if m["role"] == "user")
            st.metric("Vos questions", user_msgs)


# ============================================
# POINT D'ENTRÉE
# ============================================

if __name__ == "__main__":
    main()