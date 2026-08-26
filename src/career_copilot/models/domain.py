from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class ContactInfo(BaseModel):
    email: str
    github: str = ""
    linkedin: str = ""


class Education(BaseModel):
    degree: str
    school: str
    dates: str
    location: str = ""
    gpa: str = ""
    highlights: list[str] = []


class SpokenLanguage(BaseModel):
    language: str
    level: str


class Skills(BaseModel):
    languages: list[str] = []
    frameworks: list[str] = []
    ai_ml: list[str] = []
    databases: list[str] = []
    security: list[str] = []
    tools: list[str] = []


class Experience(BaseModel):
    id: str
    role: str
    company: str
    dates: str
    location: str = ""
    context: str = ""
    bullets: list[str]


class CV(BaseModel):
    name: str
    contact: ContactInfo
    summary: str = ""
    education: list[Education] = []
    skills: Skills = Skills()
    experience: list[Experience] = []
    projects: list[str] = []
    languages_spoken: list[SpokenLanguage] = []


class Project(BaseModel):
    id: str
    title: str
    tech: list[str] = []
    date: str = ""
    description: str = ""


class SourceChunk(BaseModel):
    """A single piece of CV/project data that can be referenced by the LLM."""

    source_id: str
    source_type: str
    content: str


class TailoredBullet(BaseModel):
    text: str
    source_id: str
    relevance: str = "medium"


class TailoringResult(BaseModel):
    tailored_bullets: list[TailoredBullet]
    why_i_fit: str
    gaps: list[str] = []


class ApplicationStatus(StrEnum):
    SAVED = "saved"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFERED = "offered"
    REJECTED = "rejected"


class ApplicationCreate(BaseModel):
    company: str
    role: str
    jd_text: str
    url: str | None = None
    notes: str | None = None


class ApplicationUpdate(BaseModel):
    company: str | None = None
    role: str | None = None
    status: ApplicationStatus | None = None
    jd_text: str | None = None
    url: str | None = None
    notes: str | None = None


class TailoringVersionResponse(BaseModel):
    id: int
    application_id: int
    version_number: int
    tailoring_result: TailoringResult
    created_at: datetime


class ApplicationResponse(BaseModel):
    id: int
    company: str
    role: str
    status: str
    jd_text: str
    url: str | None
    notes: str | None
    tailoring_result: TailoringResult | None = None
    applied_at: datetime | None
    created_at: datetime
    updated_at: datetime
