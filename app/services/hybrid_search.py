import re
import json
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi

from app.services.vector_store import VectorStore
from app.services.resume_service import ResumeService
from app.services.embedding_service import EmbeddingService


def tokenize_text(text: str) -> List[str]:
    """Tokenize and normalize text for BM25 keyword matching."""
    if not text:
        return []
    # Lowercase and extract alphanumeric words
    tokens = re.findall(r"\b\w+\b", text.lower())
    return tokens


class HybridSearchService:
    """
    Hybrid Search combining BM25 Keyword Search and FAISS Dense Vector Search
    with Reciprocal Rank Fusion (RRF).
    """

    def __init__(self, rrf_k: int = 60):
        self.vector_store = VectorStore()
        self.resume_service = ResumeService()
        self.embedding_service = EmbeddingService()
        self.rrf_k = rrf_k

    def build_resume_corpus_text(self, resume_id: str, profile_dict_or_obj: Any) -> str:
        """Construct full text document for BM25 indexing."""
        if not profile_dict_or_obj:
            return resume_id
        
        parts = [resume_id]
        
        def get_val(obj, key):
            if isinstance(obj, dict):
                return obj.get(key)
            return getattr(obj, key, None)

        name = get_val(profile_dict_or_obj, "candidate_name")
        if name:
            parts.append(str(name))

        summary = get_val(profile_dict_or_obj, "professional_summary")
        if summary:
            parts.append(str(summary))

        skills = get_val(profile_dict_or_obj, "technical_skills")
        if skills:
            if isinstance(skills, list):
                parts.extend([str(s) for s in skills if s])
            else:
                parts.append(str(skills))

        exps = get_val(profile_dict_or_obj, "work_experience")
        if exps and isinstance(exps, list):
            for exp in exps:
                t = get_val(exp, "job_title") or get_val(exp, "designation") or ""
                if t:
                    parts.append(str(t))
                comp = get_val(exp, "company") or ""
                if comp:
                    parts.append(str(comp))
                resps = get_val(exp, "responsibilities")
                if resps:
                    if isinstance(resps, list):
                        parts.extend([str(r) for r in resps if r])
                    else:
                        parts.append(str(resps))

        projs = get_val(profile_dict_or_obj, "projects")
        if projs and isinstance(projs, list):
            for proj in projs:
                title = get_val(proj, "title")
                if title:
                    parts.append(str(title))
                desc = get_val(proj, "description")
                if desc:
                    parts.append(str(desc))

        return " ".join(parts)

    def search(
        self,
        job_description: str,
        job_embedding: List[float],
        top_k: int = 10,
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Execute Hybrid Search (BM25 + FAISS Vector) and fuse ranks via RRF.
        """
        all_resumes = self.resume_service.list_resumes()
        if not all_resumes:
            return []

        # 1. Prepare Corpus for BM25
        doc_list = []
        tokenized_corpus = []
        for r in all_resumes:
            resume_id = r["resume_id"]
            prof_raw = r.get("candidate_profile")
            profile_data = None
            if prof_raw:
                try:
                    profile_data = json.loads(prof_raw) if isinstance(prof_raw, str) else prof_raw
                except Exception:
                    profile_data = None
            
            doc_text = self.build_resume_corpus_text(resume_id, profile_data)
            tokens = tokenize_text(doc_text)
            doc_list.append({"resume_id": resume_id, "doc_text": doc_text})
            tokenized_corpus.append(tokens)

        # 2. Run BM25 Keyword Search
        bm25 = BM25Okapi(tokenized_corpus)
        query_tokens = tokenize_text(job_description)
        bm25_scores = bm25.get_scores(query_tokens)

        # Sort documents by BM25 score
        bm25_ranked_indices = sorted(
            range(len(bm25_scores)),
            key=lambda i: bm25_scores[i],
            reverse=True
        )

        bm25_ranks = {}
        for rank, idx in enumerate(bm25_ranked_indices, start=1):
            res_id = doc_list[idx]["resume_id"]
            bm25_ranks[res_id] = {
                "rank": rank,
                "score": float(bm25_scores[idx])
            }

        # 3. Run FAISS Vector Search
        vector_results = self.vector_store.search(embedding=job_embedding, top_k=len(all_resumes))
        vector_ranks = {}
        for rank, v_res in enumerate(vector_results, start=1):
            res_id = v_res["resume_id"]
            vector_ranks[res_id] = {
                "rank": rank,
                "score": float(v_res["score"]),
                "matched_chunk_type": v_res.get("matched_chunk_type", ""),
                "matched_chunk_text": v_res.get("matched_chunk_text", "")
            }

        # 4. Fuse Ranks using Reciprocal Rank Fusion (RRF)
        combined_scores = {}
        for idx, doc in enumerate(doc_list):
            res_id = doc["resume_id"]
            
            b_info = bm25_ranks.get(res_id, {"rank": len(doc_list), "score": 0.0})
            v_info = vector_ranks.get(res_id, {
                "rank": len(doc_list),
                "score": 0.0,
                "matched_chunk_type": "",
                "matched_chunk_text": ""
            })

            # Reciprocal Rank Fusion
            rrf_score = (
                (bm25_weight * (1.0 / (self.rrf_k + b_info["rank"]))) +
                (vector_weight * (1.0 / (self.rrf_k + v_info["rank"])))
            )

            combined_scores[res_id] = {
                "resume_id": res_id,
                "rrf_score": rrf_score,
                "bm25_rank": b_info["rank"],
                "bm25_score": b_info["score"],
                "vector_rank": v_info["rank"],
                "vector_score": v_info["score"],
                "matched_chunk_type": v_info.get("matched_chunk_type", ""),
                "matched_chunk_text": v_info.get("matched_chunk_text", ""),
                # Map vector score to percentage
                "score": v_info["score"]
            }

        # Sort candidates by combined RRF score
        sorted_hybrid = sorted(
            combined_scores.values(),
            key=lambda x: x["rrf_score"],
            reverse=True
        )

        return sorted_hybrid[:top_k]

