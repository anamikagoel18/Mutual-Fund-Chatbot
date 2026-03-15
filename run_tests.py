import os
import sys
import json
import time
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

# Add the project root to sys.path to import the RAG app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from phase3_rag_engine.rag_app import MutualFundRAG

load_dotenv()

def test_phase2_vector_store():
    print("--- Testing Phase 2: Vector Store ---")
    base_dir = os.getcwd()
    persist_directory = os.path.join(base_dir, "vector_db")
    api_key = os.environ.get("GOOGLE_API_KEY")

    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)
    
    try:
        vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings,
            collection_name="mutual_fund_faq"
        )
        
        # Test 1: Document Count
        # Chroma collection count
        count = vector_store._collection.count()
        print(f"[PASS] Document Count: {count} (Expected: 9)")
        assert count == 9
        
        # Test 2: Metadata verification
        docs = vector_store.similarity_search("Kotak Large Cap", k=1)
        if docs:
            meta = docs[0].metadata
            print(f"[PASS] Metadata check: {meta.get('fund_name')} - {meta.get('source_url')}")
            assert "Kotak Large Cap" in meta.get('fund_name')
            assert "source_url" in meta
        
        return True
    except Exception as e:
        print(f"[FAIL] Phase 2 Testing encountered an error: {e}")
        return False

def test_phase3_rag_engine():
    print("\n--- Testing Phase 3: RAG Engine ---")
    rag = MutualFundRAG(threshold=0.5)
    
    test_cases = [
        {
            "name": "Factual Question: NAV",
            "query": "What is the current NAV of ICICI Prudential Large Cap Fund?",
            "check": lambda res: "NAV" in res and "₹" in res
        },
        {
            "name": "Factual Question: Expense Ratio",
            "query": "What is the expense ratio of HDFC Mid Cap Fund?",
            "check": lambda res: "%" in res and "HDFC Mid Cap" in res
        },
        {
            "name": "Factual Question: Minimum SIP",
            "query": "What is the Minimum SIP for HDFC Large Cap Fund?",
            "check": lambda res: "HDFC Large Cap" in res and "₹100" in res # Expected value based on common SIPs or specific scraping
        },
        {
            "name": "Factual Question: Fund Manager",
            "query": "Who manages the Kotak Midcap Fund?",
            "check": lambda res: "Pankaj Tibrewal" in res or "Ankit Sancheti" in res
        },
        {
            "name": "Integration: AMC and Category",
            "query": "Tell me the AMC and Category for ICICI Prudential Smallcap Fund.",
            "check": lambda res: "ICICI Prudential" in res and "Small Cap" in res
        },
        {
            "name": "Integration: Minimum Lumpsum",
            "query": "What is the minimum lumpsum investment for ICICI Prudential MidCap Fund?",
            "check": lambda res: "₹5,000" in res # User explicitly corrected this in Phase 1
        },
        {
            "name": "Formatting: 3 Sentence Limit",
            "query": "Give me a summary of Kotak Small Cap Fund including manager and inception date.",
            "check": lambda res: len([s for s in res.split("\n\n")[0].split('.') if len(s.strip()) > 5]) <= 3
        },
        {
            "name": "Guardrail: Low Confidence Rejection",
            "query": "Who is the Prime Minister of India?",
            "check": lambda res: "I'm sorry" in res or "not provide" in res or "don't have" in res
        },
        {
            "name": "Guardrail: Investment Advice Blocking",
            "query": "Is it a good time to buy HDFC Mid Cap Fund?",
            "check": lambda res: "I'm sorry" in res or "not provide investment advice" in res or "factual" in res
        },
        {
            "name": "Link Validation: exactly one link",
            "query": "Provide the source for ICICI Prudential Smallcap Fund details.",
            "check": lambda res: res.count("https://") == 1
        }
    ]
    
    all_passed = True
    for case in test_cases:
        print(f"Running Test: {case['name']}...")
        time.sleep(10) # Respect Gemini Free Tier rate limits (15 RPM + Cooldowns)
        try:
            response = rag.query(case['query'])
            if case['check'](response):
                print(f"[PASS] {case['name']}")
            else:
                print(f"[FAIL] {case['name']}")
                print(f"      Response: {response}")
                all_passed = False
        except Exception as e:
            print(f"[ERROR] {case['name']}: {e}")
            all_passed = False
            
    return all_passed

if __name__ == "__main__":
    # Ensure UTF-8 output for Rupee symbols
    if sys.platform == "win32":
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    
    p2 = test_phase2_vector_store()
    p3 = test_phase3_rag_engine()
    
    if p2 and p3:
        print("\n[CONCLUSION] ALL TEST PHASES PASSED!")
    else:
        print("\n[CONCLUSION] SOME TESTS FAILED. CHECK LOGS.")
