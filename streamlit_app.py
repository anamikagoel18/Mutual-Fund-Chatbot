import sys
import os

# 1. SQLite Fix for Streamlit Cloud
try:
    import pysqlite3
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

import sqlite3
import json
import time
import streamlit as st
import chromadb
from phase2_vector_store.ingest import ingest_data
from phase3_rag_engine.rag_app import MutualFundRAG
from phase4_guardrails.guardrail_manager import GuardrailManager

# Page configuration
st.set_page_config(
    page_title="Mutual Fund Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium UI
st.markdown("""
<style>
    /* Dark Theme Base */
    .stApp {
        background-color: #0E1117;
        color: #E0E0E0;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
    
    /* Chat Bubble Styling */
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }
    
    /* User Message Bubble */
    [data-testid="stChatMessageUser"] {
        background-color: #238636;
        border: 1px solid #2EA043;
    }
    
    /* Assistant Message Bubble */
    [data-testid="stChatMessageAssistant"] {
        background-color: #21262D;
        border: 1px solid #30363D;
    }
    
    /* Custom Header */
    .chat-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 0px;
        border-bottom: 2px solid #30363D;
        margin-bottom: 20px;
    }
    
    .status-online {
        color: #3FB950;
        font-size: 0.8em;
    }
    
    /* Fund List Item */
    .fund-list-item {
        padding: 8px;
        margin: 5px 0px;
        background: #0D1117;
        border-radius: 8px;
        border: 1px solid #30363D;
        font-size: 0.9em;
    }
    
    /* Quick Prompt Buttons */
    .stButton > button {
        background-color: #21262D;
        color: #C9D1D9;
        border: 1px solid #30363D;
        border-radius: 8px;
        width: 100%;
        text-align: left;
    }
</style>
""", unsafe_allow_html=True)

# API Key Loading
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("GEMINI_API_KEY is not set. Please configure it in Streamlit Secrets or .env.")
    st.stop()

# Persistent Path
DB_PATH = "/tmp/vector_db"

# Initialization
if "db_initialized" not in st.session_state:
    with st.status("🚀 Preparing Mutual Fund Database...", expanded=True) as status:
        st.write("Initializing vector store...")
        try:
            # Ensure Ingestion runs once (per session, to handle ephemeral /tmp)
            ingest_data() 
            
            # Load Backend Engines
            shared_client = chromadb.PersistentClient(path=DB_PATH)
            st.session_state.guardrails = GuardrailManager()
            st.session_state.rag = MutualFundRAG(client=shared_client)
            
            st.session_state.db_initialized = True
            status.update(label="Initialization Complete!", state="complete", expanded=False)
        except Exception as e:
            st.error(f"Initialization Failed: {e}")
            st.stop()

# Sidebar Content
with st.sidebar:
    st.title("🤖 Mutual Fund Bot")
    st.markdown('<div class="status-online">● Online</div>', unsafe_allow_html=True)
    st.divider()
    
    st.subheader("📊 AVAILABLE FUNDS")
    search_query = st.text_input("Search funds...", placeholder="Type to filter...")
    
    # Load funds list for display
    try:
        with open("structured_funds.json", "r", encoding="utf-8") as f:
            funds_data = json.load(f)
            fund_names = [f["Fund Name"] for f in funds_data]
    except:
        fund_names = ["HDFC Large Cap", "Kotak Midcap", "ICICI Smallcap"] # Fallback
    
    filtered_funds = [f for f in fund_names if search_query.lower() in f.lower()]
    for name in filtered_funds:
        st.markdown(f'<div class="fund-list-item">{name}</div>', unsafe_allow_html=True)

# Main Header
col1, col2 = st.columns([1, 1])
with col1:
    st.markdown('### 💬 Mutual Fund Assistant')
with col2:
    if st.button("🗑️ Clear Chat", use_container_width=False):
        st.session_state.messages = []
        st.rerun()

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your Mutual Fund Factual Assistant. How can I help you today?"}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("Ask about NAV, AUM, or Expense Ratio..."):
    # Add User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate Assistant Response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing fund data..."):
            try:
                # 1. Guardrail Checks
                response = None
                if st.session_state.guardrails.contains_pii(prompt):
                    response = st.session_state.guardrails.get_pii_refusal()
                elif st.session_state.guardrails.is_advisory_intent(prompt):
                    response = st.session_state.guardrails.get_advisory_refusal()
                elif st.session_state.guardrails.is_multi_intent(prompt):
                    response = st.session_state.guardrails.get_multi_intent_refusal()
                
                # 2. RAG Query
                if not response:
                    response = st.session_state.rag.query(prompt)
                
                # Display and Save
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                err = "I encountered an error. Please try again."
                st.error(f"Error: {e}")
                st.session_state.messages.append({"role": "assistant", "content": err})
