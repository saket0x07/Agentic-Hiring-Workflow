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

    def get_parsed_experience_years(self) -> float:
        """Extract numeric total years of experience from profile."""
        if self.total_experience is not None:
            try:
                import re
                if isinstance(self.total_experience, (int, float)):
                    return float(self.total_experience)
                matches = re.findall(r"[-+]?\d*\.\d+|\d+", str(self.total_experience))
                if matches:
                    return float(matches[0])
            except Exception:
                pass
        
        # Fallback: estimate from work_experience count
        if self.work_experience:
            return float(len(self.work_experience) * 1.5)
        return 0.0

    def get_education_tier(self) -> int:
        """
        Determine highest education tier:
        0: None/Unknown
        1: Diploma / High School
        2: Bachelor's
        3: Master's
        4: Doctorate / PhD
        """
        if not self.education:
            return 0

        max_tier = 0
        phd_keywords = ["phd", "doctor", "doctorate", "ph.d"]
        master_keywords = ["master", "m.tech", "mtech", "ms", "ma", "m.e", "me", "m.sc", "msc", "mba", "postgraduate", "pg"]
        bachelor_keywords = ["bachelor", "b.tech", "btech", "bs", "ba", "b.e", "be", "b.sc", "bsc", "undergraduate", "degree", "b.a", "b.s"]

        for edu in self.education:
            degree_str = ""
            if isinstance(edu, Education):
                degree_str = str(edu.degree or "").lower() + " " + str(edu.specialization or "").lower()
            elif isinstance(edu, dict):
                degree_str = str(edu.get("degree", "")).lower() + " " + str(edu.get("specialization", "")).lower()
            
            if any(k in degree_str for k in phd_keywords):
                max_tier = max(max_tier, 4)
            elif any(k in degree_str for k in master_keywords):
                max_tier = max(max_tier, 3)
            elif any(k in degree_str for k in bachelor_keywords):
                max_tier = max(max_tier, 2)
            elif degree_str.strip():
                max_tier = max(max_tier, 1)

        return max_tier

