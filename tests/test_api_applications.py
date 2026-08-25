from unittest.mock import AsyncMock, MagicMock

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
        "tailoring_result": None,
        "applied_at": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    app = MagicMock(spec=Application)
    for key, value in defaults.items():
        setattr(app, key, value)
    return app


def test_applications_routes_registered():
    from fastapi.testclient import TestClient

    from career_copilot.main import app

    client = TestClient(app, raise_server_exceptions=False)

    post_resp = client.post("/api/applications")
    assert post_resp.status_code != 404

    get_resp = client.get("/api/applications")
    assert get_resp.status_code != 404

    get_one_resp = client.get("/api/applications/1")
    assert get_one_resp.status_code != 404

    patch_resp = client.patch("/api/applications/1")
    assert patch_resp.status_code != 404

    delete_resp = client.delete("/api/applications/1")
    assert delete_resp.status_code != 404


@pytest.mark.asyncio
async def test_create_application():
    from career_copilot.models.domain import ApplicationCreate
    from career_copilot.services.applications import create_application

    mock_session = AsyncMock()
    data = ApplicationCreate(
        company="Acme Corp",
        role="Backend Engineer",
        jd_text="Looking for a backend engineer...",
    )

    await create_application(mock_session, data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    added_obj = mock_session.add.call_args[0][0]
    assert added_obj.company == "Acme Corp"
    assert added_obj.role == "Backend Engineer"


@pytest.mark.asyncio
async def test_list_applications():
    from career_copilot.services.applications import list_applications

    mock_session = AsyncMock()
    app1 = _make_application(id=1, company="Acme")
    app2 = _make_application(id=2, company="Beta")
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [app1, app2]
    mock_session.execute.return_value = mock_result

    result = await list_applications(mock_session)

    assert len(result) == 2
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_list_applications_with_status_filter():
    from career_copilot.services.applications import list_applications

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    await list_applications(mock_session, status="applied")

    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_application_found():
    from career_copilot.services.applications import get_application

    mock_session = AsyncMock()
    app = _make_application()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = app
    mock_session.execute.return_value = mock_result

    result = await get_application(mock_session, 1)

    assert result is app


@pytest.mark.asyncio
async def test_get_application_not_found():
    from career_copilot.services.applications import get_application

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await get_application(mock_session, 999)

    assert result is None


@pytest.mark.asyncio
async def test_update_application():
    from career_copilot.models.domain import ApplicationUpdate
    from career_copilot.services.applications import update_application

    mock_session = AsyncMock()
    app = _make_application()
    data = ApplicationUpdate(status="applied", notes="Submitted via portal")

    await update_application(mock_session, app, data)

    assert app.status == "applied"
    assert app.notes == "Submitted via portal"
    assert app.company == "Acme Corp"
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_delete_application():
    from career_copilot.services.applications import delete_application

    mock_session = AsyncMock()
    app = _make_application()

    await delete_application(mock_session, app)

    mock_session.delete.assert_called_once_with(app)
    mock_session.commit.assert_called_once()
