import os
import json
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv
from phase4_guardrails.guardrail_manager import GuardrailManager

# Load environment variables
load_dotenv()

class MutualFundRAG:
    def __init__(self, threshold=0.5):
        self.api_key = os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment.")
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.persist_directory = os.path.join(base_dir, "vector_db")
        
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

    def _format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def query(self, user_query):
        # 1. Start-of-pipeline Guardrails (PII & Intent)
        if self.guardrails.contains_pii(user_query):
            return self.guardrails.get_pii_refusal()
        
        if self.guardrails.is_advisory_intent(user_query):
            return self.guardrails.get_advisory_refusal()

        if self.guardrails.is_multi_intent(user_query):
            return self.guardrails.get_multi_intent_refusal()

        # 2. Retrieval with Similarity Score
        try:
            results = self.vector_store.similarity_search_with_relevance_scores(user_query, k=2)
        except Exception as e:
            print(f"Error during vector retrieval: {e}")
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                return "I'm sorry, I've exceeded my search quota for today. Please try again later."
            return "I'm sorry, I encountered an error while retrieving data. Please try again."
        
        if not results or results[0][1] < self.threshold:
            return "I'm sorry, I don't have the specific information for that attribute in my records."

        retrieved_docs = [res[0] for res in results]
        context = self._format_docs(retrieved_docs)
        source_url = retrieved_docs[0].metadata.get("source_url", "N/A")

        # 3. Prompt Engineering
        prompt_template = ChatPromptTemplate.from_template("""
        You are a factual mutual fund assistant. Use ONLY the retrieved official public sources below to answer the user's question.
        
        Strict Instructions:
        1. Answer ONLY the specific attribute asked in the question (e.g., expense ratio, exit load, AUM, benchmark).
        2. DO NOT include additional fund details such as fund manager, category, or investment objective unless explicitly asked.
        3. If multiple values are found for the requested attribute, pick ONLY the mathematically valid primary one. For example, if AUM has two values, return only the primary fund size in Cr.
        4. Keep the answer extremely concise, maximum 1 sentence. State the final value clearly.
        5. Never provide investment advice, personal opinions, or recommendations.
        6. If the specific attribute information is not found in the retrieved context, return a low-confidence response: "I'm sorry, I don't have the specific information for that attribute in my records."
        
        Context:
        {context}
        
        Question: {question}
        
        Answer Format:
        [Concise attribute Answer Text]
        Last updated from sources: {source_url}
        """)

        # 3. Execution Chain
        chain = (
            {"context": lambda x: context, "source_url": lambda x: source_url, "question": RunnablePassthrough()}
            | prompt_template
            | self.llm
            | StrOutputParser()
        )

        try:
            response = chain.invoke(user_query)
        except Exception as e:
            print(f"Error during LLM invocation: {e}")
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                return "I'm sorry, I've exceeded my search quota for today. Please try again later."
            return "I'm sorry, I encountered an error while processing your request. Please try again."
        
        # Post-generation validation for specific phrase
        source_phrase = f"Last updated from sources: {source_url}"
        if source_phrase not in response:
            # Clean response if LLM hallucinated a different format or multiple links
            lines = response.split('\n')
            final_text = " ".join([l for l in lines if "http" not in l and l.strip()])
            response = f"{final_text}\n\n{source_phrase}"
            
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
