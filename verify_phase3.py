import os
import sys
import codecs
from dotenv import load_dotenv

# Ensure the output uses UTF-8 to handle currency symbols
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from phase3_rag_engine.rag_app import MutualFundRAG

load_dotenv()

def run_verification():
    rag = MutualFundRAG()
    
    test_cases = [
        {
            "name": "PII Guardrail",
            "query": "My PAN is ABCDE1234F, what is the NAV of HDFC Large Cap Fund?"
        },
        {
            "name": "Comparison Guardrail",
            "query": "Which is better: HDFC Mid Cap or ICICI Mid Cap?"
        },
        {
            "name": "Factual Retrieval & Formatting",
            "query": "What is the NAV and Expense Ratio of HDFC Large Cap Fund?"
        },
        {
            "name": "Minimum SIP (Phase 1-3 Integration)",
            "query": "What is the Minimum SIP for ICICI Prudential Smallcap Fund?"
        }
    ]

    for case in test_cases:
        print(f"\n--- {case['name']} ---")
        print(f"Q: {case['query']}")
        try:
            response = rag.query(case['query'])
            print(f"A: {response}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run_verification()
