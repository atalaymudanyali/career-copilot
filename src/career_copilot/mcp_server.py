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

OLLAMA_UNAVAILABLE = "Cannot connect to Ollama. Make sure it is running with: ollama serve"
DB_UNAVAILABLE = "Cannot connect to the database. Start Docker with: docker compose up -d"


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


def _get_db_session():
    from career_copilot.db import async_session

    return async_session


@mcp.tool()
async def list_applications(status: str | None = None) -> str:
    """List tracked job applications, optionally filtered by status."""
    try:
        from career_copilot.services.applications import (
            list_applications as list_apps,
        )

        async with _get_db_session()() as session:
            apps = await list_apps(session, status=status)
    except (OSError, Exception) as exc:
        if "connect" in str(exc).lower() or "operational" in str(exc).lower():
            return DB_UNAVAILABLE
        raise

    if not apps:
        if not status:
            return "No applications found."
        return f"No applications with status '{status}'."

    lines = ["## Applications", ""]
    for app in apps:
        lines.append(f"- **#{app.id}** {app.company} — {app.role} [{app.status}]")
        if app.applied_at:
            lines.append(f"  Applied: {app.applied_at.strftime('%Y-%m-%d')}")
    return "\n".join(lines)


@mcp.tool()
async def add_application(
    company: str,
    role: str,
    job_description: str,
    url: str | None = None,
    notes: str | None = None,
) -> str:
    """Save a new job application to the tracker."""
    try:
        from career_copilot.models.domain import ApplicationCreate
        from career_copilot.services.applications import create_application

        data = ApplicationCreate(
            company=company,
            role=role,
            jd_text=job_description,
            url=url,
            notes=notes,
        )
        async with _get_db_session()() as session:
            app = await create_application(session, data)
    except (OSError, Exception) as exc:
        if "connect" in str(exc).lower() or "operational" in str(exc).lower():
            return DB_UNAVAILABLE
        raise

    return f"Application #{app.id} created: {app.company} — {app.role} [saved]"


@mcp.tool()
async def get_application(application_id: int) -> str:
    """Get full details of a tracked application by its ID."""
    try:
        from career_copilot.services.applications import (
            get_application as get_app,
        )

        async with _get_db_session()() as session:
            app = await get_app(session, application_id)
    except (OSError, Exception) as exc:
        if "connect" in str(exc).lower() or "operational" in str(exc).lower():
            return DB_UNAVAILABLE
        raise

    if not app:
        return f"Application #{application_id} not found."

    lines = [
        f"## Application #{app.id}",
        "",
        f"**Company:** {app.company}",
        f"**Role:** {app.role}",
        f"**Status:** {app.status}",
        f"**Created:** {app.created_at.strftime('%Y-%m-%d')}",
    ]
    if app.url:
        lines.append(f"**URL:** {app.url}")
    if app.notes:
        lines.append(f"**Notes:** {app.notes}")
    if app.applied_at:
        lines.append(f"**Applied:** {app.applied_at.strftime('%Y-%m-%d')}")
    lines.extend(["", "### Job Description", "", app.jd_text])
    if app.tailoring_result:
        lines.extend(["", "### Tailoring Result", "", json.dumps(app.tailoring_result, indent=2)])
    return "\n".join(lines)


@mcp.tool()
async def update_application_status(application_id: int, status: str) -> str:
    """Update the status of a tracked application (saved/applied/interviewing/offered/rejected)."""
    from career_copilot.models.domain import ApplicationStatus

    valid_statuses = [s.value for s in ApplicationStatus]
    if status not in valid_statuses:
        return f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"

    try:
        from career_copilot.models.domain import ApplicationUpdate
        from career_copilot.services.applications import (
            get_application as get_app,
        )
        from career_copilot.services.applications import (
            update_application,
        )

        async with _get_db_session()() as session:
            app = await get_app(session, application_id)
            if not app:
                return f"Application #{application_id} not found."
            data = ApplicationUpdate(status=ApplicationStatus(status))
            app = await update_application(session, app, data)
    except (OSError, Exception) as exc:
        if "connect" in str(exc).lower() or "operational" in str(exc).lower():
            return DB_UNAVAILABLE
        raise

    return f"Application #{app.id} ({app.company} — {app.role}) updated to [{app.status}]"


@mcp.tool()
async def generate_cv_pdf(job_description: str, company: str, role: str) -> str:
    """Tailor the CV for a job and generate a PDF file."""
    try:
        result = await tailor(job_description)
    except httpx.ConnectError:
        return OLLAMA_UNAVAILABLE

    try:
        from career_copilot.services.pdf import generate_cv_pdf as make_pdf
    except ImportError:
        return "WeasyPrint is not installed. Install it with: uv pip install weasyprint"

    result_dict = result.model_dump()
    pdf_bytes = make_pdf(result_dict, company, role)

    from pathlib import Path

    output_dir = Path(__file__).resolve().parents[2] / "output"
    output_dir.mkdir(exist_ok=True)

    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_company = company.replace(" ", "_")
    safe_role = role.replace(" ", "_")
    filename = f"CV_{safe_company}_{safe_role}_{timestamp}.pdf"
    filepath = output_dir / filename
    filepath.write_bytes(pdf_bytes)

    return f"PDF generated: {filepath}"


@mcp.tool()
async def list_tailoring_versions(application_id: int) -> str:
    """List all tailoring versions for an application, showing version number and date."""
    try:
        from career_copilot.services.tailoring_versions import (
            list_versions,
        )

        async with _get_db_session()() as session:
            versions = await list_versions(session, application_id)
    except (OSError, Exception) as exc:
        if "connect" in str(exc).lower() or "operational" in str(exc).lower():
            return DB_UNAVAILABLE
        raise

    if not versions:
        return f"No tailoring versions found for application #{application_id}."

    lines = [f"## Tailoring Versions for Application #{application_id}", ""]
    for v in versions:
        date_str = v.created_at.strftime("%Y-%m-%d %H:%M") if v.created_at else "N/A"
        bullet_count = len(v.tailoring_result.get("tailored_bullets", []))
        lines.append(f"- **v{v.version_number}** (id={v.id}) — {date_str} — {bullet_count} bullets")
    return "\n".join(lines)


@mcp.tool()
async def get_tailoring_version(application_id: int, version_number: int) -> str:
    """Get the full tailoring result for a specific version of an application."""
    try:
        from career_copilot.services.tailoring_versions import (
            list_versions,
        )

        async with _get_db_session()() as session:
            versions = await list_versions(session, application_id)
            version = next((v for v in versions if v.version_number == version_number), None)
    except (OSError, Exception) as exc:
        if "connect" in str(exc).lower() or "operational" in str(exc).lower():
            return DB_UNAVAILABLE
        raise

    if not version:
        return f"Version {version_number} not found for application #{application_id}."

    result = version.tailoring_result
    lines = [f"## Version {version.version_number} — Application #{application_id}", ""]

    lines.append("### Tailored Bullets")
    for i, bullet in enumerate(result.get("tailored_bullets", []), 1):
        lines.append(f"{i}. [{bullet.get('relevance', 'medium').upper()}] {bullet['text']}")
        lines.append(f"   Source: {bullet['source_id']}")
    lines.append("")

    if result.get("why_i_fit"):
        lines.extend(["### Why I Fit", "", result["why_i_fit"], ""])

    if result.get("gaps"):
        lines.append("### Gaps")
        for gap in result["gaps"]:
            lines.append(f"- {gap}")

    return "\n".join(lines)


@mcp.tool()
async def list_favorite_bullets(application_id: int | None = None) -> str:
    """List favorited bullets, optionally filtered by application ID."""
    try:
        from career_copilot.services.favorites import (
            list_all_favorites,
            list_favorites,
        )

        async with _get_db_session()() as session:
            if application_id:
                favorites = await list_favorites(session, application_id)
            else:
                favorites = await list_all_favorites(session)
    except (OSError, Exception) as exc:
        if "connect" in str(exc).lower() or "operational" in str(exc).lower():
            return DB_UNAVAILABLE
        raise

    if not favorites:
        scope = f" for application #{application_id}" if application_id else ""
        return f"No favorite bullets found{scope}."

    lines = ["## Favorite Bullets", ""]
    for fav in favorites:
        lines.append(f"- [{fav.relevance.upper()}] {fav.bullet_text}")
        lines.append(f"  Source: {fav.source_id} | App: #{fav.application_id}")
    return "\n".join(lines)


@mcp.tool()
async def toggle_favorite_bullet(
    application_id: int,
    bullet_text: str,
    source_id: str,
    relevance: str = "medium",
) -> str:
    """Star or unstar a bullet for an application. Returns the new state."""
    try:
        from career_copilot.services.favorites import toggle_favorite

        async with _get_db_session()() as session:
            is_now_favorited = await toggle_favorite(
                session, application_id, bullet_text, source_id, relevance
            )
    except (OSError, Exception) as exc:
        if "connect" in str(exc).lower() or "operational" in str(exc).lower():
            return DB_UNAVAILABLE
        raise

    action = "starred" if is_now_favorited else "unstarred"
    return f"Bullet {action} for application #{application_id}: {bullet_text[:80]}"


def main():
    mcp.run()
