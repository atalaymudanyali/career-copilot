from pathlib import Path

from career_copilot.services.data_loader import build_source_chunks, load_cv, load_projects

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_cv():
    cv = load_cv(FIXTURES / "cv.json")
    assert cv.name == "Test User"
    assert len(cv.experience) == 1
    assert cv.experience[0].id == "internship-alpha"
    assert len(cv.experience[0].bullets) == 2


def test_load_cv_skills():
    cv = load_cv(FIXTURES / "cv.json")
    assert "Python" in cv.skills.languages
    assert "FastAPI" in cv.skills.frameworks
    assert "GPT-4 API" in cv.skills.ai_ml


def test_load_projects():
    projects = load_projects(FIXTURES / "projects")
    assert len(projects) == 1
    assert projects[0].id == "test-project"
    assert projects[0].title == "Test Project"
    assert "Python" in projects[0].tech
    assert "containerized" in projects[0].description.lower()


def test_build_source_chunks():
    cv = load_cv(FIXTURES / "cv.json")
    projects = load_projects(FIXTURES / "projects")
    chunks = build_source_chunks(cv, projects)

    source_ids = {c.source_id for c in chunks}
    assert "internship-alpha:bullet:0" in source_ids
    assert "internship-alpha:bullet:1" in source_ids
    assert "project:test-project" in source_ids
    assert "skills:all" in source_ids

    # CV bullets include role context
    bullet_chunk = next(c for c in chunks if c.source_id == "internship-alpha:bullet:0")
    assert "Software Intern" in bullet_chunk.content
    assert "Alpha Corp" in bullet_chunk.content


def test_source_chunk_types():
    cv = load_cv(FIXTURES / "cv.json")
    projects = load_projects(FIXTURES / "projects")
    chunks = build_source_chunks(cv, projects)

    types = {c.source_type for c in chunks}
    assert types == {"cv_bullet", "project_description", "skill"}


def test_context_chunk_included_when_present():
    cv = load_cv(FIXTURES / "cv.json")
    cv.experience[0].context = "Shipped a product to production."
    projects = load_projects(FIXTURES / "projects")
    chunks = build_source_chunks(cv, projects)

    context_chunks = [c for c in chunks if c.source_type == "cv_context"]
    assert len(context_chunks) == 1
    assert "Shipped a product" in context_chunks[0].content
    assert context_chunks[0].source_id == "internship-alpha:context"


def test_context_chunk_skipped_when_empty():
    cv = load_cv(FIXTURES / "cv.json")
    assert cv.experience[0].context == ""
    projects = load_projects(FIXTURES / "projects")
    chunks = build_source_chunks(cv, projects)

    context_chunks = [c for c in chunks if c.source_type == "cv_context"]
    assert len(context_chunks) == 0
