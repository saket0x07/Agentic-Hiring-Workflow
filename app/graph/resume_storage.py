from app.graph.resume_state import ResumeState
from app.services.resume_service import ResumeService


class ResumeStorageNode:
    def __init__(self):
        self.service = ResumeService()

    def __call__(self, state: ResumeState):
        if state.candidate_profile:
            self.service.save_resume(
                resume_id=state.resume_id,
                profile=state.candidate_profile,
                file_path=str(state.file_path),
            )
            state.status = "STORED"
        return state
