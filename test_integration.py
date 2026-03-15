import os
import sys
import time
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from phase3_rag_engine.rag_app import MutualFundRAG

load_dotenv()

def run_focused_tests():
    print("--- Focused Integration Tests (Phases 1-3) ---")
    rag = MutualFundRAG(threshold=0.5)
    
    test_queries = [
        "What is the Minimum SIP for HDFC Large Cap Fund?",
        "What is the Minimum Lumpsum for ICICI Prudential MidCap Fund?",
        "Who is the fund manager for Kotak Small Cap Fund?",
        "Provide a summary for ICICI Prudential Large Cap Fund in 3 sentences."
    ]
    
    # Ensure UTF-8 output
    if sys.platform == "win32":
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

    for query in test_queries:
        print(f"\nQ: {query}")
        print("Waiting 15 seconds for quota stability...")
        time.sleep(15)
        try:
            answer = rag.query(query)
            print(f"A: {answer}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run_focused_tests()
