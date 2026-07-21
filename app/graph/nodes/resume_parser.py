from app.graph.resume_state import ResumeState
from app.agents.resume_parser import ResumeParserAgent


class ResumeParserNode:
    def __init__(self):
        self.agent = ResumeParserAgent()

    async def __call__(self, state: ResumeState):
        profile = await self.agent.parse(state.raw_text)
        state.candidate_profile = profile
        state.status = "PARSED"
        return state
