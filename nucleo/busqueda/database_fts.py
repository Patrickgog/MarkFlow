"""Gestor de índice SQLite FTS5 para búsqueda de texto completo y historial de snapshots."""

import sqlite3
import hashlib
import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path


class FTS5Index:
    """Clase para manejar índice FTS5 de SQLite para búsqueda instantánea."""
    
    def __init__(self, db_path: str = "storage/outputs/genoffice_index.db"):
        self.db_path = db_path
        self.conn = None
        self._init_db()
    
    def _init_db(self) -> None:
        """Inicializa la base de datos con tablas FTS5 y historial."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        
        # Crear tabla FTS5 para búsqueda de texto completo
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents USING fts5(
                title,
                content,
                path,
                tags,
                content_unindexed
            )
        """)
        
        # Crear tabla de snapshots para rollback
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_path TEXT NOT NULL,
                hash_sha256 CHAR(64) NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                state_name TEXT,
                file_data BLOB
            )
        """)
        
        # Tabla de metadatos de archivos
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS file_metadata (
                path TEXT PRIMARY KEY,
                last_modified DATETIME,
                file_size INTEGER,
                file_hash CHAR(64)
            )
        """)
        
        self.conn.commit()
    
    def index_document(self, 
                       doc_path: str, 
                       title: str, 
                       content: str, 
                       tags: Optional[List[str]] = None,
                       content_unindexed: Optional[str] = None) -> None:
        """Indexa un documento en la base de datos FTS5."""
        # Remover índice previo si existe
        self.conn.execute("DELETE FROM documents WHERE path = ?", (doc_path,))
        
        # Insertar nuevo índice
        tags_str = ','.join(tags) if tags else ''
        self.conn.execute(
            "INSERT INTO documents (title, content, path, tags, content_unindexed) VALUES (?, ?, ?, ?, ?)",
            (title, content, doc_path, tags_str, content_unindexed)
        )
        
        # Guardar metadatos
        file_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        self.conn.execute(
            """INSERT OR REPLACE INTO file_metadata (path, file_hash) VALUES (?, ?)""",
            (doc_path, file_hash)
        )
        
        self.conn.commit()
    
    def remove_document(self, doc_path: str) -> None:
        """Elimina un documento del índice (al borrarlo del almacén)."""
        self.conn.execute("DELETE FROM documents WHERE path = ?", (doc_path,))
        self.conn.execute("DELETE FROM file_metadata WHERE path = ?", (doc_path,))
        self.conn.commit()

    def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Busca documentos por contenido usando FTS5."""
        cursor = self.conn.execute(
            """SELECT path, title,
                    rank,
                    snippet(documents, 1, '<mark>', '</mark>', '…', 24) as snippet
             FROM documents
             WHERE documents MATCH ?
             ORDER BY rank
             LIMIT ?""",
            (f'"{query}"', limit),
        )
        
        results = []
        for row in cursor:
            results.append({
                "path": row[0],
                "title": row[1],
                "rank": row[2],
                "snippet": row[3]
            })
        
        return results
    
    def take_snapshot(self, doc_path: str, file_data: bytes, state_name: str = "") -> str:
        """Toma un snapshot del documento para rollback."""
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        self.conn.execute(
            """INSERT INTO snapshots (doc_path, hash_sha256, state_name, file_data) 
               VALUES (?, ?, ?, ?)""",
            (doc_path, file_hash, state_name, sqlite3.Binary(file_data))
        )
        
        self.conn.commit()
        
        # Retornar el ID del snapshot
        snapshot_id = self.conn.execute(
            "SELECT last_insert_rowid() FROM snapshots"
        ).fetchone()[0]
        
        return str(snapshot_id)
    
    def rollback_to_snapshot(self, snapshot_id: int) -> Optional[bytes]:
        """Restaura un documento a un snapshot anterior."""
        cursor = self.conn.execute(
            "SELECT file_data FROM snapshots WHERE id = ?",
            (snapshot_id,)
        )
        
        row = cursor.fetchone()
        if row:
            return bytes(row[0])
        return None
    
    def close(self) -> None:
        """Cierra la conexión a la base de datos."""
        if self.conn:
            self.conn.close()