
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import EmploymentType,WorkMode

class HiringRequest(BaseModel):
    """ RECURITER INOUT FOR JD GENERATIONS """
    role: str = Field(...,description="Job Title")
    department: str
    experience: str
    location: str
    employment_type: EmploymentType
    work_mode: WorkMode
    budget: Optional[str] = None
    required_skills:List[str]
    preferred_skills: List[str]=[]
    notes: Optional[str]= None
    
    