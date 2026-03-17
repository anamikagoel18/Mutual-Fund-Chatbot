try:
    import pysqlite3
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass
except Exception:
    pass

import sqlite3
print(f"--- Ingesting with SQLite Version: {sqlite3.sqlite_version} ---")

import json
import os
import streamlit as st
import hashlib
from dotenv import load_dotenv

# Load local environment variables from .env
load_dotenv()
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

def generate_id(fund_name):
    """Generates a unique and stable ID based on the fund name."""
    return hashlib.md5(fund_name.encode()).hexdigest()

def ingest_data():
    # API Key Loading (Streamlit Secrets or Environment Variables)
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set. Please configure it using environment variables or Streamlit Secrets.")

    # Ensure underlying libraries can find the key
    os.environ["GOOGLE_API_KEY"] = api_key
    os.environ["GEMINI_API_KEY"] = api_key

    # Paths
    persist_directory = os.environ.get("CHROMA_DB_DIR", "/tmp/vector_db")
    os.makedirs(persist_directory, exist_ok=True)
    print(f"--- Using Vector DB Dir: {os.path.abspath(persist_directory)} ---")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "phase1_data_acquisition", "structured_funds.json")

    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found. Run Phase 1 first.")
        return

    # Load data
    with open(data_path, "r", encoding="utf-8") as f:
        funds = json.load(f)

    documents = []
    ids = []
    
    for fund in funds:
        fund_name = fund.get('Fund Name')
        if not fund_name:
            continue
            
        # Create a cohesive text block for the document content
        content = f"Fund Name: {fund_name}\n"
        content += f"AMC: {fund.get('AMC')}\n"
        content += f"Category: {fund.get('Category')}\n"
        content += f"NAV: {fund.get('NAV')}\n"
        content += f"Expense Ratio: {fund.get('Expense Ratio')}\n"
        content += f"Benchmark: {fund.get('Benchmark')}\n"
        content += f"AUM: {fund.get('AUM')}\n"
        content += f"Inception Date: {fund.get('Inception Date')}\n"
        content += f"Minimum Lumpsum: {fund.get('Minimum Lumpsum')}\n"
        content += f"Minimum SIP: {fund.get('Minimum SIP')}\n"
        content += f"Exit Load: {fund.get('Exit Load')}\n"
        content += f"Lock-in Period: {fund.get('Lock-in Period')}\n"
        content += f"Portfolio Turnover: {fund.get('Portfolio Turnover')}\n"
        content += f"Riskometer: {fund.get('Riskometer')}\n"
        content += f"Fund Manager: {fund.get('Fund Manager')}\n"
        content += f"Investment Objective: {fund.get('Investment Objective')}\n"
        content += f"Source URL: {fund.get('Source URL')}\n"

        # Define metadata (Include all fields for strict consistency checks)
        metadata = {
            "fund_name": fund_name,
            "source_url": fund.get("Source URL"),
            "fund_category": fund.get("Category"),
            "scheme_type": "Direct" if "Direct" in fund.get("Source URL", "") or "Direct" in fund_name else "Regular",
            "NAV": fund.get("NAV"),
            "AUM": fund.get("AUM"),
            "Minimum Lumpsum": fund.get("Minimum Lumpsum"),
            "Minimum SIP": fund.get("Minimum SIP"),
            "Expense Ratio": fund.get("Expense Ratio"),
            "Benchmark": fund.get("Benchmark"),
            "Inception Date": fund.get("Inception Date"),
            "Exit Load": fund.get("Exit Load"),
            "Lock-in Period": fund.get("Lock-in Period"),
            "Portfolio Turnover": fund.get("Portfolio Turnover"),
            "Riskometer": fund.get("Riskometer"),
            "Fund Manager": fund.get("Fund Manager")
        }

        # Create Document object
        doc = Document(page_content=content, metadata=metadata)
        documents.append(doc)
        ids.append(generate_id(fund_name))

    # Initialize Embeddings
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in environment or .env file.")
        return

    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)

    persist_directory = os.environ.get("CHROMA_DB_DIR", "/tmp/vector_db")
    print(f"--- Ingesting to: {os.path.abspath(persist_directory)} ---")
    
    # Initialize ChromaDB
    vector_store = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
        collection_name="mutual_fund_faq"
    )
    
    # Add/Update documents using stable IDs
    # Chroma's .add_documents performs an upsert if IDs are provided and already exist
    print("Writing to persistent storage...")
    vector_store.add_documents(documents=documents, ids=ids)
    
    print(f"--- Ingestion Completed Successfully: {len(documents)} documents processed ---")

if __name__ == "__main__":
    print("--- Starting Manual Data Ingestion ---")
    ingest_data()
