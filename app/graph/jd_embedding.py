from app.graph.retrieval_state import RetrievalState
from app.services.embedding_service import EmbeddingService

class JDEmbeddingNode:

    def __init__(self):
        self.embedding_service = EmbeddingService()

    def __call__(self, state: RetrievalState):
        embedding = self.embedding_service.generate_embedding(state.job_description)
        state.job_embedding = embedding
        state.status = "JD_EMBEDDED"
    
        return state
        