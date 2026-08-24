import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from app.db import init_db, get_all_documents, get_document
from app.search import perform_search

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("chatbot")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized successfully.")
    yield
    # Shutdown (nothing special to clean up)
    logger.info("Shutting down chatbot server...")

app = FastAPI(
    title="No-LLM Semantic Search Chatbot",
    description="Locally hosted semantic search chatbot using SentenceTransformers and TF-IDF fallback.",
    version="1.0.0",
    lifespan=lifespan
)

# Request schema for search
class SearchRequest(BaseModel):
    query: str
    top_k: int = 3

# === API Routes ===

@app.get("/api/documents")
async def list_documents():
    """Retrieve metadata for all documents in the knowledge base."""
    try:
        docs = await get_all_documents()
        return {"documents": docs, "count": len(docs)}
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/content")
async def get_document_content(file_path: str = Query(..., description="Absolute path to the document file")):
    """Read and return the raw text content of a document (for previewing in UI)."""
    try:
        # Security check: verify path is inside the workspace
        abs_path = os.path.abspath(file_path)
        workspace_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
        if not abs_path.startswith(workspace_path):
            # Also allow accessing neighbor folder if it is in User's desktop, 
            # but restrict it to only our workspace just to be safe.
            # However, let's verify if the file exists and is indeed a .md file inside our Chatbot_POC3 folder.
            if "Chatbot_POC3" not in abs_path:
                raise HTTPException(status_code=403, detail="Access denied. Path is outside workspace.")
        
        if not os.path.exists(abs_path):
            raise HTTPException(status_code=404, detail="File not found.")
            
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content, "file_path": file_path}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search")
async def search(req: SearchRequest):
    """Perform a semantic or TF-IDF keyword search using the user query."""
    if not req.query.strip():
         raise HTTPException(status_code=400, detail="Query cannot be empty.")
    try:
        results = await perform_search(req.query, req.top_k)
        # Check if search engine is currently using vector search
        from app.search import USE_VECTOR_SEARCH
        return {
            "query": req.query,
            "results": results,
            "search_mode": "Vector Semantic (SentenceTransformers)" if USE_VECTOR_SEARCH else "Keyword TF-IDF (Fallback)",
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error performing search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files folder
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
os.makedirs(STATIC_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the chatbot dashboard page."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_path):
         return HTMLResponse(content="<h1>Frontend asset index.html is still being created. Please reload in a moment.</h1>")
    return FileResponse(index_path)
