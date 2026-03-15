import os
import sys

# Add project root to sys.path to resolve module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from phase3_rag_engine.rag_app import MutualFundRAG
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Mutual Fund RAG Chatbot API")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG Engine
try:
    rag_engine = MutualFundRAG()
except Exception as e:
    print(f"Error initializing RAG Engine: {e}")
    rag_engine = None

# Mount Static Files (Frontend)
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
print(f"DEBUG: Serving static files from: {frontend_path}")
if not os.path.exists(frontend_path):
    print(f"ERROR: Frontend path does not exist!")
app.mount("/ui", StaticFiles(directory=frontend_path, html=True), name="ui")

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str

@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "rag_engine": "initialized" if rag_engine else "failed"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not rag_engine:
        raise HTTPException(status_code=500, detail="RAG Engine not initialized. Check API keys and vector store.")
    
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    try:
        response_text = rag_engine.query(request.query)
        return ChatResponse(response=response_text)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
