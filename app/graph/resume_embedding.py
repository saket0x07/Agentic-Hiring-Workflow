from app.graph.resume_state import ResumeState
from app.services.embedding_service import EmbeddingService


class ResumeEmbeddingNode:
    def __init__(self):
        self.embedding_service = EmbeddingService()

    def __call__(self, state: ResumeState):
        if state.candidate_profile:
            embedding = self.embedding_service.generate_resume_embedding(state.candidate_profile)
            state.embedding = embedding
            state.status = "EMBEDDED"
        return state
