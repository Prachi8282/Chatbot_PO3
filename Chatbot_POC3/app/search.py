import json
import logging
import math
import re
import numpy as np
from app.db import get_all_chunks

logger = logging.getLogger("chatbot.search")

# Global variables for the model and state
EMBEDDING_MODEL = None
USE_VECTOR_SEARCH = False

# Try to load sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    logger.info("sentence-transformers detected! Attempting to load model 'all-MiniLM-L6-v2'...")
    # Load model (downloads or loads from cache)
    EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    USE_VECTOR_SEARCH = True
    logger.info("Semantic vector search engine successfully loaded.")
except Exception as e:
    logger.warning(f"Failed to load sentence-transformers ({e}). Falling back to pure Python TF-IDF engine.")
    USE_VECTOR_SEARCH = False


# --- TF-IDF Fallback Search Implementation ---

def tokenize(text):
    """Normalize and tokenize text into words."""
    text = text.lower()
    # Remove non-alphanumeric characters
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text.split()

class TFIDFSearch:
    """Lightweight, pure-Python TF-IDF retrieval system."""
    def __init__(self, chunks):
        self.chunks = chunks
        self.vocab = []
        self.idf = {}
        self.chunk_vectors = []
        self.build_index()

    def build_index(self):
        if not self.chunks:
            return
        
        # Tokenize all chunks
        tokenized_chunks = [tokenize(chunk["content"]) for chunk in self.chunks]
        
        # Calculate Document Frequency (DF)
        num_docs = len(self.chunks)
        df = {}
        for tokens in tokenized_chunks:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                df[token] = df.get(token, 0) + 1
        
        # Calculate Inverse Document Frequency (IDF)
        self.idf = {}
        for token, count in df.items():
            # Standard IDF formula with smoothing
            self.idf[token] = math.log((1 + num_docs) / (1 + count)) + 1
            
        # Build vocabulary
        self.vocab = list(self.idf.keys())
        vocab_index = {word: i for i, word in enumerate(self.vocab)}
        
        # Build vector representations for chunks
        self.chunk_vectors = []
        for tokens in tokenized_chunks:
            vector = np.zeros(len(self.vocab))
            # Calculate Term Frequency (TF)
            tf = {}
            for token in tokens:
                tf[token] = tf.get(token, 0) + 1
            
            # Compute TF-IDF
            for token, tf_val in tf.items():
                if token in vocab_index:
                    vector[vocab_index[token]] = tf_val * self.idf[token]
                    
            # Normalize the vector (L2 norm)
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            self.chunk_vectors.append(vector)

    def search(self, query, top_k=3):
        if not self.chunks or not self.vocab:
            return []
        
        query_tokens = tokenize(query)
        vocab_index = {word: i for i, word in enumerate(self.vocab)}
        
        # Build query vector
        query_vector = np.zeros(len(self.vocab))
        q_tf = {}
        for token in query_tokens:
            q_tf[token] = q_tf.get(token, 0) + 1
            
        for token, tf_val in q_tf.items():
            if token in vocab_index:
                # Apply same IDF weights to query
                query_vector[vocab_index[token]] = tf_val * self.idf[token]
                
        # Normalize query vector
        q_norm = np.linalg.norm(query_vector)
        if q_norm > 0:
            query_vector = query_vector / q_norm
        else:
            # Query has no overlapping vocabulary
            return []
            
        # Compute Cosine Similarities
        results = []
        for i, chunk_vec in enumerate(self.chunk_vectors):
            similarity = float(np.dot(chunk_vec, query_vector))
            if similarity > 0:
                results.append((similarity, self.chunks[i]))
                
        # Sort by similarity descending
        results.sort(key=lambda x: x[0], reverse=True)
        return results[:top_k]


# --- Main Search Logic ---

def get_embedding(text: str) -> np.ndarray:
    """Generate embedding vector using the local model."""
    if not USE_VECTOR_SEARCH or EMBEDDING_MODEL is None:
        return None
    return EMBEDDING_MODEL.encode(text)

async def perform_search(query: str, top_k: int = 3):
    """
    Search the database for matching chunks.
    Uses vector similarity if sentence-transformers is loaded;
    otherwise falls back to a clean TF-IDF search index.
    """
    chunks = await get_all_chunks()
    if not chunks:
        return []

    # If sentence-transformers is loaded, perform dense vector search
    if USE_VECTOR_SEARCH and EMBEDDING_MODEL is not None:
        logger.info(f"Performing vector semantic search for query: '{query}'")
        try:
            # Generate query embedding
            query_emb = EMBEDDING_MODEL.encode(query)
            query_norm = np.linalg.norm(query_emb)
            
            results = []
            for chunk in chunks:
                if chunk["embedding"] is None:
                    continue
                # Load embedding from buffer
                chunk_emb = np.frombuffer(chunk["embedding"], dtype=np.float32)
                chunk_norm = np.linalg.norm(chunk_emb)
                
                if chunk_norm > 0 and query_norm > 0:
                    similarity = float(np.dot(chunk_emb, query_emb) / (chunk_norm * query_norm))
                    # Scale similarity to 0-1 range for user friendliness if it goes negative (rare for cosine)
                    similarity = max(0.0, min(1.0, similarity))
                    # Add result
                    results.append({
                        "score": round(similarity * 100, 2), # convert to percentage
                        "content": chunk["content"],
                        "heading": chunk["heading"],
                        "document_title": chunk["title"],
                        "file_path": chunk["file_path"]
                    })
            
            # Sort by score descending
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:top_k]
            
        except Exception as ex:
            logger.error(f"Vector search failed: {ex}. Falling back to TF-IDF matching.")
            # Fall through to TF-IDF search fallback

    # Fallback to TF-IDF Search
    logger.info(f"Performing TF-IDF keyword-semantic fallback search for query: '{query}'")
    engine = TFIDFSearch(chunks)
    raw_results = engine.search(query, top_k=top_k)
    
    results = []
    for score, chunk in raw_results:
        results.append({
            "score": round(score * 100, 2), # convert to percentage
            "content": chunk["content"],
            "heading": chunk["heading"],
            "document_title": chunk["title"],
            "file_path": chunk["file_path"]
        })
        
    return results
