from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from career_copilot.services.retrieval import retrieve


def _make_db_chunk(source_id, source_type, content):
    chunk = MagicMock()
    chunk.source_id = source_id
    chunk.source_type = source_type
    chunk.content = content
    return chunk


@pytest.mark.asyncio
@patch("career_copilot.services.retrieval.OllamaClient")
async def test_retrieve_returns_source_chunks(mock_client_cls):
    mock_client = AsyncMock()
    mock_client.embed.return_value = [[0.1] * 768]
    mock_client_cls.return_value = mock_client

    db_chunks = [
        _make_db_chunk("exp:bullet:0", "cv_bullet", "Built REST APIs"),
        _make_db_chunk("project:test", "project_description", "Test project"),
    ]

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = db_chunks
    mock_session.execute.return_value = mock_result

    result = await retrieve("backend engineer", mock_session, k=5)

    assert len(result) == 2
    assert result[0].source_id == "exp:bullet:0"
    assert result[1].source_id == "project:test"
    mock_client.embed.assert_called_once_with(["backend engineer"])


@pytest.mark.asyncio
@patch("career_copilot.services.retrieval.OllamaClient")
async def test_retrieve_returns_empty_when_no_chunks(mock_client_cls):
    mock_client = AsyncMock()
    mock_client.embed.return_value = [[0.1] * 768]
    mock_client_cls.return_value = mock_client

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    result = await retrieve("frontend designer", mock_session)

    assert result == []
