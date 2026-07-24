from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """
    Generate semantic embeddings for resumes and job descriptions.
    """

    def __init__(self, model_name: str = "BAAI/bge-base-en-v1.5"):
        self.model = SentenceTransformer(model_name)

    def build_resume_document(self, profile) -> str:
        """
        Build the semantic text document that will be embedded.
        Supports both dict and CandidateProfile object instances.
        """
        if not profile:
            return ""

        def get_val(obj, key):
            if isinstance(obj, dict):
                return obj.get(key)
            return getattr(obj, key, None)

        sections = []

        name = get_val(profile, "candidate_name")
        if name:
            sections.append(f"Candidate Name: {name}")

        summary = get_val(profile, "professional_summary")
        if summary:
            sections.append(str(summary))

        skills = get_val(profile, "technical_skills")
        if skills:
            if isinstance(skills, list):
                sections.append("Technical Skills: " + ", ".join([str(s) for s in skills if s]))
            elif isinstance(skills, str):
                sections.append("Technical Skills: " + skills)

        soft_skills = get_val(profile, "soft_skills")
        if soft_skills:
            if isinstance(soft_skills, list):
                sections.append("Soft Skills: " + ", ".join([str(s) for s in soft_skills if s]))
            elif isinstance(soft_skills, str):
                sections.append("Soft Skills: " + soft_skills)

        exps = get_val(profile, "work_experience")
        if exps and isinstance(exps, list):
            for exp in exps:
                company = get_val(exp, "company") or ""
                designation = get_val(exp, "designation") or get_val(exp, "job_title") or ""
                if company or designation:
                    sections.append(f"{designation} at {company}".strip())
                responsibilities = get_val(exp, "responsibilities") or []
                if isinstance(responsibilities, list):
                    sections.extend([str(r) for r in responsibilities if r])
                elif isinstance(responsibilities, str):
                    sections.append(responsibilities)

        projs = get_val(profile, "projects")
        if projs and isinstance(projs, list):
            for project in projs:
                title = get_val(project, "title")
                if title:
                    sections.append(str(title))
                description = get_val(project, "description")
                if description:
                    if isinstance(description, list):
                        sections.extend([str(d) for d in description if d])
                    else:
                        sections.append(str(description))

                tech = get_val(project, "technologies")
                if tech:
                    if isinstance(tech, list):
                        sections.append(", ".join([str(t) for t in tech if t]))
                    elif isinstance(tech, str):
                        sections.append(tech)

        certs = get_val(profile, "certifications")
        if certs and isinstance(certs, list):
            for cert in certs:
                cname = get_val(cert, "name") or get_val(cert, "title")
                if cname:
                    sections.append(str(cname))

        edus = get_val(profile, "education")
        if edus and isinstance(edus, list):
            for edu in edus:
                degree = get_val(edu, "degree") or ""
                spec = get_val(edu, "specialization") or ""
                spec_str = f" in {spec}" if spec else ""
                sections.append(f"{degree}{spec_str}".strip())

        raw = get_val(profile, "raw_text")
        if raw:
            sections.append(f"Full Text: {raw}")

        return "\n".join([s for s in sections if s])

    def build_resume_chunks(self, profile) -> list[dict]:
        """
        Build separate logical section chunks for a candidate profile.
        Returns a list of dicts: [{"chunk_type": str, "text": str}]
        """
        if not profile:
            return []

        def get_val(obj, key):
            if isinstance(obj, dict):
                return obj.get(key)
            return getattr(obj, key, None)

        chunks = []

        # Candidate Name & Summary Chunk
        summary_parts = []
        name = get_val(profile, "candidate_name")
        if name:
            summary_parts.append(f"Candidate Name: {name}")
        summary = get_val(profile, "professional_summary")
        if summary:
            summary_parts.append(f"Summary: {summary}")
        if summary_parts:
            chunks.append({"chunk_type": "summary", "text": "\n".join(summary_parts)})

        # Skills Chunk
        skills_parts = []
        skills = get_val(profile, "technical_skills")
        if skills:
            if isinstance(skills, list):
                skills_parts.append("Technical Skills: " + ", ".join([str(s) for s in skills if s]))
            elif isinstance(skills, str):
                skills_parts.append("Technical Skills: " + skills)
        soft_skills = get_val(profile, "soft_skills")
        if soft_skills:
            if isinstance(soft_skills, list):
                skills_parts.append("Soft Skills: " + ", ".join([str(s) for s in soft_skills if s]))
            elif isinstance(soft_skills, str):
                skills_parts.append("Soft Skills: " + soft_skills)
        if skills_parts:
            chunks.append({"chunk_type": "skills", "text": "\n".join(skills_parts)})

        # Work Experience Chunks (1 chunk per experience)
        exps = get_val(profile, "work_experience")
        if exps and isinstance(exps, list):
            for i, exp in enumerate(exps, 1):
                exp_parts = []
                company = get_val(exp, "company") or ""
                designation = get_val(exp, "designation") or get_val(exp, "job_title") or ""
                if company or designation:
                    exp_parts.append(f"Role: {designation} at {company}".strip())
                responsibilities = get_val(exp, "responsibilities") or []
                if isinstance(responsibilities, list):
                    exp_parts.extend([str(r) for r in responsibilities if r])
                elif isinstance(responsibilities, str):
                    exp_parts.append(responsibilities)
                if exp_parts:
                    chunks.append({"chunk_type": f"experience_{i}", "text": "\n".join(exp_parts)})

        # Projects Chunks (1 chunk per project)
        projs = get_val(profile, "projects")
        if projs and isinstance(projs, list):
            for i, project in enumerate(projs, 1):
                proj_parts = []
                title = get_val(project, "title")
                if title:
                    proj_parts.append(f"Project Title: {title}")
                description = get_val(project, "description")
                if description:
                    if isinstance(description, list):
                        proj_parts.extend([str(d) for d in description if d])
                    else:
                        proj_parts.append(str(description))
                tech = get_val(project, "technologies")
                if tech:
                    if isinstance(tech, list):
                        proj_parts.append("Technologies: " + ", ".join([str(t) for t in tech if t]))
                    elif isinstance(tech, str):
                        proj_parts.append("Technologies: " + tech)
                if proj_parts:
                    chunks.append({"chunk_type": f"project_{i}", "text": "\n".join(proj_parts)})

        # Education Chunk
        edus = get_val(profile, "education")
        if edus and isinstance(edus, list):
            edu_parts = []
            for edu in edus:
                degree = get_val(edu, "degree") or ""
                spec = get_val(edu, "specialization") or ""
                institute = get_val(edu, "institute") or ""
                spec_str = f" in {spec}" if spec else ""
                inst_str = f" from {institute}" if institute else ""
                edu_parts.append(f"Education: {degree}{spec_str}{inst_str}".strip())
            if edu_parts:
                chunks.append({"chunk_type": "education", "text": "\n".join(edu_parts)})

        # Certifications Chunk
        certs = get_val(profile, "certifications")
        if certs and isinstance(certs, list):
            cert_parts = []
            for cert in certs:
                cname = get_val(cert, "name") or get_val(cert, "title")
                issuer = get_val(cert, "issuer") or ""
                issuer_str = f" (by {issuer})" if issuer else ""
                if cname:
                    cert_parts.append(f"Certification: {cname}{issuer_str}")
            if cert_parts:
                chunks.append({"chunk_type": "certifications", "text": "\n".join(cert_parts)})

        # Fallback to full document if no structured chunks were extracted
        if not chunks:
            doc = self.build_resume_document(profile)
            if doc:
                chunks.append({"chunk_type": "full_document", "text": doc})

        return chunks

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding vector from raw text.
        """
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def generate_resume_embedding(self, profile) -> list[float]:
        """
        Generate embedding directly from CandidateProfile.
        """
        document = self.build_resume_document(profile)
        return self.generate_embedding(document)

    def generate_resume_chunk_embeddings(self, profile) -> list[dict]:
        """
        Generate embeddings for each section chunk in CandidateProfile.
        Returns list of dicts: [{"chunk_type": str, "text": str, "embedding": list[float]}]
        """
        chunks = self.build_resume_chunks(profile)
        result = []
        for chunk in chunks:
            emb = self.generate_embedding(chunk["text"])
            result.append({
                "chunk_type": chunk["chunk_type"],
                "text": chunk["text"],
                "embedding": emb
            })
        return result

