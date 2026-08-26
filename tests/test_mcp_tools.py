import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from career_copilot.models.domain import (
    CV,
    ContactInfo,
    Education,
    Experience,
    Project,
    Skills,
    SourceChunk,
    SpokenLanguage,
    TailoredBullet,
    TailoringResult,
)


def _sample_cv():
    return CV(
        name="Test Candidate",
        contact=ContactInfo(email="test@example.com"),
        summary="A skilled developer.",
        education=[
            Education(degree="BSc Computer Science", school="Test University", dates="2022-2026"),
        ],
        skills=Skills(
            languages=["Python", "Java"],
            frameworks=["FastAPI", "Spring Boot"],
            ai_ml=["LangChain"],
            databases=["PostgreSQL"],
        ),
        experience=[
            Experience(
                id="exp1",
                role="Backend Developer",
                company="TestCorp",
                dates="2025-Present",
                bullets=["Built REST APIs with FastAPI"],
            ),
        ],
        languages_spoken=[SpokenLanguage(language="English", level="Fluent")],
    )


def _sample_projects():
    return [
        Project(id="proj1", title="Career Copilot", tech=["Python", "FastAPI"]),
    ]


def _sample_chunks():
    return [
        SourceChunk(source_id="exp1:bullet:0", source_type="cv_bullet", content="Built APIs"),
        SourceChunk(source_id="skills:all", source_type="skill", content="Python, Java"),
    ]


@patch("career_copilot.mcp_server.load_projects", return_value=[])
@patch("career_copilot.mcp_server.load_cv")
def test_get_cv_summary_returns_name(mock_cv, mock_projects):
    from career_copilot.mcp_server import get_cv_summary

    mock_cv.return_value = _sample_cv()
    result = get_cv_summary()
    assert "Test Candidate" in result


@patch("career_copilot.mcp_server.load_projects", return_value=[])
@patch("career_copilot.mcp_server.load_cv")
def test_get_cv_summary_includes_education(mock_cv, mock_projects):
    from career_copilot.mcp_server import get_cv_summary

    mock_cv.return_value = _sample_cv()
    result = get_cv_summary()
    assert "BSc Computer Science" in result
    assert "Test University" in result


@patch("career_copilot.mcp_server.load_projects")
@patch("career_copilot.mcp_server.load_cv")
def test_get_cv_summary_includes_projects(mock_cv, mock_projects):
    from career_copilot.mcp_server import get_cv_summary

    mock_cv.return_value = _sample_cv()
    mock_projects.return_value = _sample_projects()
    result = get_cv_summary()
    assert "Career Copilot" in result


@patch("career_copilot.mcp_server.load_cv")
def test_list_skills_returns_categories(mock_cv):
    from career_copilot.mcp_server import list_skills

    mock_cv.return_value = _sample_cv()
    result = list_skills()
    assert "Languages:" in result
    assert "Python" in result
    assert "Frameworks:" in result
    assert "FastAPI" in result
    assert "AI/ML:" in result


@patch("career_copilot.mcp_server.load_cv")
def test_list_skills_empty(mock_cv):
    from career_copilot.mcp_server import list_skills

    mock_cv.return_value = CV(name="Empty", contact=ContactInfo(email="e@e.com"))
    result = list_skills()
    assert result == "No skills listed."


@patch("career_copilot.mcp_server.build_source_chunks")
@patch("career_copilot.mcp_server.load_projects")
@patch("career_copilot.mcp_server.load_cv")
def test_list_source_chunks_returns_json(mock_cv, mock_projects, mock_build):
    from career_copilot.mcp_server import list_source_chunks

    mock_cv.return_value = _sample_cv()
    mock_projects.return_value = _sample_projects()
    mock_build.return_value = _sample_chunks()
    result = list_source_chunks()
    parsed = json.loads(result)
    assert len(parsed) == 2
    assert parsed[0]["source_id"] == "exp1:bullet:0"


@patch("career_copilot.mcp_server.build_source_chunks")
@patch("career_copilot.mcp_server.load_projects")
@patch("career_copilot.mcp_server.load_cv")
def test_list_source_chunks_has_required_fields(mock_cv, mock_projects, mock_build):
    from career_copilot.mcp_server import list_source_chunks

    mock_cv.return_value = _sample_cv()
    mock_projects.return_value = _sample_projects()
    mock_build.return_value = _sample_chunks()
    result = list_source_chunks()
    parsed = json.loads(result)
    for chunk in parsed:
        assert "source_id" in chunk
        assert "source_type" in chunk
        assert "content" in chunk


def _sample_tailoring_result():
    return TailoringResult(
        tailored_bullets=[
            TailoredBullet(
                text="Developed REST APIs using FastAPI",
                source_id="exp1:bullet:0",
                relevance="high",
            ),
            TailoredBullet(
                text="Proficient in Python and Java",
                source_id="skills:all",
                relevance="medium",
            ),
        ],
        why_i_fit="Strong backend experience with Python and API development.",
        gaps=["Kubernetes", "GraphQL"],
    )


@pytest.mark.asyncio
@patch("career_copilot.mcp_server.tailor")
async def test_tailor_cv_returns_bullets(mock_tailor):
    from career_copilot.mcp_server import tailor_cv

    mock_tailor.return_value = _sample_tailoring_result()
    result = await tailor_cv("We need a backend developer with Python")
    assert "Tailored Bullets" in result
    assert "Developed REST APIs" in result
    assert "exp1:bullet:0" in result
    assert "HIGH" in result


@pytest.mark.asyncio
@patch("career_copilot.mcp_server.tailor")
async def test_tailor_cv_includes_why_and_gaps(mock_tailor):
    from career_copilot.mcp_server import tailor_cv

    mock_tailor.return_value = _sample_tailoring_result()
    result = await tailor_cv("Backend developer role")
    assert "Why I Fit" in result
    assert "Strong backend" in result
    assert "Gaps" in result
    assert "Kubernetes" in result
    assert "GraphQL" in result


@pytest.mark.asyncio
@patch("career_copilot.mcp_server.tailor", side_effect=httpx.ConnectError(""))
async def test_tailor_cv_ollama_unavailable(mock_tailor):
    from career_copilot.mcp_server import tailor_cv

    result = await tailor_cv("Any JD")
    assert "Cannot connect to Ollama" in result


@pytest.mark.asyncio
@patch("career_copilot.mcp_server.OllamaClient")
@patch("career_copilot.mcp_server.load_cv")
async def test_analyze_skill_gaps_returns_response(mock_cv, mock_llm_cls):
    from career_copilot.mcp_server import analyze_skill_gaps

    mock_cv.return_value = _sample_cv()
    mock_llm = AsyncMock()
    mock_llm.chat.return_value = "## Must-have gaps\n- Kubernetes"
    mock_llm_cls.return_value = mock_llm

    result = await analyze_skill_gaps("Need 3+ years Kubernetes experience")
    assert "Kubernetes" in result


@pytest.mark.asyncio
@patch(
    "career_copilot.mcp_server.OllamaClient",
    side_effect=httpx.ConnectError(""),
)
async def test_analyze_skill_gaps_ollama_unavailable(mock_llm_cls):
    from career_copilot.mcp_server import analyze_skill_gaps

    result = await analyze_skill_gaps("Any JD")
    assert "Cannot connect to Ollama" in result


# --- Application tracker tool tests ---


def _mock_application(
    id=1,
    company="TestCorp",
    role="Backend Developer",
    status="saved",
    jd_text="Looking for a dev",
    url=None,
    notes=None,
    tailoring_result=None,
    applied_at=None,
):
    from datetime import datetime
    from unittest.mock import MagicMock

    app = MagicMock()
    app.id = id
    app.company = company
    app.role = role
    app.status = status
    app.jd_text = jd_text
    app.url = url
    app.notes = notes
    app.tailoring_result = tailoring_result
    app.applied_at = applied_at
    app.created_at = datetime(2026, 1, 15)
    app.updated_at = datetime(2026, 1, 15)
    return app


def _mock_db_session():
    from unittest.mock import MagicMock

    mock_session = AsyncMock()
    mock_session_factory = MagicMock()
    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_session)
    ctx.__aexit__ = AsyncMock(return_value=False)
    mock_session_factory.return_value = ctx
    return mock_session, mock_session_factory


@pytest.mark.asyncio
async def test_list_applications_returns_apps():
    from career_copilot.mcp_server import list_applications

    _, mock_factory = _mock_db_session()
    mock_apps = [
        _mock_application(id=1, company="Google", role="SWE"),
        _mock_application(id=2, company="Meta", role="Backend"),
    ]

    with (
        patch("career_copilot.mcp_server._get_db_session", return_value=mock_factory),
        patch(
            "career_copilot.services.applications.list_applications",
            return_value=mock_apps,
        ),
    ):
        result = await list_applications()
        assert "Google" in result
        assert "Meta" in result
        assert "#1" in result
        assert "#2" in result


@pytest.mark.asyncio
async def test_list_applications_empty():
    from career_copilot.mcp_server import list_applications

    _, mock_factory = _mock_db_session()

    with (
        patch("career_copilot.mcp_server._get_db_session", return_value=mock_factory),
        patch(
            "career_copilot.services.applications.list_applications",
            return_value=[],
        ),
    ):
        result = await list_applications()
        assert "No applications found" in result


@pytest.mark.asyncio
async def test_add_application_creates():
    from career_copilot.mcp_server import add_application

    _, mock_factory = _mock_db_session()
    mock_app = _mock_application(id=5, company="Stripe", role="Backend Engineer")

    with (
        patch("career_copilot.mcp_server._get_db_session", return_value=mock_factory),
        patch(
            "career_copilot.services.applications.create_application",
            return_value=mock_app,
        ),
    ):
        result = await add_application("Stripe", "Backend Engineer", "Build APIs")
        assert "#5" in result
        assert "Stripe" in result


@pytest.mark.asyncio
async def test_get_application_found():
    from career_copilot.mcp_server import get_application

    _, mock_factory = _mock_db_session()
    mock_app = _mock_application(
        id=3, company="Google", role="SWE", jd_text="Build distributed systems"
    )

    with (
        patch("career_copilot.mcp_server._get_db_session", return_value=mock_factory),
        patch(
            "career_copilot.services.applications.get_application",
            return_value=mock_app,
        ),
    ):
        result = await get_application(3)
        assert "Google" in result
        assert "SWE" in result
        assert "Build distributed systems" in result


@pytest.mark.asyncio
async def test_get_application_not_found():
    from career_copilot.mcp_server import get_application

    _, mock_factory = _mock_db_session()

    with (
        patch("career_copilot.mcp_server._get_db_session", return_value=mock_factory),
        patch(
            "career_copilot.services.applications.get_application",
            return_value=None,
        ),
    ):
        result = await get_application(999)
        assert "not found" in result


@pytest.mark.asyncio
async def test_update_application_status_valid():
    from career_copilot.mcp_server import update_application_status

    _, mock_factory = _mock_db_session()
    mock_app = _mock_application(id=1, company="Google", role="SWE", status="applied")

    with (
        patch("career_copilot.mcp_server._get_db_session", return_value=mock_factory),
        patch(
            "career_copilot.services.applications.get_application",
            return_value=mock_app,
        ),
        patch(
            "career_copilot.services.applications.update_application",
            return_value=mock_app,
        ),
    ):
        result = await update_application_status(1, "applied")
        assert "applied" in result
        assert "Google" in result


@pytest.mark.asyncio
async def test_update_application_status_invalid():
    from career_copilot.mcp_server import update_application_status

    result = await update_application_status(1, "invalid_status")
    assert "Invalid status" in result
    assert "saved" in result


# --- PDF generation tool tests ---


@pytest.mark.asyncio
@patch(
    "career_copilot.services.pdf.generate_cv_pdf",
    return_value=b"%PDF-1.4 fake",
)
@patch("career_copilot.mcp_server.tailor")
async def test_generate_cv_pdf_returns_path(mock_tailor, mock_make_pdf):
    from career_copilot.mcp_server import generate_cv_pdf

    mock_tailor.return_value = _sample_tailoring_result()
    result = await generate_cv_pdf("Backend dev role", "Google", "SWE")
    assert "PDF generated" in result
    assert "Google" in result
    assert "SWE" in result
    assert result.endswith(".pdf")


@pytest.mark.asyncio
@patch(
    "career_copilot.mcp_server.tailor",
    side_effect=httpx.ConnectError(""),
)
async def test_generate_cv_pdf_ollama_unavailable(mock_tailor):
    from career_copilot.mcp_server import generate_cv_pdf

    result = await generate_cv_pdf("Any JD", "Google", "SWE")
    assert "Cannot connect to Ollama" in result
