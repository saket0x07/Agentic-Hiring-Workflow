from app.graph.retrieval_state import RetrievalState
from app.services.vector_store import VectorStore

class ResumeSearchNode:

    def __init__(self):
        self.vector_store = VectorStore()

    def __call__(self, state: RetrievalState):
        candidates=self.vector_store.search(embedding=state.job_embedding, top_k=state.top_k)
        state.retrieved_candidates = candidates
        state.status = "RETRIEVED"
        
        return state
        