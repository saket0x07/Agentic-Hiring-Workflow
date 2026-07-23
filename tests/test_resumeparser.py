import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from app.agents.resume_parser import ResumeParserAgent
from app.services.resume_extractor import ResumeExtractor


@pytest.mark.asyncio
async def test_resume_parser():
    raw_text = ResumeExtractor.extract_text("data/resumes/Saket-Resume.pdf")
    agent = ResumeParserAgent()
    profile = await agent.parse(raw_text)

    print(profile.model_dump_json(indent=4))
    assert profile.candidate_name is not None


if __name__ == "__main__":
    asyncio.run(test_resume_parser())