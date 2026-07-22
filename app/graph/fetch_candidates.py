from app.graph.retrieval_state import RetrievalState
from app.services.resume_service import ResumeService

class FetchCandidatesNodes:
    def __init__(self):
        self.resume_service=ResumeService()

    def __call__(self,state:RetrievalState):
        profiles = []
        for candidate in state.retrieved_candidates:
            resume_id = candidate.get("resume_id") or candidate.get("id")
            if resume_id:
                profile = self.resume_service._get_resume_by_id(resume_id)
                if profile:
                    profiles.append({
                        "resume_id": resume_id,
                        "similarity_score": candidate.get("score", 0.0),
                        "profile": profile
                    })
        
        state.candidate_profiles = profiles
        state.status = "PROFILE_FETCHED"
        return state       
        