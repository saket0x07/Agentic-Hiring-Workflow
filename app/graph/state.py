from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

class HiringState(TypedDict):
    """Shared state of the hiring workflow.
    Every LangGraph node reads from and updates this state."""
    job_id: str
    workflow_stage: str
    status: str

    hiring_request: Dict[str, Any]
    generated_jd: Optional[Dict[str, Any]]
    pdf_path: Optional[str]

    approved: bool
    feedback: Optional[str]

    messages: List[str]
    errors: List[str]