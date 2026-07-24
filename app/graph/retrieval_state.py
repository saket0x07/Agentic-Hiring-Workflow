from typing import Optional

from pydantic import BaseModel
from app.schemas.candidate_profile import CandidateProfile

class RetrievalState(BaseModel):
    """
    Shared state for Retrieval & Ranking Graph.
    """
    job_id: str
    job_description: str
    job_embedding: Optional[list[float]]=None
    retrieved_candidates: list[dict]=[]    
    candidate_profiles: list[dict]=[]
    top_k: int = 5
    filters: Optional[dict] = None
    status: str="START"
    error: Optional[str]=None


