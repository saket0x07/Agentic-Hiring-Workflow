import json
import logging
from app.graph.retrieval_state import RetrievalState
from app.evaluators.match_justifier import MatchJustifierService

logger = logging.getLogger("explain_candidates")


class ExplainCandidatesNode:
    """
    LangGraph Node that enriches retrieved and reranked candidates with
    Match Justification Rationale and Skill Gap Analysis.
    """

    def __init__(self):
        self.match_justifier = MatchJustifierService()

    def __call__(self, state: RetrievalState):
        if not state.candidate_profiles:
            return state

        jd_data = {}
        try:
            if isinstance(state.job_description, str):
                jd_data = json.loads(state.job_description)
            elif isinstance(state.job_description, dict):
                jd_data = state.job_description
        except Exception:
            jd_data = {"job_title": "Job Position", "description": str(state.job_description)}

        for candidate in state.candidate_profiles:
            justification = self.match_justifier.generate_justification(candidate, jd_data)
            candidate["match_justification"] = justification

        state.status = "EXPLAINED"
        return state
