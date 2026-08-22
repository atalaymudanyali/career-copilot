from pydantic import BaseModel


class ContactInfo(BaseModel):
    email: str
    github: str = ""
    linkedin: str = ""


class Education(BaseModel):
    degree: str
    school: str
    dates: str
    gpa: str = ""


class Skills(BaseModel):
    languages: list[str] = []
    frameworks: list[str] = []
    ai_ml: list[str] = []
    databases: list[str] = []
    tools: list[str] = []


class Experience(BaseModel):
    id: str
    role: str
    company: str
    dates: str
    bullets: list[str]


class CV(BaseModel):
    name: str
    contact: ContactInfo
    education: list[Education] = []
    skills: Skills = Skills()
    experience: list[Experience] = []
    projects: list[str] = []


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
