import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

def verify_retrieval():
    base_dir = os.getcwd()
    persist_directory = os.path.join(base_dir, "vector_db")
    api_key = os.environ.get("GOOGLE_API_KEY")

    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)
    
    vector_store = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
        collection_name="mutual_fund_faq"
    )

    query = "What is the expense ratio and fund manager of Kotak Large Cap Fund?"
    print(f"Querying: {query}")
    
    docs = vector_store.similarity_search_with_relevance_scores(query, k=1)
    
    for doc, score in docs:
        print(f"\nSimilarity Score: {score}")
        print(f"Retrieved Fund: {doc.metadata.get('fund_name')}")
        print(f"Source URL: {doc.metadata.get('source_url')}")
        print("\nContent Snippet:")
        print(doc.page_content[:500] + "...")

if __name__ == "__main__":
    verify_retrieval()
