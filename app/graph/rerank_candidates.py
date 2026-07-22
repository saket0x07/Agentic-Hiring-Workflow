from app.graph.retrieval_state import RetrievalState
from app.services.reranker_service import RerankerService


class RerankCandidatesNodes:

    def __init__(self):
        self.reranker_service = RerankerService()

    def __call__(self, state: RetrievalState):
        reranked = self.reranker_service.rerank(state.job_description, state.candidate_profiles)

        state.candidate_profiles = reranked
        state.status = "RERANKED"

        return state