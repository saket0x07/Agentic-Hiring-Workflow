from typing import List, Union, Dict, Any
from pydantic import BaseModel, Field, AliasChoices

class JobDescription(BaseModel):
    job_title: str = Field(validation_alias=AliasChoices("job_title", "title"))
    summary: str
    responsibilities: List[str]
    must_have_skills: List[str]
    nice_to_have_skills: List[str]
    experience: str
    education: str
    interview_rounds: List[Union[str, Dict[str, Any]]]