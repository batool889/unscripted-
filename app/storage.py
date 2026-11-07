import json
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS chunks (id TEXT PRIMARY KEY, document_id TEXT, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS courses (code TEXT PRIMARY KEY, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, payload TEXT NOT NULL);
"""

def read_db(path: Path):
    if not path.exists(): raise RuntimeError("Knowledge index not found. Run python -m app.ingestion first.")
    return sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)

def load_table(path: Path, table: str):
    if table not in {"chunks", "courses", "documents", "meta"}: raise ValueError("Unknown table")
    with read_db(path) as con:
        return [json.loads(r[0]) for r in con.execute(f"SELECT payload FROM {table}")]

def build_db(path, chunks, courses, documents, meta):
    con=sqlite3.connect(path)
    try:
        con.executescript(SCHEMA)
        with con:
            for t in ["chunks", "courses", "documents", "meta"]: con.execute(f"DELETE FROM {t}")
            con.executemany("INSERT INTO chunks VALUES (?,?,?)", [(c["source_id"],c["document_id"],json.dumps(c,ensure_ascii=False)) for c in chunks])
            con.executemany("INSERT INTO courses VALUES (?,?)", [(c["course_code"],json.dumps(c,ensure_ascii=False)) for c in courses])
            con.executemany("INSERT INTO documents VALUES (?,?)", [(d["document_id"],json.dumps(d,ensure_ascii=False)) for d in documents])
            con.executemany("INSERT INTO meta VALUES (?,?)", [(k,json.dumps(v,ensure_ascii=False)) for k,v in meta.items()])
    finally: con.close()

class VectorStore:
    def __init__(self, path, name, create=False):
        import chromadb
        from chromadb.config import Settings
        self.client=chromadb.PersistentClient(path=str(path),settings=Settings(anonymized_telemetry=False))
        if create:
            self.collection=self.client.get_or_create_collection(name,embedding_function=None,metadata={"hnsw:space":"cosine"})
        else: self.collection=self.client.get_collection(name,embedding_function=None)
    def upsert(self,chunks,embeddings):
        self.collection.upsert(ids=[c["source_id"] for c in chunks],embeddings=embeddings,
                               metadatas=[{"document_id":c["document_id"],"institution":"nnu"} for c in chunks])
    def query(self,embedding,k):
        if not self.collection.count(): return []
        result=self.collection.query(query_embeddings=[embedding],n_results=min(k,self.collection.count()),include=["distances"])
        return list(zip(result["ids"][0],result["distances"][0]))
