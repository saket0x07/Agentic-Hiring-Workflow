from app.graph.resume_state import ResumeState
from app.services.vector_store import VectorStore


class ResumeIndexerNode:
    def __init__(self):
        self.vector_store = VectorStore()

    def __call__(self, state: ResumeState):
        if state.embedding:
            self.vector_store.add_resume(resume_id=state.resume_id, embedding=state.embedding)
            state.status = "INDEXED"
        return state