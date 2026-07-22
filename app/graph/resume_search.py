from app.graph.retrieval_state import RetrievalState
from app.services.hybrid_search import HybridSearchService


class ResumeSearchNode:
    """
    Graph node for Hybrid Search combining BM25 Keyword Search & FAISS Vector Search.
    """

    def __init__(self):
        self.hybrid_search_service = HybridSearchService()

    def __call__(self, state: RetrievalState):
        candidates = self.hybrid_search_service.search(
            job_description=state.job_description,
            job_embedding=state.job_embedding,
            top_k=state.top_k
        )
        state.retrieved_candidates = candidates
        state.status = "RETRIEVED_HYBRID"
        
        return state