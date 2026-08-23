from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from career_copilot.models.domain import SourceChunk


def _make_chunks():
    return [
        SourceChunk(
            source_id="exp:bullet:0",
            source_type="cv_bullet",
            content="Built REST APIs",
        ),
        SourceChunk(
            source_id="project:test",
            source_type="project_description",
            content="Test project",
        ),
    ]


def test_ingest_endpoint_registered():
    from fastapi.testclient import TestClient

    from career_copilot.main import app

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/ingest")
    assert response.status_code != 404


@pytest.mark.asyncio
@patch("career_copilot.services.ingestion.load_cv")
@patch("career_copilot.services.ingestion.load_projects")
@patch("career_copilot.services.ingestion.build_source_chunks")
@patch("career_copilot.services.ingestion.OllamaClient")
async def test_ingest_chunks_calls_embed(mock_client_cls, mock_build, mock_projects, mock_cv):
    chunks = _make_chunks()
    mock_build.return_value = chunks
    mock_cv.return_value = None
    mock_projects.return_value = []

    mock_client = AsyncMock()
    mock_client.embed.return_value = [[0.1] * 768, [0.2] * 768]
    mock_client_cls.return_value = mock_client

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    from career_copilot.services.ingestion import ingest_chunks

    result = await ingest_chunks(mock_session)

    mock_client.embed.assert_called_once_with(["Built REST APIs", "Test project"])
    assert result["total_chunks"] == 2
    assert result["created"] == 2
    assert result["skipped"] == 0
    assert mock_session.add.call_count == 2
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
@patch("career_copilot.services.ingestion.load_cv")
@patch("career_copilot.services.ingestion.load_projects")
@patch("career_copilot.services.ingestion.build_source_chunks")
@patch("career_copilot.services.ingestion.OllamaClient")
async def test_ingest_skips_existing_chunks(mock_client_cls, mock_build, mock_projects, mock_cv):
    chunks = _make_chunks()
    mock_build.return_value = chunks
    mock_cv.return_value = None
    mock_projects.return_value = []

    mock_client = AsyncMock()
    mock_client.embed.return_value = [[0.1] * 768, [0.2] * 768]
    mock_client_cls.return_value = mock_client

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = "existing"
    mock_session.execute.return_value = mock_result

    from career_copilot.services.ingestion import ingest_chunks

    result = await ingest_chunks(mock_session)

    assert result["created"] == 0
    assert result["skipped"] == 2
    assert mock_session.add.call_count == 0
