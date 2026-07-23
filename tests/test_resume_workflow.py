import asyncio
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.graph.resume_state import ResumeState
from app.graph.resume_workflow import resume_workflow


@pytest.mark.asyncio
async def test_resume_workflow_execution():
    resume_path = Path("data/resumes/Saket-Resume.pdf")
    assert resume_path.exists()

    initial_state = ResumeState(
        resume_id="TEST-WORKFLOW-001",
        file_path=resume_path,
    )

    final_state = await resume_workflow.ainvoke(initial_state)

    assert final_state["status"] == "INDEXED"
    assert final_state["raw_text"] is not None
    assert final_state["candidate_profile"] is not None
    assert final_state["embedding"] is not None
    assert len(final_state["embedding"]) == 768


if __name__ == "__main__":
    asyncio.run(test_resume_workflow_execution())
