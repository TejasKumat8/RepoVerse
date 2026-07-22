import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.core.config import settings

class VectorStore:
    def __init__(self, repo_id: str):
        self.repo_id = repo_id
        self.vector_dir = settings.STORAGE_DIR / "vectors" / repo_id
        self.vector_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.vector_dir / "index.json"
        
        self.chunks: List[Dict[str, Any]] = []
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            token_pattern=r'(?u)\b\w+\b|[^\w\s]',
            sublinear_tf=True
        )
        self.tfidf_matrix = None
        self.is_indexed = False

    def build_index(self, chunks: List[Dict[str, Any]]):
        self.chunks = chunks
        if not chunks:
            self.is_indexed = False
            return

        corpus = [f"{c['file_path']} {c['language']}\n{c['content']}" for c in chunks]
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self.is_indexed = True

        # Save to disk
        self.save_index()

    def save_index(self):
        data = {
            "repo_id": self.repo_id,
            "chunks": self.chunks
        }
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_index(self) -> bool:
        if not self.index_file.exists():
            return False
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.chunks = data.get("chunks", [])
            if self.chunks:
                corpus = [f"{c['file_path']} {c['language']}\n{c['content']}" for c in self.chunks]
                self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
                self.is_indexed = True
                return True
        except Exception:
            pass
        return False

    def search(self, query: str, top_k: int = 6) -> List[Dict[str, Any]]:
        if not self.is_indexed or self.tfidf_matrix is None or not self.chunks:
            return []

        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score > 0.01:  # Filter completely non-matching chunks
                chunk = self.chunks[idx].copy()
                chunk["score"] = round(score, 4)
                results.append(chunk)

        # Fallback if no scores > 0.01: return top 3 chunks anyway
        if not results and len(self.chunks) > 0:
            for idx in top_indices[:3]:
                chunk = self.chunks[idx].copy()
                chunk["score"] = float(scores[idx])
                results.append(chunk)

        return results
