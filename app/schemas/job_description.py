from typing import Any, Dict, List, Union
from pydantic import AliasChoices, BaseModel, Field


class JobDescription(BaseModel):
    job_title: str = Field(validation_alias=AliasChoices("job_title", "title", "role"))
    summary: str = Field(default="", validation_alias=AliasChoices("summary", "description", "overview"))
    responsibilities: List[str] = Field(default_factory=list, validation_alias=AliasChoices("responsibilities", "key_responsibilities", "duties"))
    must_have_skills: List[str] = Field(default_factory=list, validation_alias=AliasChoices("must_have_skills", "required_skills", "skills"))
    nice_to_have_skills: List[str] = Field(default_factory=list, validation_alias=AliasChoices("nice_to_have_skills", "preferred_skills"))
    experience: str = Field(default="Not specified", validation_alias=AliasChoices("experience", "required_experience", "years_of_experience"))
    education: str = Field(default="Not specified", validation_alias=AliasChoices("education", "qualification", "education_requirements"))
    interview_rounds: List[Union[str, Dict[str, Any]]] = Field(default_factory=list, validation_alias=AliasChoices("interview_rounds", "interview_process", "rounds"))