import os
import sqlite3
import json
import logging
import aiosqlite

logger = logging.getLogger("chatbot.db")

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chatbot.db"))

async def init_db():
    """Initialize the database schema."""
    logger.info(f"Initializing database at: {DB_PATH}")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        
        # Create documents table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                file_path TEXT NOT NULL UNIQUE,
                content TEXT NOT NULL
            );
        """)
        
        # Create chunks table (stores document paragraphs, headings, and optional vector embeddings)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                chunk_index INTEGER,
                heading TEXT,
                content TEXT NOT NULL,
                embedding BLOB,
                FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
            );
        """)
        await db.commit()

async def save_document(title: str, file_path: str, content: str) -> int:
    """Save or update a document in the database and return its ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Upsert document
        cursor = await db.execute(
            "SELECT id FROM documents WHERE file_path = ?", 
            (file_path,)
        )
        row = await cursor.fetchone()
        if row:
            doc_id = row[0]
            await db.execute(
                "UPDATE documents SET title = ?, content = ? WHERE id = ?",
                (title, content, doc_id)
            )
            # Clear old chunks for this document
            await db.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
        else:
            cursor = await db.execute(
                "INSERT INTO documents (title, file_path, content) VALUES (?, ?, ?)",
                (title, file_path, content)
            )
            doc_id = cursor.lastrowid
        await db.commit()
        return doc_id

async def save_chunk(doc_id: int, chunk_index: int, heading: str, content: str, embedding: bytes = None):
    """Save a chunk of a document along with its embedding vector bytes."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO chunks (document_id, chunk_index, heading, content, embedding) VALUES (?, ?, ?, ?, ?)",
            (doc_id, chunk_index, heading, content, embedding)
        )
        await db.commit()

async def get_all_chunks():
    """Retrieve all chunks from the database for similarity matching."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT chunks.id, chunks.document_id, chunks.chunk_index, chunks.heading, 
                   chunks.content, chunks.embedding, documents.title, documents.file_path
            FROM chunks
            JOIN documents ON chunks.document_id = documents.id
        """)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_all_documents():
    """Retrieve metadata of all indexed documents."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT id, title, file_path, length(content) as char_count FROM documents")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_document(doc_id: int):
    """Retrieve full details of a specific document."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
