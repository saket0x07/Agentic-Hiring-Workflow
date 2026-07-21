from time import strftime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from app.schemas.candidate_profile import CandidateProfile

class ResumeState(BaseModel):
    """
    state shared across resume ingestion Workflow.
    """

    resume_id: str
    file_path: Path
    raw_text: Optional[str] = None
    candidate_profile: Optional[CandidateProfile] = None
    status: str = "UPLOADED"
    error: Optional[str]=None
    embedding: Optional[list[float]]=None

