from app.graph.resume_state import ResumeState
from app.services.embedding_service import EmbeddingService


class ResumeEmbeddingNode:
    def __init__(self):
        self.embedding_service = EmbeddingService()

    def __call__(self, state: ResumeState):
        if state.candidate_profile:
            chunk_embeddings = self.embedding_service.generate_resume_chunk_embeddings(state.candidate_profile)
            state.chunk_embeddings = chunk_embeddings
            state.embedding = chunk_embeddings[0]["embedding"] if chunk_embeddings else self.embedding_service.generate_resume_embedding(state.candidate_profile)
            state.status = "EMBEDDED"
        return state

