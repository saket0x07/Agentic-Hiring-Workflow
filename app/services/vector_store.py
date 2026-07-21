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
        dimension: int = 384,
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
            return faiss.read_index(str(self.index_path))
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

    def add_resume(self, resume_id: str, embedding: list[float]):
        vector = np.array([embedding], dtype="float32")
        self.index.add(vector)
        self.mapping.append({"id": resume_id})
        self._save()

    def search(self, embedding: list[float], top_k: int = 10):
        vector = np.array([embedding], dtype="float32")
        scores, indices = self.index.search(vector, top_k)
        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx == -1:
                continue
            results.append({"resume_id": self.mapping[idx]["id"], "score": float(score)})
        return results

    def total_vectors(self) -> int:
        return self.index.ntotal