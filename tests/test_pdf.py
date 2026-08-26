from unittest.mock import MagicMock, patch

import pytest

from career_copilot.models.db import Application


def _make_application(**overrides):
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    defaults = {
        "id": 1,
        "company": "Acme Corp",
        "role": "Backend Engineer",
        "status": "saved",
        "jd_text": "Looking for a backend engineer...",
        "url": None,
        "notes": None,
        "tailoring_result": {
            "tailored_bullets": [
                {
                    "text": "Built REST APIs with .NET Core",
                    "source_id": "internship-mobven:bullet:2",
                    "relevance": "high",
                },
            ],
            "why_i_fit": "Strong backend experience with REST APIs and Docker.",
            "gaps": ["Kubernetes experience"],
        },
        "applied_at": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    app = MagicMock(spec=Application)
    for key, value in defaults.items():
        setattr(app, key, value)
    return app


def test_cv_pdf_route_registered():
    from fastapi.testclient import TestClient

    from career_copilot.main import app

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/dashboard/1/cv.pdf")
    assert resp.status_code != 404


@pytest.mark.asyncio
@patch("career_copilot.api.dashboard.generate_cv_pdf", return_value=b"%PDF-mock-content")
@patch(
    "career_copilot.api.dashboard.get_favorited_texts",
    return_value=["Built REST APIs with .NET Core"],
)
@patch("career_copilot.api.dashboard.get_application")
async def test_download_cv_pdf_returns_pdf(mock_get, mock_favs, mock_pdf):
    from fastapi.testclient import TestClient

    from career_copilot.main import app

    application = _make_application()
    mock_get.return_value = application

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/dashboard/1/cv.pdf")

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert b"%PDF-mock-content" in resp.content
    mock_pdf.assert_called_once_with(
        application.tailoring_result, application.company, application.role,
        favorite_texts={"Built REST APIs with .NET Core"},
    )


@pytest.mark.asyncio
@patch("career_copilot.api.dashboard.get_application", return_value=None)
async def test_download_cv_pdf_not_found(mock_get):
    from fastapi.testclient import TestClient

    from career_copilot.main import app

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/dashboard/999/cv.pdf")

    assert resp.status_code == 404


@pytest.mark.asyncio
@patch("career_copilot.api.dashboard.get_application")
async def test_download_cv_pdf_not_tailored(mock_get):
    from fastapi.testclient import TestClient

    from career_copilot.main import app

    application = _make_application(tailoring_result=None)
    mock_get.return_value = application

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/dashboard/1/cv.pdf")

    assert resp.status_code == 404


def test_load_cv_returns_cv_model():
    from career_copilot.services.pdf import load_cv

    cv = load_cv()

    assert cv.name == "Atalay Mudanyali"
    assert cv.contact.email == "atalay.mudanyali@gmail.com"
    assert len(cv.experience) > 0
    assert len(cv.education) > 0
