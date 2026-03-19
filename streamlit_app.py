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

# Custom CSS for Premium Navy UI
st.markdown("""
<style>
    /* Navy Theme Base */
    .stApp {
        background-color: #050A18;
        color: #E0E0E0;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #081021;
        border-right: 1px solid #1A2436;
    }
    
    /* Chat Bubble Styling */
    .stChatMessage {
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 12px;
    }
    
    /* User Message Bubble (Blue) */
    [data-testid="stChatMessageUser"] {
        background-color: #1A3E7A;
        border: 1px solid #2B5797;
    }
    
    /* Assistant Message Bubble (Dark Grey/Navy) */
    [data-testid="stChatMessageAssistant"] {
        background-color: #10192A;
        border: 1px solid #1A2436;
    }
    
    /* Top Search Bar Styling */
    .stTextInput input {
        background-color: #081021;
        border: 1px solid #1A2436;
        color: white;
    }
    
    /* Status indicator */
    .status-badge {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.9em;
    }
    .status-dot {
        height: 8px;
        width: 8px;
        background-color: #3FB950;
        border-radius: 50%;
    }
    
    /* Quick Prompt Buttons */
    .stButton > button {
        background-color: #10192A !important;
        color: #C9D1D9 !important;
        border: 1px solid #1A2436 !important;
        border-radius: 8px !important;
        text-align: left !important;
        padding: 10px !important;
        font-size: 0.85em !important;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        border-color: #2B5797 !important;
        background-color: #1A2436 !important;
    }
    
    /* Fund Button Styling (Sidebar) */
    .fund-btn-container {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px;
        margin-bottom: 5px;
        background: transparent;
    }
    
    .fund-icon {
        background-color: #1A3E7A;
        color: white;
        width: 30px;
        height: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 6px;
        font-weight: bold;
    }
    
    /* Clear Chat Link Style */
    .clear-chat-link {
        color: #FF4B4B;
        cursor: pointer;
        font-size: 0.85em;
        text-decoration: none;
        float: right;
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
    st.error("GEMINI_API_KEY is not set.")
    st.stop()

DB_PATH = "/tmp/vector_db"

# Initialization
if "db_initialized" not in st.session_state:
    with st.status("🚀 Initializing...", expanded=True) as status:
        try:
            ingest_data() 
            shared_client = chromadb.PersistentClient(path=DB_PATH)
            st.session_state.guardrails = GuardrailManager()
            st.session_state.rag = MutualFundRAG(client=shared_client)
            st.session_state.db_initialized = True
            status.update(label="Ready!", state="complete", expanded=False)
        except Exception as e:
            st.error(f"Failed: {e}")
            st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am your Mutual Fund Factual Assistant. How can I help you today?"}]

if "selected_fund" not in st.session_state:
    st.session_state.selected_fund = None

# Sidebar
with st.sidebar:
    st.title("Mutual Fund Chatbot")
    st.divider()
    
    st.subheader("AVAILABLE FUNDS")
    
    # Load funds data
    try:
        with open("structured_funds.json", "r", encoding="utf-8") as f:
            funds_data = json.load(f)
    except:
        funds_data = []

    for fund in funds_data:
        fund_name = fund["Fund Name"]
        category = fund["Category"]
        first_letter = fund_name[0]
        
        # Use columns to mimic the complex button layout
        col_icon, col_text = st.columns([1, 4])
        with col_icon:
            st.markdown(f'<div class="fund-icon">{first_letter}</div>', unsafe_allow_html=True)
        with col_text:
            if st.button(f"**{fund_name}**\n{category}", key=f"btn_{fund_name}"):
                st.session_state.selected_fund = fund
                # Auto-prompt if clicked? For now just select.
    
# Main Layout
# 3 Columns for main area
left_pad, main_col, right_col = st.columns([0.1, 3.5, 1.5])

with main_col:
    # Header
    head1, head2 = st.columns([4, 1])
    with head1:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 15px;">
            <div style="font-size: 30px;">🤖</div>
            <div>
                <b style="font-size: 1.2em;">Mutual Fund Factual Assistant</b><br>
                <span class="status-badge"><div class="status-dot"></div> Online</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with head2:
        if st.button("🗑️ Clear Chat", key="clear_chat_main"):
            st.session_state.messages = [{"role": "assistant", "content": "Hello! I am your Mutual Fund Factual Assistant. How can I help you today?"}]
            st.session_state.selected_fund = None
            st.rerun()

    st.divider()

    # Chat Area
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input at bottom
    if prompt := st.chat_input("Ask anything about mutual funds..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun() # Refresh to show user message immediately

# Response logic (run outside columns to avoid formatting issues if needed, but here it's fine)
if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
    user_p = st.session_state.messages[-1]["content"]
    with main_col:
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                try:
                    # Guardrails
                    resp = None
                    if st.session_state.guardrails.contains_pii(user_p):
                        resp = st.session_state.guardrails.get_pii_refusal()
                    elif st.session_state.guardrails.is_advisory_intent(user_p):
                        resp = st.session_state.guardrails.get_advisory_refusal()
                    elif st.session_state.guardrails.is_multi_intent(user_p):
                        resp = st.session_state.guardrails.get_multi_intent_refusal()
                    
                    if not resp:
                        resp = st.session_state.rag.query(user_p)
                    
                    st.markdown(resp)
                    st.session_state.messages.append({"role": "assistant", "content": resp})
                except Exception as e:
                    st.error(f"Error: {e}")

# Right Column: Quick Prompts & Context
with right_col:
    st.subheader("QUICK PROMPTS")
    prompts = [
        "What is the NAV of HDFC Large Cap?",
        "Who manages Kotak Small Cap?",
        "ICICI MidCap expense ratio?",
        "Minimum SIP for HDFC Mid Cap?"
    ]
    for p in prompts:
        if st.button(p, key=f"prompt_{p}"):
            st.session_state.messages.append({"role": "user", "content": p})
            st.rerun()

    st.divider()
    st.subheader("FUND CONTEXT")
    if st.session_state.selected_fund:
        f = st.session_state.selected_fund
        st.info(f"""
        **Selected**: {f['Fund Name']}
        - **AMC**: {f['AMC']}
        - **Category**: {f['Category']}
        - **Inception**: {f['Inception Date']}
        """)
        if st.button("Query Selected Fund Details"):
            st.session_state.messages.append({"role": "user", "content": f"Give me details for {f['Fund Name']}"})
            st.rerun()
    else:
        st.write("Select a fund from the sidebar for contextual questions.")
