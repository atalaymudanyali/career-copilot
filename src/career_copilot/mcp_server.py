import json

import httpx
from mcp.server.mcpserver import MCPServer

from career_copilot.prompts.templates import (
    SKILL_GAP_SYSTEM_PROMPT,
    build_skill_gap_prompt,
)
from career_copilot.services.data_loader import build_source_chunks, load_cv, load_projects
from career_copilot.services.llm import OllamaClient
from career_copilot.services.tailoring import tailor

mcp = MCPServer("Career Copilot")

OLLAMA_UNAVAILABLE = (
    "Cannot connect to Ollama. Make sure it is running with: ollama serve"
)


@mcp.tool()
def get_cv_summary() -> str:
    """Get the candidate's CV summary including name, education, experience, and skills overview."""
    cv = load_cv()
    projects = load_projects()

    lines = [f"# {cv.name}", ""]

    if cv.summary:
        lines.extend([cv.summary, ""])

    if cv.education:
        lines.append("## Education")
        for edu in cv.education:
            line = f"- {edu.degree} — {edu.school} ({edu.dates})"
            if edu.gpa:
                line += f" | GPA: {edu.gpa}"
            lines.append(line)
        lines.append("")

    if cv.experience:
        lines.append("## Experience")
        for exp in cv.experience:
            lines.append(f"- {exp.role} at {exp.company} ({exp.dates})")
        lines.append("")

    if projects:
        lines.append("## Projects")
        for proj in projects:
            tech = ", ".join(proj.tech) if proj.tech else "N/A"
            lines.append(f"- {proj.title} [{tech}]")
        lines.append("")

    skills = cv.skills
    skill_sections = [
        ("Languages", skills.languages),
        ("Frameworks", skills.frameworks),
        ("AI/ML", skills.ai_ml),
        ("Databases", skills.databases),
        ("Security", skills.security),
        ("Tools", skills.tools),
    ]
    non_empty = [(name, items) for name, items in skill_sections if items]
    if non_empty:
        lines.append("## Skills")
        for name, items in non_empty:
            lines.append(f"- {name}: {', '.join(items)}")
        lines.append("")

    if cv.languages_spoken:
        lines.append("## Languages")
        for lang in cv.languages_spoken:
            lines.append(f"- {lang.language}: {lang.level}")

    return "\n".join(lines)


@mcp.tool()
def list_skills() -> str:
    """List all candidate skills organized by category."""
    cv = load_cv()
    skills = cv.skills

    sections = [
        ("Languages", skills.languages),
        ("Frameworks", skills.frameworks),
        ("AI/ML", skills.ai_ml),
        ("Databases", skills.databases),
        ("Security", skills.security),
        ("Tools", skills.tools),
    ]

    lines = []
    for name, items in sections:
        if items:
            lines.append(f"{name}: {', '.join(items)}")

    return "\n".join(lines) if lines else "No skills listed."


@mcp.tool()
def list_source_chunks() -> str:
    """List all CV and project source chunks with their IDs."""
    cv = load_cv()
    projects = load_projects()
    chunks = build_source_chunks(cv, projects)
    return json.dumps([chunk.model_dump() for chunk in chunks], indent=2)


@mcp.tool()
async def tailor_cv(job_description: str) -> str:
    """Tailor the candidate's CV bullets to match a specific job description."""
    try:
        result = await tailor(job_description)
    except httpx.ConnectError:
        return OLLAMA_UNAVAILABLE

    lines = ["## Tailored Bullets", ""]
    for i, bullet in enumerate(result.tailored_bullets, 1):
        lines.append(f"{i}. [{bullet.relevance.upper()}] {bullet.text}")
        lines.append(f"   Source: {bullet.source_id}")
    lines.append("")

    if result.why_i_fit:
        lines.extend(["## Why I Fit", "", result.why_i_fit, ""])

    if result.gaps:
        lines.append("## Gaps")
        for gap in result.gaps:
            lines.append(f"- {gap}")

    return "\n".join(lines)


@mcp.tool()
async def analyze_skill_gaps(job_description: str) -> str:
    """Analyze what skills or requirements a job description asks for that the candidate lacks."""
    try:
        cv = load_cv()

        skills_summary = []
        for category, items in cv.skills.model_dump().items():
            if items:
                skills_summary.append(f"{category}: {', '.join(items)}")

        experience_summary = []
        for exp in cv.experience:
            experience_summary.append(f"- {exp.role} at {exp.company} ({exp.dates})")

        llm = OllamaClient()
        prompt = build_skill_gap_prompt(
            "\n".join(skills_summary),
            "\n".join(experience_summary),
            job_description,
        )
        response = await llm.chat(
            system_prompt=SKILL_GAP_SYSTEM_PROMPT,
            user_prompt=prompt,
            json_mode=False,
        )
        return response
    except httpx.ConnectError:
        return OLLAMA_UNAVAILABLE


def main():
    mcp.run()
