import sys
import os

# 1. SQLite Fix for Streamlit Cloud
try:
    import pysqlite3.dbapi2 as pysqlite3
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

# Custom CSS for Premium UI (Focused on Interactivity and Alignment)
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
    
    /* Modern Chat Bubble Styling */
    .stChatMessage {
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 12px;
        width: fit-content;
        max-width: 80%;
    }
    
    /* User Message Bubble (Blue, Right Aligned) */
    [data-testid="stChatMessageUser"] {
        background-color: #1A3E7A !important;
        border: 1px solid #2B5797 !important;
        margin-left: auto !important;
    }
    
    /* Assistant Message Bubble (Dark Grey/Navy, Left Aligned) */
    [data-testid="stChatMessageAssistant"] {
        background-color: #10192A !important;
        border: 1px solid #1A2436 !important;
        margin-right: auto !important;
    }
    
    /* Hide Default Avatar */
    [data-testid="stChatMessage"] .st-emotion-cache-1c7n2ka {
        display: none;
    }
    
    /* Source text as muted small */
    .source-text {
        color: #8B949E;
        font-size: 0.8em;
        margin-top: 10px;
        border-top: 1px solid #1A2436;
        padding-top: 5px;
    }
    
    /* Fund Button Styling (Sidebar) */
    .stButton > button {
        background-color: #10192A !important;
        color: #C9D1D9 !important;
        border: 1px solid #1A2436 !important;
        border-radius: 10px !important;
        text-align: left !important;
        padding: 12px !important;
        width: 100% !important;
        display: block !important;
    }
    
    .stButton > button:hover {
        border-color: #2B5797 !important;
        background-color: #1A2436 !important;
    }
    
    /* Highlight Selected Fund */
    .selected-fund-btn > button {
        border-color: #58A6FF !important;
        background-color: #161B22 !important;
        box-shadow: 0 0 5px rgba(88, 166, 255, 0.3);
    }
    
    /* Pill Button Style for Quick Prompts */
    .pill-btn > button {
        border-radius: 30px !important;
        padding: 5px 15px !important;
        font-size: 0.8em !important;
        background-color: #0D1117 !important;
    }
    
    /* Ensure chat input is clean */
    .stChatInput {
        padding-bottom: 20px !important;
    }
    
    /* Visibility Overrides */
    h1, h2, h3, [data-testid="stSidebarNav"] span, .stSubheader {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    
    .status-online {
        color: #4BD863 !important;
        font-weight: bold;
    }
    
    .stMarkdown p {
        color: #E0E0E0;
    }
</style>
""", unsafe_allow_html=True)

# Initialization
if "db_initialized" not in st.session_state:
    with st.status("🛠️ Initializing Data Systems...", expanded=True) as status:
        try:
            ingest_data() 
            shared_client = chromadb.PersistentClient(path="/tmp/vector_db")
            st.session_state.guardrails = GuardrailManager()
            st.session_state.rag = MutualFundRAG(client=shared_client)
            st.session_state.db_initialized = True
            status.update(label="System Ready!", state="complete", expanded=False)
        except Exception as e:
            st.error(f"Initialization Failed: {e}")
            st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am your Mutual Fund Factual Assistant. How can I help you today?"}]

if "selected_fund" not in st.session_state:
    st.session_state.selected_fund = None

# Sidebar: Fund List
with st.sidebar:
    st.markdown('<h1 style="color: white; margin-bottom: 0;">🤖 Mutual Fund Bot</h1>', unsafe_allow_html=True)
    st.markdown('<div class="status-online">● Online</div>', unsafe_allow_html=True)
    st.divider()
    
    st.markdown('<b style="color: white; font-size: 1.1em;">AVAILABLE FUNDS</b>', unsafe_allow_html=True)
    try:
        with open("structured_funds.json", "r", encoding="utf-8") as f:
            funds_data = json.load(f)
            # Custom sort: Kotak -> HDFC -> ICICI, and Large -> Mid -> Small
            amc_order = {"Kotak Mutual Fund": 0, "HDFC Mutual Fund": 1, "ICICI Mutual Fund": 2}
            cat_order = {"Large-Cap": 0, "Mid-Cap": 1, "Small-Cap": 2}
            funds_data.sort(key=lambda x: (amc_order.get(x["AMC"], 99), cat_order.get(x["Category"], 99)))
    except:
        funds_data = []

    for fund in funds_data:
        fname = fund["Fund Name"]
        fcat = fund["Category"]
        is_selected = st.session_state.selected_fund and st.session_state.selected_fund["Fund Name"] == fname
        
        # Wrap button in a div class for highlighting
        btn_class = "selected-fund-btn" if is_selected else "normal-fund-btn"
        st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
        if st.button(f"**{fname}**\n{fcat}", key=f"sidebar_{fname}"):
            st.session_state.selected_fund = fund
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# Main 3-Column Layout
left_gap, chat_col, right_col = st.columns([0.1, 4, 2])

with chat_col:
    # Header area
    head_col1, head_col2 = st.columns([5, 1])
    with head_col1:
        st.markdown("### 💬 Mutual Fund Assistant")
    with head_col2:
        if st.button("Clear Chat", key="btn_clear_chat"):
            st.session_state.messages = [{"role": "assistant", "content": "Hello! I am your Mutual Fund Factual Assistant. How can I help you today?"}]
            st.rerun()
    
    st.divider()

    # 1. Display Message History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            content = msg["content"]
            if "Last updated from sources:" in content:
                parts = content.split("Last updated from sources:")
                st.markdown(parts[0].strip())
                url = parts[1].strip()
                st.markdown(f'<div class="source-text">Last updated from sources:<br><a href="{url}" target="_blank" style="color: #58A6FF; text-decoration: none;">{url}</a></div>', unsafe_allow_html=True)
            else:
                st.markdown(content)

    # 2. Input Bar
    if prompt := st.chat_input("Ask about NAV, AUM, or specific fund details..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    # 3. Response Generation (Triggers whenever the last message is from user)
    if st.session_state.messages[-1]["role"] == "user":
        with st.chat_message("assistant"):
            with st.spinner("Analyzing fund data..."):
                try:
                    user_query = st.session_state.messages[-1]["content"]
                    response = None
                    
                    # Guardrails
                    if st.session_state.guardrails.contains_pii(user_query):
                        response = st.session_state.guardrails.get_pii_refusal()
                    elif st.session_state.guardrails.is_advisory_intent(user_query):
                        response = st.session_state.guardrails.get_advisory_refusal()
                    elif st.session_state.guardrails.is_multi_intent(user_query):
                        response = st.session_state.guardrails.get_multi_intent_refusal()
                    
                    if not response:
                        response = st.session_state.rag.query(user_query)
                    
                    # Store and Display
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    if "Last updated from sources:" in response:
                        parts = response.split("Last updated from sources:")
                        st.markdown(parts[0].strip())
                        url = parts[1].strip()
                        st.markdown(f'<div class="source-text">Last updated from sources:<br><a href="{url}" target="_blank" style="color: #58A6FF; text-decoration: none;">{url}</a></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(response)
                    
                    st.rerun() # Refresh to stop the spinner and finalize state
                except Exception as e:
                    st.error(f"Error: {e}")

# Right Column: Quick Prompts
with right_col:
    st.markdown('<b style="color: white; font-size: 1.1em;">QUICK PROMPTS</b>', unsafe_allow_html=True)
    st.markdown('<div class="pill-btn">', unsafe_allow_html=True)
    
    # Define prompts based on selection
    if st.session_state.selected_fund:
        current_fund = st.session_state.selected_fund["Fund Name"]
        prompts = [
            f"What is the NAV of {current_fund}?",
            f"Expense ratio of {current_fund}?",
            f"Who manages {current_fund}?",
            f"Minimum SIP for {current_fund}?"
        ]
    else:
        prompts = [
            "What is the exit load of ICICI Prudential LargeCap Fund?",
            "What is the expense ratio of Kotak Midcap Fund?",
            "What is the investment objective of HDFC Mid Cap Fund?",
            "What is the minimum SIP for ICICI Smallcap Fund?"
        ]
        
    for p in prompts:
        if st.button(p, key=f"pill_{p}"):
            st.session_state.messages.append({"role": "user", "content": p})
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
