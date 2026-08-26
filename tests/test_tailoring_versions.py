from unittest.mock import AsyncMock, MagicMock

import pytest

from career_copilot.services.tailoring_versions import (
    create_version,
    get_latest_version,
    get_version,
    list_versions,
)


def _mock_session():
    session = AsyncMock()
    return session


SAMPLE_RESULT = {
    "tailored_bullets": [
        {"text": "Built APIs", "source_id": "exp1:b1", "relevance": "high"}
    ],
    "why_i_fit": "Strong backend skills",
    "gaps": [],
}


@pytest.mark.asyncio
async def test_create_version_first():
    session = _mock_session()
    mock_scalar = MagicMock()
    mock_scalar.scalar.return_value = None
    session.execute.return_value = mock_scalar

    version = MagicMock()
    version.application_id = 1
    version.version_number = 1
    version.tailoring_result = SAMPLE_RESULT

    async def fake_refresh(obj):
        obj.version_number = 1
        obj.application_id = 1
        obj.tailoring_result = SAMPLE_RESULT

    session.refresh.side_effect = fake_refresh

    await create_version(session, 1, SAMPLE_RESULT)
    session.add.assert_called_once()
    session.commit.assert_awaited_once()
    added_obj = session.add.call_args[0][0]
    assert added_obj.application_id == 1
    assert added_obj.version_number == 1
    assert added_obj.tailoring_result == SAMPLE_RESULT


@pytest.mark.asyncio
async def test_create_version_increments():
    session = _mock_session()
    mock_scalar = MagicMock()
    mock_scalar.scalar.return_value = 3
    session.execute.return_value = mock_scalar

    session.refresh = AsyncMock()

    await create_version(session, 1, SAMPLE_RESULT)
    added_obj = session.add.call_args[0][0]
    assert added_obj.version_number == 4


@pytest.mark.asyncio
async def test_list_versions():
    session = _mock_session()
    v1 = MagicMock(version_number=1)
    v2 = MagicMock(version_number=2)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [v2, v1]
    session.execute.return_value = mock_result

    versions = await list_versions(session, 1)
    assert len(versions) == 2
    assert versions[0].version_number == 2


@pytest.mark.asyncio
async def test_get_version():
    session = _mock_session()
    v = MagicMock(id=5, version_number=2)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = v
    session.execute.return_value = mock_result

    result = await get_version(session, 5)
    assert result.id == 5


@pytest.mark.asyncio
async def test_get_version_not_found():
    session = _mock_session()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result

    result = await get_version(session, 999)
    assert result is None


@pytest.mark.asyncio
async def test_get_latest_version():
    session = _mock_session()
    v = MagicMock(version_number=3)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = v
    session.execute.return_value = mock_result

    result = await get_latest_version(session, 1)
    assert result.version_number == 3


@pytest.mark.asyncio
async def test_get_latest_version_none():
    session = _mock_session()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result

    result = await get_latest_version(session, 1)
    assert result is None
