from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class ContactInfo(BaseModel):
    email: Optional[str] = None
    phone: Optional[Union[str, int]] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None


class Education(BaseModel):
    degree: Optional[Union[str, List[str]]] = None
    institute: Optional[Union[str, List[str]]] = None
    specialization: Optional[Union[str, List[str]]] = None
    start_year: Optional[Union[str, int]] = None
    end_year: Optional[Union[str, int]] = None
    gpa: Optional[Union[str, int, float]] = None

    @field_validator("degree", "institute", "specialization", mode="before")
    @classmethod
    def join_list_to_str(cls, v):
        if isinstance(v, list):
            return " ".join(str(x) for x in v)
        return v


class WorkExperience(BaseModel):
    company: Optional[Union[str, List[str]]] = None
    designation: Optional[Union[str, List[str]]] = None
    start_date: Optional[Union[str, int]] = None
    end_date: Optional[Union[str, int]] = None
    duration: Optional[Union[str, int, float]] = None
    responsibilities: List[str] = Field(default_factory=list)

    @field_validator("company", "designation", mode="before")
    @classmethod
    def join_list_to_str(cls, v):
        if isinstance(v, list):
            return " ".join(str(x) for x in v)
        return v

    @field_validator("responsibilities", mode="before")
    @classmethod
    def ensure_list(cls, v):
        if isinstance(v, str):
            return [v]
        return v or []


class Project(BaseModel):
    title: Optional[Union[str, List[str]]] = None
    description: Optional[Union[str, List[str]]] = None
    technologies: List[str] = Field(default_factory=list)

    @field_validator("title", "description", mode="before")
    @classmethod
    def join_list_to_str(cls, v):
        if isinstance(v, list):
            return "\n".join(str(x) for x in v)
        return v

    @field_validator("technologies", mode="before")
    @classmethod
    def ensure_tech_list(cls, v):
        if isinstance(v, str):
            return [v]
        return v or []


class Certification(BaseModel):
    name: Optional[Union[str, List[str]]] = None
    issuer: Optional[Union[str, List[str]]] = None
    year: Optional[Union[str, int]] = None

    @field_validator("name", "issuer", mode="before")
    @classmethod
    def join_list_to_str(cls, v):
        if isinstance(v, list):
            return " ".join(str(x) for x in v)
        return v


class CandidateProfile(BaseModel):
    candidate_name: Optional[Union[str, List[str]]] = None
    contact: Optional[ContactInfo] = None
    professional_summary: Optional[Union[str, List[str]]] = None
    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    work_experience: List[WorkExperience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    achievements: List[Union[str, dict]] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    total_experience: Optional[Union[str, int, float]] = None
    raw_text: Optional[str] = None

    @field_validator("candidate_name", "professional_summary", mode="before")
    @classmethod
    def join_list_to_str(cls, v):
        if isinstance(v, list):
            return " ".join(str(x) for x in v)
        return v

    @field_validator("education", mode="before")
    @classmethod
    def convert_education(cls, v):
        if isinstance(v, list):
            res = []
            for item in v:
                if isinstance(item, str):
                    res.append({"degree": item})
                elif isinstance(item, dict):
                    res.append(item)
            return res
        return v

    @field_validator("work_experience", mode="before")
    @classmethod
    def convert_work_experience(cls, v):
        if isinstance(v, list):
            res = []
            for item in v:
                if isinstance(item, str):
                    res.append({"company": item})
                elif isinstance(item, dict):
                    res.append(item)
            return res
        return v

    @field_validator("projects", mode="before")
    @classmethod
    def convert_projects(cls, v):
        if isinstance(v, list):
            res = []
            for item in v:
                if isinstance(item, str):
                    res.append({"title": item})
                elif isinstance(item, dict):
                    res.append(item)
            return res
        return v

    @field_validator("certifications", mode="before")
    @classmethod
    def convert_certifications(cls, v):
        if isinstance(v, list):
            res = []
            for item in v:
                if isinstance(item, str):
                    res.append({"name": item})
                elif isinstance(item, dict):
                    res.append(item)
            return res
        return v
