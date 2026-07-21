from app.graph.resume_state import ResumeState
from app.services.resume_extractor import ResumeExtractor

class ResumeExtractorNode:
    def __call__(self, state: ResumeState):
        raw_text = ResumeExtractor.extract_text(state.file_path)
        state.raw_text = raw_text
        state.status = "TEXT_EXTRACTED"

        return state