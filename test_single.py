import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from phase3_rag_engine.rag_app import MutualFundRAG

load_dotenv()

def test_retrieval_only():
    print("--- Retrieval-Only Integration Test (Minimum SIP) ---")
    rag = MutualFundRAG(threshold=0.5)
    
    query = "What is the Minimum SIP for HDFC Large Cap Fund?"
    
    # Ensure UTF-8 output
    if sys.platform == "win32":
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

    print(f"\nQ: {query}")
    try:
        # Just test retrieval
        docs_with_scores = rag.vector_store.similarity_search_with_relevance_scores(query, k=1)
        if docs_with_scores:
            doc, score = docs_with_scores[0]
            print(f"Retrieved Doc Metadata: {doc.metadata}")
            print(f"Similarity Score: {score}")
            print(f"Snippet: {doc.page_content[:200]}...")
            if score >= 0.5:
                print("[PASS] Retrieval successful and confident!")
            else:
                print("[FAIL] Retrieval score too low.")
        else:
            print("[FAIL] No documents retrieved.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_retrieval_only()
