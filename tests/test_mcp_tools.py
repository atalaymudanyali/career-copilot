import json
from unittest.mock import patch

from career_copilot.models.domain import (
    CV,
    ContactInfo,
    Education,
    Experience,
    Project,
    Skills,
    SourceChunk,
    SpokenLanguage,
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
