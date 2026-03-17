import sys
try:
    import pysqlite3.dbapi2 as pysqlite3
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

import sqlite3
# Log SQLite details
print(f"--- ACTIVE SQLITE VERSION: {sqlite3.sqlite_version} ---")
print(f"--- SQLITE SOURCE: {getattr(sqlite3, '__file__', 'builtin')} ---")

import json
import os
import sys
import hashlib
import streamlit as st
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from dotenv import load_dotenv

# Load local environment variables from .env
load_dotenv()

# Ensure the project root is in path for imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from phase2_vector_store.ingest import ingest_data
from phase3_rag_engine.rag_app import MutualFundRAG
from phase4_guardrails.guardrail_manager import GuardrailManager

# API Key Loading (Streamlit Secrets or Environment Variables)
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("GEMINI_API_KEY is not set. Please configure it using environment variables or Streamlit Secrets.")
    st.stop()

# Ensure the key is set in environment for underlying libraries if needed
os.environ["GEMINI_API_KEY"] = api_key
os.environ["GOOGLE_API_KEY"] = api_key

# Page configuration
st.set_page_config(
    page_title="Mutual Fund Chatbot",
    page_icon="🤖",
    layout="wide"
)

# Sidebar with project info
with st.sidebar:
    st.title("About Project")
    st.info("""
    **Mutual Fund Factual Assistant**
    - **RAG Engine**: Gemini 1.5 Flash
    - **Vector Store**: ChromaDB
    - **Guardrails**: PII, Advisory, Multi-intent
    """)
    st.divider()
    st.success("App Status: Online")
    
    if st.button("Clear History"):
        st.session_state.messages = []
        st.rerun()

# Initialization (Run once per session)
if "db_initialized" not in st.session_state:
    with st.status("🛠️ Initializing Application...", expanded=True) as status:
        import shutil
        import time
        # Use a unique path to rule out caching/locks
        db_path = f"/tmp/vector_db_{int(time.time())}"
        st.write(f"Setting up unique database at: {db_path}")
        
        try:
            os.makedirs(db_path, exist_ok=True)
            
            # Diagnostic: Show Versions
            import sqlite3
            st.write(f"SQLite Engine Version: `{sqlite3.sqlite_version}`")
            if sqlite3.sqlite_version_info < (3, 35, 0):
                 st.warning("SQLite version is below 3.35.0. ChromaDB may fail. Attempting to proceed...")
            
            # Trigger Ingestion
            st.write("Ingesting fund data into vector store...")
            
            # Sub-diagnostic: Test raw SQLite
            try:
                import sqlite3
                conn = sqlite3.connect(":memory:")
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE test_bootstrap (id INTEGER PRIMARY KEY)")
                conn.commit()
                st.write("✅ Raw SQLite bootstrap test passed.")
                conn.close()
            except Exception as se:
                st.error(f"Raw SQLite test failed: {se}")
            
            ingest_data()
            st.write(f"Files in {db_path} after ingestion: `{os.listdir(db_path)}`")
            
            # Initialize Backend Logic
            st.session_state.guardrails = GuardrailManager()
            st.session_state.rag = MutualFundRAG()
            
            st.session_state.db_initialized = True
            st.write("✅ Initialization Complete.")
            status.update(label="Initialization Complete!", state="complete", expanded=False)
        except Exception as e:
            st.error(f"Critical Error during initialization: {e}")
            st.stop()

# Application UI
st.title("🤖 Mutual Fund Chatbot")
st.markdown("Ask me factual questions about Mutual Funds (NAV, AUM, Objective, etc.).")

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Interaction
if prompt := st.chat_input("What is the NAV of Kotak Large Cap Fund?"):
    # Clearer separation of chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Response generation
    with st.chat_message("assistant"):
        try:
            # 1. Check Guardrail Flow BEFORE RAG
            response = None
            
            # PII Check
            if st.session_state.guardrails.contains_pii(prompt):
                response = st.session_state.guardrails.get_pii_refusal()
            
            # Advisory Check
            if not response and st.session_state.guardrails.is_advisory_intent(prompt):
                response = st.session_state.guardrails.get_advisory_refusal()
            
            # Multi-intent Check
            if not response and st.session_state.guardrails.is_multi_intent(prompt):
                response = st.session_state.guardrails.get_multi_intent_refusal()
            
            # 2. Only if all pass -> call RAG
            if not response:
                with st.spinner("Analyzing funds..."):
                    response = st.session_state.rag.query(prompt)
            
            # Display response
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
        except Exception as e:
            error_message = "I encountered an error while processing your request."
            st.error(error_message)
            # Log for backend monitoring
            print(f"ERROR: {e}")
