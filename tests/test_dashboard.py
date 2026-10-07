import pytest


def test_index_returns_html():
    from fastapi.testclient import TestClient

    from career_copilot.main import app

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Career Copilot" in response.text


def test_index_contains_dashboard_link():
    from fastapi.testclient import TestClient

    from career_copilot.main import app

    client = TestClient(app)
    response = client.get("/")
    assert '/dashboard"' in response.text


def test_pipeline_route_registered():
    from fastapi.testclient import TestClient

    from career_copilot.main import app

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/dashboard/pipeline")
    assert resp.status_code != 404


def test_nav_contains_pipeline_link():
    from fastapi.testclient import TestClient

    from career_copilot.main import app

    client = TestClient(app)
    response = client.get("/")
    assert '/dashboard/pipeline"' in response.text


async def _call_with_application(handler, application, **kwargs):
    from unittest.mock import AsyncMock, MagicMock, patch

    session = AsyncMock()
    with (
        patch("career_copilot.api.dashboard.get_application", return_value=application),
        patch("career_copilot.api.dashboard.list_versions", return_value=[]),
        patch("career_copilot.api.dashboard.get_favorited_texts", return_value=set()),
        patch("career_copilot.api.dashboard.templates") as templates,
    ):
        await handler(request=MagicMock(), application_id=1, session=session, **kwargs)
    return templates


def _application(notes):
    from unittest.mock import MagicMock

    from career_copilot.models.db import Application

    app = MagicMock(spec=Application)
    app.notes = notes
    app.company = "Acme Corp"
    return app


@pytest.mark.asyncio
async def test_removing_the_last_note_clears_notes():
    from career_copilot.api.dashboard import dashboard_remove_note

    application = _application("only note")
    await _call_with_application(dashboard_remove_note, application, note_index=0)

    assert application.notes is None


@pytest.mark.asyncio
async def test_empty_required_field_in_form_is_ignored():
    from unittest.mock import AsyncMock, MagicMock, patch

    from career_copilot.api.dashboard import dashboard_update

    application = _application("keep")
    request = MagicMock()
    request.form = AsyncMock(return_value={"company": "", "notes": ""})
    with (
        patch("career_copilot.api.dashboard.get_application", return_value=application),
        patch("career_copilot.api.dashboard.list_versions", return_value=[]),
        patch("career_copilot.api.dashboard.get_favorited_texts", return_value=set()),
        patch("career_copilot.api.dashboard.templates"),
    ):
        await dashboard_update(request=request, application_id=1, session=AsyncMock())

    assert application.company == "Acme Corp"
    assert application.notes is None
