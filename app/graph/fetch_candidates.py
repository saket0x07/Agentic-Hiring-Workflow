from app.graph.retrieval_state import RetrievalState
from app.services.resume_service import ResumeService

class FetchCandidatesNodes:
    def __init__(self):
        self.resume_service = ResumeService()

    def __call__(self, state: RetrievalState):
        profiles = []
        for candidate in state.retrieved_candidates:
            resume_id = candidate.get("resume_id") or candidate.get("id")
            if resume_id:
                profile = self.resume_service._get_resume_by_id(resume_id)
                if profile:
                    profiles.append({
                        "resume_id": resume_id,
                        "similarity_score": candidate.get("score", 0.0),
                        "rrf_score": candidate.get("rrf_score", 0.0),
                        "bm25_score": candidate.get("bm25_score", 0.0),
                        "bm25_rank": candidate.get("bm25_rank", 0),
                        "vector_rank": candidate.get("vector_rank", 0),
                        "matched_chunk_type": candidate.get("matched_chunk_type", ""),
                        "matched_chunk_text": candidate.get("matched_chunk_text", ""),
                        "profile": profile
                    })

        
        state.candidate_profiles = profiles
        state.status = "PROFILE_FETCHED"
        return state