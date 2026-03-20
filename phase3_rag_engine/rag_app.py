import sys
try:
    import pysqlite3.dbapi2 as pysqlite3
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

import os
import json
import chromadb
import streamlit as st
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from phase4_guardrails.guardrail_manager import GuardrailManager
from dotenv import load_dotenv

# Load local environment variables from .env
load_dotenv()

class MutualFundRAG:
    def __init__(self, client=None, threshold=0.5):
        # API Key Loading (Streamlit Secrets or Environment Variables)
        try:
            self.api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            self.api_key = os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set. Please configure it using environment variables or Streamlit Secrets.")
        
        # Ensure underlying libraries can find the key
        os.environ["GOOGLE_API_KEY"] = self.api_key
        os.environ["GEMINI_API_KEY"] = self.api_key
        
        self.persist_directory = os.environ.get("CHROMA_DB_DIR", "/tmp/vector_db")
        print(f"--- RAG Loading from: {os.path.abspath(self.persist_directory)} ---")
        
        # Initialize Embeddings (must match Phase 2)
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001", 
            google_api_key=self.api_key
        )
        
        # Load Vector Store with PersistentClient
        if not client:
            client = chromadb.PersistentClient(path=self.persist_directory)
            
        self.vector_store = Chroma(
            client=client,
            embedding_function=self.embeddings,
            collection_name="mutual_fund_faq"
        )
        
        # Initialize LLM (Gemini 1.5 Flash latest for stable quota)
        self.llm = ChatGoogleGenerativeAI(
            model="models/gemini-1.5-flash", 
            google_api_key=self.api_key,
            temperature=0
        )
        
        self.threshold = threshold
        self.guardrails = GuardrailManager()

    def _normalize_query(self, query):
        """Normalizes common fund names and aliases for better retrieval."""
        query = query.lower().strip()
        
        # Comprehensive Alias Mapping
        aliases = {
            "hdfc large cap": "HDFC Large Cap Fund",
            "hdfc top 100": "HDFC Large Cap Fund",
            "hdfc mid cap": "HDFC Mid-Cap Opportunities Fund",
            "hdfc midcap": "HDFC Mid-Cap Opportunities Fund",
            "hdfc small cap": "HDFC Small Cap Fund",
            "icici large cap": "ICICI Prudential Bluechip Fund",
            "icici bluechip": "ICICI Prudential Bluechip Fund",
            "icici midcap": "ICICI Prudential MidCap Fund",
            "icici mid cap": "ICICI Prudential MidCap Fund",
            "icici small cap": "ICICI Prudential Smallcap Fund",
            "icici smallcap": "ICICI Prudential Smallcap Fund",
            "kotak large cap": "Kotak Large Cap Fund",
            "kotak midcap": "Kotak Emerging Equity Fund",
            "kotak mid cap": "Kotak Emerging Equity Fund",
            "kotak emerging": "Kotak Emerging Equity Fund",
            "kotak small cap": "Kotak Small Cap Fund"
        }
        
        for alias, full_name in aliases.items():
            if alias in query:
                # Replace or append the formal name
                query = query.replace(alias, full_name)
        
        return query

    def query(self, user_query):
        # 1. Start-of-pipeline Guardrails (STRICT PRIORITY)
        # Check PII
        if self.guardrails.contains_pii(user_query):
            return self.guardrails.get_pii_refusal()
        
        # Check Advisory/Opinion
        if self.guardrails.is_advisory_intent(user_query):
            return self.guardrails.get_advisory_refusal()
            
        # Check Multi-intent (Multiple funds or attributes)
        if self.guardrails.is_multi_intent(user_query):
            return self.guardrails.get_multi_intent_refusal()

        # 2. Enhanced Retrieval & Selection (Only proceeds if all guardrails pass)
        normalized_query = self._normalize_query(user_query)
        try:
            # Use k=3 as requested
            results = self.vector_store.similarity_search_with_relevance_scores(normalized_query, k=5)
        except Exception as e:
            print(f"Error during vector retrieval: {e}")
            return "I'm sorry, I encountered an error while retrieving data. Please try again."
        
        if not results:
            return "I'm sorry, I don't have information on that fund in my records."

        # Group by fund and select the one with the SINGLE HIGHEST relevancia score
        best_doc = results[0][0]
        max_score = results[0][1]
        
        # Ensure minimum relevance
        if max_score < self.threshold:
            # Try a broader search if first attempt was too specific
            results = self.vector_store.similarity_search_with_relevance_scores(user_query, k=3)
            if not results or results[0][1] < 0.2: # Hard floor
                return "I'm sorry, I don't have specific information for that query."
            best_doc = results[0][0]
            max_score = results[0][1]

        # Use ALL attributes from the single selected fund
        context = best_doc.page_content
        source_url = best_doc.metadata.get("source_url", "N/A")

        # 3. Prompt Engineering (Strict Natural Language Output)
        prompt_template = ChatPromptTemplate.from_template("""
        You are a factual mutual fund assistant. Use ONLY the retrieved official public sources below.
        
        Strict Instructions:
        1. Answer in a complete, natural sentence. 
           Format: "The [Attribute] of [Fund Name] is [Value]."
           Example: "The NAV of Kotak Midcap Fund is ₹147.14."
        2. If "Investment Objective" is asked, return: "The investment objective of [Fund Name] is: [Full Text]"
        3. Do NOT return raw values alone.
        4. Use ONLY the information provided in the Context.
        5. If multiple values exist (e.g., Growth vs IDCW), always pick the Growth/Direct plan value.
        6. DO NOT return multiple funds. Focus only on the primary fund mentioned in the context.
        7. Maintain a neutral, factual tone. No advice.
        
        Context:
        {context}
        
        Question: {question}
        
        Answer:
        """)

        chain = (
            {"context": lambda x: context, "question": RunnablePassthrough()}
            | prompt_template
            | self.llm
            | StrOutputParser()
        )

        try:
            response = chain.invoke(user_query)
        except Exception as e:
            error_details = str(e)
            print(f"Error during LLM invocation: {error_details}")
            if "quota" in error_details.lower():
                return "I'm sorry, the AI service is currently busy (quota exceeded). Please try again in a minute."
            return f"I'm sorry, I encountered an error while processing your request: {error_details[:100]}"
        
        # Ensure Source URL is present and correctly mapped
        source_phrase = f"Last updated from sources:\n{source_url}"
        
        # Clean response if LLM added its own URL or used old format
        import re
        response = re.sub(r"Last updated from sources:.*", "", response, flags=re.DOTALL).strip()
        
        return f"{response}\n\n{source_phrase}"

if __name__ == "__main__":
    rag = MutualFundRAG()
    questions = [
        "What is the NAV and expense ratio of HDFC Small Cap Fund?",
        "Who is the fund manager for Kotak Midcap Fund?",
        "Should I invest in ICICI Large Cap fund for 10 years?" # Should trigger refusal or factual-only answer
    ]
    
    for q in questions:
        print(f"\nQ: {q}")
        print(f"A: {rag.query(q)}")
