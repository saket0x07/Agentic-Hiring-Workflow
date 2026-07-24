from sentence_transformers import CrossEncoder

class RerankerService:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-12-v2"):
        self.model = CrossEncoder(model_name)

    def rerank(self, job_description: str, candidates: list):
        if not candidates:
            return []
        
        pairs = []
        for candidate in candidates:
            resume_text = self._build_resume_text(candidate)
            pairs.append((job_description, resume_text))

        scores = self.model.predict(pairs)

        for candidate, score in zip(candidates, scores):
            candidate["rerank_score"] = float(score)

        # Sort primarily by Cross-Encoder rerank score, with Hybrid RRF as secondary ranker
        candidates.sort(
            key=lambda x: (x.get("rerank_score", 0.0), x.get("rrf_score", 0.0)),
            reverse=True
        )
        return candidates

    def _build_resume_text(self, candidate_item):
        if not candidate_item:
            return ""
        
        # Support candidate passing as dict with 'profile' or directly as profile dict
        profile = candidate_item.get("profile") if isinstance(candidate_item, dict) else candidate_item
        matched_chunk_text = candidate_item.get("matched_chunk_text") if isinstance(candidate_item, dict) else None
        matched_chunk_type = candidate_item.get("matched_chunk_type") if isinstance(candidate_item, dict) else None

        sections = []

        def get_val(obj, key):
            if isinstance(obj, dict):
                return obj.get(key)
            return getattr(obj, key, None)

        # 1. Add Candidate Summary / Name
        summary = get_val(profile, "professional_summary")
        if summary:
            sections.append(f"Summary: {summary}")
        else:
            raw = get_val(profile, "raw_text")
            if raw:
                sections.append(str(raw)[:500])

        # 2. Add Technical Skills
        skills = get_val(profile, "technical_skills")
        if skills:
            if isinstance(skills, list):
                sections.append("Technical Skills: " + ", ".join([str(s) for s in skills if s]))
            else:
                sections.append("Technical Skills: " + str(skills))

        # 3. Add Top Matching Section Chunk (Chunk-Aware Reranking Context)
        if matched_chunk_text:
            chunk_type_label = str(matched_chunk_type).replace("_", " ").title() if matched_chunk_type else "Top Section"
            sections.append(f"Top Matching Candidate Section ({chunk_type_label}):\n{matched_chunk_text}")

        # 4. Add Key Experience Titles
        exps = get_val(profile, "work_experience")
        if exps and isinstance(exps, list):
            for exp in exps:
                title = get_val(exp, "job_title") or get_val(exp, "designation") or ""
                company = get_val(exp, "company") or ""
                if title or company:
                    sections.append(f"Role: {title} at {company}".strip())
                resps = get_val(exp, "responsibilities")
                if resps:
                    if isinstance(resps, list):
                        sections.extend([str(r) for r in resps[:2] if r])
                    else:
                        sections.append(str(resps)[:200])

        if not sections:
            raw = get_val(profile, "raw_text")
            if raw:
                sections.append(str(raw)[:1000])

        return "\n\n".join([s for s in sections if s])