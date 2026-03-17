try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except (ImportError, KeyError):
    pass

import os
import json
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
    def __init__(self, threshold=0.5):
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
        
        # Load Vector Store
        self.vector_store = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
            collection_name="mutual_fund_faq"
        )
        
        # Initialize LLM (Gemini 1.5 Flash latest for stable quota)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-flash-latest", 
            google_api_key=self.api_key,
            temperature=0
        )
        
        self.threshold = threshold
        self.guardrails = GuardrailManager()

    def _normalize_query(self, query):
        """Normalizes common fund names and aliases for better retrieval."""
        query = query.lower()
        aliases = {
            "hdfc large cap": "HDFC Top 100 Fund", # Common alias for their large cap
            "hdfc mid cap": "HDFC Mid-Cap Opportunities Fund",
            "icici midcap": "ICICI Prudential MidCap Fund",
            "icici large cap": "ICICI Prudential Bluechip Fund",
            "kotak large cap": "Kotak Large Cap Fund",
            "kotak midcap": "Kotak Emerging Equity Fund"
        }
        for alias, full_name in aliases.items():
            if alias in query:
                # Add full name to query for better vector match
                query += f" {full_name}"
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

        # 3. Prompt Engineering (No truncation for objectives)
        prompt_template = ChatPromptTemplate.from_template("""
        You are a factual mutual fund assistant. Use ONLY the retrieved official public sources below.
        
        Strict Instructions:
        1. Answer ONLY the specific attribute asked (e.g., NAV, expense ratio, AUM).
        2. If "Investment Objective" is asked, return the FULL text provided in the context. Do NOT truncate or summarize it.
        3. For other attributes, be concise but ensure the exact value from the source is used.
        4. If multiple values exist for one attribute in the context, pick the primary direct plan value. 
        5. DO NOT return duplicate values.
        6. Always maintain a neutral, factual tone. No investment advice.
        7. Format: [Answer Text]
        
        Context:
        {context}
        
        Question: {question}
        
        Answer Text:
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
            print(f"Error during LLM invocation: {e}")
            return "I'm sorry, I encountered an error while processing your request."
        
        # Ensure Source URL is present and correctly mapped from selected metadata
        source_phrase = f"Last updated from sources: {source_url}"
        if "Last updated from sources" not in response:
            response = f"{response.strip()}\n\n{source_phrase}"
        else:
            # Replace any hallucinated URL with the one from metadata
            import re
            response = re.sub(r"Last updated from sources: .*", source_phrase, response)
            
        return response

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
