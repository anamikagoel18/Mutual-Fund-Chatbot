from phase3_rag_engine.rag_app import MutualFundRAG
import os

def test_rag_locally():
    print("Initializing RAG Engine...")
    try:
        rag = MutualFundRAG()
        print("RAG Engine Initialized.")
        
        query = "What is the NAV of HDFC Large Cap?"
        print(f"Querying: {query}")
        response = rag.query(query)
        print(f"Response: {response}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")

if __name__ == "__main__":
    test_rag_locally()
