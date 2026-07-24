import json
from pathlib import Path

import faiss
import numpy as np


class VectorStore:
    """
    FAISS Vector Store for resume embeddings.
    """

    def __init__(
        self,
        dimension: int = 768,
        index_path: str = "./data/vector_store/resume.index",
        mapping_path: str = "./data/vector_store/resume_mapping.json",
    ):
        self.dimension = dimension
        self.index_path = Path(index_path)
        self.mapping_path = Path(mapping_path)

        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.mapping_path.parent.mkdir(parents=True, exist_ok=True)

        self.index = self._load_or_create_index()
        self.mapping = self._load_mapping()

    def _load_or_create_index(self):
        if self.index_path.exists():
            idx = faiss.read_index(str(self.index_path))
            if idx.d == self.dimension:
                return idx
            # Index dimension mismatch - recreate index with new dimension
            if self.mapping_path.exists():
                self.mapping_path.unlink(missing_ok=True)
        return faiss.IndexFlatIP(self.dimension)

    def _load_mapping(self):
        if self.mapping_path.exists():
            with open(self.mapping_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save(self):
        faiss.write_index(self.index, str(self.index_path))
        with open(self.mapping_path, "w", encoding="utf-8") as f:
            json.dump(self.mapping, f, indent=4)

    def clear_index(self):
        """Clear all stored vectors and mapping files."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.mapping = []
        if self.index_path.exists():
            self.index_path.unlink(missing_ok=True)
        if self.mapping_path.exists():
            self.mapping_path.unlink(missing_ok=True)
        self._save()

    def delete_resume(self, resume_id: str):
        """Delete a resume by ID from FAISS index and mapping file (removes all its chunks)."""
        if not self.mapping:
            return
            
        remaining_mappings = []
        remaining_vectors = []
        
        for i, item in enumerate(self.mapping):
            item_id = item.get("id") or item.get("resume_id")
            if item_id != resume_id:
                remaining_mappings.append(item)
                if i < self.index.ntotal:
                    vec = self.index.reconstruct(i)
                    remaining_vectors.append(vec)
                    
        # Re-create index
        self.index = faiss.IndexFlatIP(self.dimension)
        self.mapping = remaining_mappings
        
        if remaining_vectors:
            matrix = np.array(remaining_vectors, dtype="float32")
            self.index.add(matrix)
            
        self._save()

    def add_resume(self, resume_id: str, embedding: list[float]):
        """Legacy method to add a single full resume embedding."""
        vector = np.array([embedding], dtype="float32")
        self.index.add(vector)
        self.mapping.append({
            "id": resume_id,
            "resume_id": resume_id,
            "chunk_type": "full_document",
            "chunk_text": ""
        })
        self._save()

    def add_resume_chunks(self, resume_id: str, chunks: list[dict]):
        """Add multiple section chunk embeddings for a single candidate resume."""
        if not chunks:
            return
        embeddings = [c["embedding"] for c in chunks if "embedding" in c]
        if not embeddings:
            return
        matrix = np.array(embeddings, dtype="float32")
        self.index.add(matrix)
        for c in chunks:
            if "embedding" in c:
                self.mapping.append({
                    "id": resume_id,
                    "resume_id": resume_id,
                    "chunk_type": c.get("chunk_type", "summary"),
                    "chunk_text": c.get("text", "")
                })
        self._save()

    def search(self, embedding: list[float], top_k: int = 10):
        """
        Search FAISS index with a query vector.
        Aggregates multiple chunk hits per candidate using MaxSim (highest matching chunk score).
        """
        if self.index.ntotal == 0:
            return []
        
        # Search for enough chunk hits to cover top_k distinct candidates
        n_search = min(max(top_k * 5, 20), self.index.ntotal)
        vector = np.array([embedding], dtype="float32")
        scores, indices = self.index.search(vector, n_search)
        
        candidate_matches = {}
        for idx, score in zip(indices[0], scores[0]):
            if idx == -1 or idx >= len(self.mapping):
                continue
            item = self.mapping[idx]
            res_id = item.get("id") or item.get("resume_id")
            if not res_id:
                continue
            
            flt_score = float(score)
            if res_id not in candidate_matches:
                candidate_matches[res_id] = {
                    "resume_id": res_id,
                    "score": flt_score,
                    "matched_chunk_type": item.get("chunk_type", ""),
                    "matched_chunk_text": item.get("chunk_text", "")
                }
            else:
                # MaxSim: Keep the highest scoring chunk for this candidate
                if flt_score > candidate_matches[res_id]["score"]:
                    candidate_matches[res_id]["score"] = flt_score
                    candidate_matches[res_id]["matched_chunk_type"] = item.get("chunk_type", "")
                    candidate_matches[res_id]["matched_chunk_text"] = item.get("chunk_text", "")

        # Sort aggregated candidates by max similarity score descending
        sorted_candidates = sorted(candidate_matches.values(), key=lambda x: x["score"], reverse=True)
        return sorted_candidates[:top_k]

    def total_vectors(self) -> int:
        return self.index.ntotal