
from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_validator, AliasChoices
from app.schemas.common import EmploymentType, WorkMode

class HiringRequest(BaseModel):
    """ RECRUITER INPUT FOR JD GENERATION """
    role: str = Field(..., validation_alias=AliasChoices("role", "job_title", "title", "position"), description="Job Title")
    department: str = Field(default="Engineering")
    experience: str = Field(default="1-3 years")
    location: str = Field(default="Remote")
    employment_type: EmploymentType = Field(default=EmploymentType.FULL_TIME)
    work_mode: WorkMode = Field(default=WorkMode.REMOTE)
    budget: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

    @field_validator("experience", mode="before")
    @classmethod
    def validate_experience(cls, v: Any) -> str:
        if isinstance(v, (int, float)):
            return f"{v} years"
        if not v:
            return "1-3 years"
        return str(v)

    @field_validator("employment_type", mode="before")
    @classmethod
    def validate_employment_type(cls, v: Any) -> EmploymentType:
        if isinstance(v, EmploymentType):
            return v
        if not v:
            return EmploymentType.FULL_TIME
        val_str = str(v).lower().strip().replace("-", "_").replace(" ", "_")
        for emp_type in EmploymentType:
            if emp_type.value == val_str or emp_type.name.lower() == val_str:
                return emp_type
        return EmploymentType.FULL_TIME

    @field_validator("work_mode", mode="before")
    @classmethod
    def validate_work_mode(cls, v: Any) -> WorkMode:
        if isinstance(v, WorkMode):
            return v
        if not v:
            return WorkMode.REMOTE
        val_str = str(v).lower().strip().replace("-", "_").replace(" ", "_")
        for mode in WorkMode:
            if mode.value == val_str or mode.name.lower() == val_str:
                return mode
        return WorkMode.REMOTE

    @field_validator("required_skills", "preferred_skills", mode="before")
    @classmethod
    def validate_skills_list(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        if isinstance(v, list):
            return [str(item).strip() for item in v if item]
        return []
    
    