from sentence_transformers import CrossEncoder

class RerankerService:
    def __init__(self):
        self.model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    def rerank(self, job_description: str, candidates: list):
        if not candidates:
            return []
        
        pairs = []
        for candidate in candidates:
            profile = candidate.get("profile")
            resume_text = self._build_resume_text(profile)
            pairs.append((job_description, resume_text))

        scores = self.model.predict(pairs)

        for candidate, score in zip(candidates, scores):
            candidate["rerank_score"] = float(score)

        # Sort primarily by Hybrid RRF rank score (BM25 + FAISS), using Cross-Encoder score as secondary ranker
        candidates.sort(
            key=lambda x: (x.get("rrf_score", 0.0), x.get("rerank_score", 0.0)),
            reverse=True
        )
        return candidates

    def _build_resume_text(self, profile):
        if not profile:
            return ""
        
        sections = []

        # Get fields safely whether profile is dict or Pydantic model
        def get_val(obj, key):
            if isinstance(obj, dict):
                return obj.get(key)
            return getattr(obj, key, None)

        summary = get_val(profile, "professional_summary")
        if summary:
            sections.append(str(summary))
        else:
            raw = get_val(profile, "raw_text")
            if raw:
                sections.append(str(raw)[:600])

        skills = get_val(profile, "technical_skills")
        if skills:
            if isinstance(skills, list):
                sections.append("Technical Skills: " + ", ".join([str(s) for s in skills if s]))
            else:
                sections.append("Technical Skills: " + str(skills))

        projects = get_val(profile, "projects")
        if projects and isinstance(projects, list):
            for proj in projects:
                title = get_val(proj, "title")
                if title:
                    sections.append(str(title))

        exps = get_val(profile, "work_experience")
        if exps and isinstance(exps, list):
            for exp in exps:
                title = get_val(exp, "job_title") or get_val(exp, "designation") or ""
                company = get_val(exp, "company") or ""
                if title or company:
                    sections.append(f"{title} at {company}".strip())
                resps = get_val(exp, "responsibilities")
                if resps:
                    if isinstance(resps, list):
                        sections.extend([str(r) for r in resps if r])
                    else:
                        sections.append(str(resps))

        if not sections:
            raw = get_val(profile, "raw_text")
            if raw:
                sections.append(str(raw)[:1000])

        return "\n".join([s for s in sections if s])