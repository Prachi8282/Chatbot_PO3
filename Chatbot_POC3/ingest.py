import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

import os
import re
import asyncio
import logging
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("chatbot.ingest")

# Imports from our app
from app.db import init_db, save_document, save_chunk

DOCUMENTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "documents"))

# Try to import embedding model packages
USE_EMBEDDINGS = False
embedding_model = None

try:
    from sentence_transformers import SentenceTransformer
    logger.info("sentence-transformers loaded successfully in ingestion pipeline. Loading model 'all-MiniLM-L6-v2'...")
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    USE_EMBEDDINGS = True
    logger.info("Embedding model loaded.")
except Exception as e:
    logger.warning(f"Could not load sentence-transformers in ingestion script ({e}). Chunks will be indexed without vector embeddings (fallback TF-IDF mode only).")
    USE_EMBEDDINGS = False

def parse_markdown_document(content):
    """
    Parses a markdown document into chunks based on markdown headings.
    Returns a list of tuples: (heading, content)
    """
    lines = content.split("\n")
    chunks = []
    
    current_heading = "General"
    current_chunk_lines = []
    
    for line in lines:
        line_strip = line.strip()
        
        # Check if line is a markdown heading (excluding document title # )
        if line_strip.startswith("##"):
            # Save previous chunk if it has content
            if current_chunk_lines:
                chunk_text = "\n".join(current_chunk_lines).strip()
                if chunk_text:
                    chunks.append((current_heading, chunk_text))
            
            # Start new chunk
            # Remove markdown hash tags
            current_heading = re.sub(r'^#+\s*', '', line_strip)
            current_chunk_lines = []
        elif line_strip.startswith("# ") and not current_chunk_lines:
            # Document title, skip adding as section but set as starting heading
            current_heading = re.sub(r'^#\s*', '', line_strip)
        else:
            current_chunk_lines.append(line)
            
    # Save the last chunk
    if current_chunk_lines:
        chunk_text = "\n".join(current_chunk_lines).strip()
        if chunk_text:
            chunks.append((current_heading, chunk_text))
            
    return chunks

async def ingest_documents():
    # 1. Initialize the database schema
    logger.info("Initializing database...")
    await init_db()
    
    # 2. Check if documents directory exists
    if not os.path.exists(DOCUMENTS_DIR):
        logger.error(f"Documents directory not found at: {DOCUMENTS_DIR}")
        return
        
    files = [f for f in os.listdir(DOCUMENTS_DIR) if f.endswith(".md")]
    logger.info(f"Found {len(files)} markdown documents in {DOCUMENTS_DIR}")
    
    for file_name in files:
        file_path = os.path.join(DOCUMENTS_DIR, file_name)
        logger.info(f"Processing: {file_name}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Extract title from the first header or use file name
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else file_name.replace(".md", "").replace("_", " ").title()
        
        # Save document metadata and get its database ID
        doc_id = await save_document(title, file_path, content)
        
        # Parse document into heading + paragraph chunks
        chunks = parse_markdown_document(content)
        logger.info(f"Parsed {len(chunks)} chunks for document '{title}'")
        
        # Save each chunk in the database
        for index, (heading, chunk_content) in enumerate(chunks):
            embedding_bytes = None
            
            # Generate vector embedding if possible
            if USE_EMBEDDINGS and embedding_model is not None:
                try:
                    # We combine heading and content to include structural metadata in the embedding
                    text_to_embed = f"{heading}: {chunk_content}" if heading else chunk_content
                    vector = embedding_model.encode(text_to_embed)
                    # Convert float32 array to raw binary bytes
                    embedding_bytes = np.array(vector, dtype=np.float32).tobytes()
                except Exception as ex:
                    logger.error(f"Failed to generate embedding for chunk {index}: {ex}")
                    
            await save_chunk(doc_id, index, heading, chunk_content, embedding_bytes)
            
        logger.info(f"Successfully indexed document '{title}' (ID: {doc_id})")

if __name__ == "__main__":
    asyncio.run(ingest_documents())
    logger.info("Ingestion process completed successfully.")
