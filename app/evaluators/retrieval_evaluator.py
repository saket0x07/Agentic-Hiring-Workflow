import math
from typing import List, Dict, Any


class RetrievalEvaluator:
    """
    Evaluator for Candidate Retrieval System.
    Computes Precision@K, HitRate@K, and Mean Reciprocal Rank (MRR).
    """

    @staticmethod
    def calculate_precision_at_k(retrieved_ids: List[str], relevant_ids: List[str], k: int = 5) -> float:
        """
        Precision@K = (Number of relevant candidates in top K) / K
        """
        if not retrieved_ids or k <= 0:
            return 0.0
        
        top_k_retrieved = set(retrieved_ids[:k])
        rel_set = set(relevant_ids)
        if not rel_set:
            return 0.0

        hits = len(top_k_retrieved.intersection(rel_set))
        return hits / float(k)

    @staticmethod
    def calculate_hit_rate_at_k(retrieved_ids: List[str], relevant_ids: List[str], k: int = 5) -> float:
        """
        HitRate@K = 1.0 if at least 1 relevant candidate is in top K, else 0.0
        """
        if not retrieved_ids or not relevant_ids or k <= 0:
            return 0.0
        top_k_retrieved = set(retrieved_ids[:k])
        rel_set = set(relevant_ids)
        return 1.0 if len(top_k_retrieved.intersection(rel_set)) > 0 else 0.0

    @staticmethod
    def calculate_reciprocal_rank(retrieved_ids: List[str], relevant_ids: List[str]) -> float:
        """
        Reciprocal Rank (RR) = 1 / (rank of first relevant item)
        """
        if not retrieved_ids or not relevant_ids:
            return 0.0
        
        rel_set = set(relevant_ids)
        for rank, res_id in enumerate(retrieved_ids, start=1):
            if res_id in rel_set:
                return 1.0 / float(rank)
        return 0.0

    @staticmethod
    def evaluate_keyword_relevance(candidate_text: str, expected_keywords: List[str]) -> float:
        """
        Evaluates keyword coverage score (0.0 to 1.0) of a candidate text against expected terms.
        """
        if not candidate_text or not expected_keywords:
            return 0.0
        text_lower = candidate_text.lower()
        matched = [kw for kw in expected_keywords if kw.lower() in text_lower]
        return len(matched) / float(len(expected_keywords))

    def evaluate_retrieval_query(
        self,
        retrieved_candidates: List[Dict[str, Any]],
        expected_keywords: List[str],
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Evaluate a single retrieval query by analyzing candidate match relevancies.
        """
        if not retrieved_candidates:
            return {
                "precision_at_k": 0.0,
                "hit_rate_at_k": 0.0,
                "mrr": 0.0,
                "avg_keyword_coverage": 0.0,
                "evaluated_candidates": 0
            }

        candidate_scores = []
        relevant_indices = []

        def get_val(obj, key):
            if isinstance(obj, dict):
                return obj.get(key)
            return getattr(obj, key, None)

        for idx, cand in enumerate(retrieved_candidates[:k], start=1):
            prof = cand.get("profile") or cand
            summary = str(get_val(prof, "professional_summary") or "")
            
            skills = get_val(prof, "technical_skills") or []
            if isinstance(skills, list):
                skills_str = " ".join([str(s) for s in skills if s])
            else:
                skills_str = str(skills)
            
            raw = str(get_val(prof, "raw_text") or "")
            
            # Extract experience & responsibilities text
            exps = get_val(prof, "work_experience") or []
            exp_text = []
            if isinstance(exps, list):
                for exp in exps:
                    comp = str(get_val(exp, "company") or "")
                    desig = str(get_val(exp, "designation") or get_val(exp, "job_title") or "")
                    resps = get_val(exp, "responsibilities") or []
                    resp_str = " ".join([str(r) for r in resps]) if isinstance(resps, list) else str(resps)
                    exp_text.append(f"{desig} {comp} {resp_str}")
            
            # Extract project titles & descriptions
            projs = get_val(prof, "projects") or []
            proj_text = []
            if isinstance(projs, list):
                for p in projs:
                    title = str(get_val(p, "title") or "")
                    desc = str(get_val(p, "description") or "")
                    tech = get_val(p, "technologies") or []
                    tech_str = " ".join([str(t) for t in tech]) if isinstance(tech, list) else str(tech)
                    proj_text.append(f"{title} {desc} {tech_str}")

            full_text = f"{summary} {skills_str} {raw} {' '.join(exp_text)} {' '.join(proj_text)}"

            coverage = self.evaluate_keyword_relevance(full_text, expected_keywords)
            candidate_scores.append(coverage)
            
            # Consider candidate relevant if keyword coverage >= 15%
            if coverage >= 0.15:
                relevant_indices.append(idx)


        # Precision@K
        precision = len(relevant_indices) / float(k)
        
        # Hit Rate@K
        hit_rate = 1.0 if len(relevant_indices) > 0 else 0.0

        # Reciprocal Rank (RR)
        first_rel_rank = relevant_indices[0] if relevant_indices else 0
        rr = (1.0 / first_rel_rank) if first_rel_rank > 0 else 0.0

        avg_coverage = sum(candidate_scores) / float(len(candidate_scores)) if candidate_scores else 0.0

        return {
            "precision_at_k": round(precision, 4),
            "hit_rate_at_k": round(hit_rate, 4),
            "mrr": round(rr, 4),
            "avg_keyword_coverage": round(avg_coverage * 100, 2),
            "evaluated_candidates": len(retrieved_candidates[:k])
        }
