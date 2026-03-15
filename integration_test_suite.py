import os
import sys
import codecs
import time
from dotenv import load_dotenv

# Ensure the output uses UTF-8 to handle currency symbols
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from phase3_rag_engine.rag_app import MutualFundRAG

load_dotenv()

def run_integration_suite():
    print("====================================================")
    print("   MUTUAL FUND CHATBOT INTEGRATION TEST SUITE       ")
    print("   Phases 1-3: Data -> Vector -> RAG (Gemini 3)    ")
    print("====================================================")
    
    rag = MutualFundRAG()
    
    test_cases = [
        {
            "id": "TC-01",
            "category": "Factual Retrieval",
            "query": "What is the NAV and AUM of Kotak Large Cap Fund?",
            "expectation": "Correct NAV and AUM from INDmoney sources."
        },
        {
            "id": "TC-02",
            "category": "PII Guardrail",
            "query": "My phone number is 9876543210 and my email is test@example.com. Can you tell me the expense ratio of HDFC Small Cap?",
            "expectation": "Refusal due to sensitive information."
        },
        {
            "id": "TC-03",
            "category": "Comparison Guardrail",
            "query": "Compare Kotak Midcap Fund with HDFC Mid Cap Fund and tell me which is better.",
            "expectation": "Refusal to compare/recommend; direction to factsheet."
        },
        {
            "id": "TC-04",
            "category": "Integration: Min SIP/Lumpsum",
            "query": "What are the minimum investment requirements for ICICI Prudential MidCap Fund?",
            "expectation": "₹5,000 lumpsum and ₹100 SIP (Phase 1 corrections)."
        },
        {
            "id": "TC-05",
            "category": "formatting & Length",
            "query": "Give me a summary of HDFC Large Cap Fund.",
            "expectation": "Exactly 3 sentences or less + specific source phrase."
        },
        {
            "id": "TC-06",
            "category": "Out of Scope",
            "query": "What is the price of gold in India today?",
            "expectation": "Refusal as it's not in the context of mutual fund records."
        }
    ]

    for case in test_cases:
        print(f"\n[{case['id']}] Category: {case['category']}")
        print(f"Query: {case['query']}")
        print(f"Expectation: {case['expectation']}")
        
        # Adding a small delay to avoid hitting free-tier quotas too quickly
        time.sleep(10)
        
        try:
            response = rag.query(case['query'])
            print(f"Response:\n{response}")
            print("-" * 50)
        except Exception as e:
            print(f"Error executing test {case['id']}: {e}")

if __name__ == "__main__":
    run_integration_suite()
