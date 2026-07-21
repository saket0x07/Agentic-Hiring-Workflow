from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """
    Generate semantic embeddings for resumes and job descriptions.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model = SentenceTransformer(model_name)

    def build_resume_document(self, profile) -> str:
        """
        Build the semantic text document that will be embedded.
        """
        sections = []

        if getattr(profile, "professional_summary", None):
            sections.append(profile.professional_summary)

        if getattr(profile, "technical_skills", None):
            sections.append("Technical Skills: " + ", ".join(profile.technical_skills))

        if getattr(profile, "work_experience", None):
            for exp in profile.work_experience:
                company = getattr(exp, "company", "") or ""
                designation = getattr(exp, "designation", "") or ""
                if company or designation:
                    sections.append(f"{designation} at {company}".strip())
                responsibilities = getattr(exp, "responsibilities", []) or []
                if isinstance(responsibilities, list):
                    sections.extend(responsibilities)
                elif isinstance(responsibilities, str):
                    sections.append(responsibilities)

        if getattr(profile, "projects", None):
            for project in profile.projects:
                title = getattr(project, "title", None)
                if title:
                    sections.append(title)
                description = getattr(project, "description", None)
                if description:
                    if isinstance(description, list):
                        sections.extend(description)
                    else:
                        sections.append(str(description))

                tech = getattr(project, "technologies", None)
                if tech:
                    if isinstance(tech, list):
                        sections.append(", ".join(tech))
                    elif isinstance(tech, str):
                        sections.append(tech)

        if getattr(profile, "certifications", None):
            for cert in profile.certifications:
                name = getattr(cert, "name", None)
                if name:
                    sections.append(name)

        if getattr(profile, "education", None):
            for edu in profile.education:
                degree = getattr(edu, "degree", "") or ""
                spec = getattr(edu, "specialization", "") or ""
                spec_str = f" in {spec}" if spec else ""
                sections.append(f"{degree}{spec_str}".strip())

        return "\n".join([s for s in sections if s])

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
