from unittest.mock import AsyncMock, patch

import pytest

from career_copilot.models.domain import SourceChunk, TailoringResult


def test_tailor_endpoint_registered():
    from fastapi.testclient import TestClient

    from career_copilot.main import app

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/tailor")
    assert response.status_code == 405


@pytest.mark.asyncio
@patch("career_copilot.services.tailoring.OllamaClient")
async def test_tailor_rag_uses_provided_chunks(mock_client_cls):
    mock_client = AsyncMock()
    mock_client.chat.return_value = {
        "tailored_bullets": [
            {"text": "Built REST APIs", "source_id": "exp:bullet:0", "relevance": "high"},
        ],
        "why_i_fit": "Strong backend skills.",
        "gaps": ["Kubernetes"],
    }
    mock_client_cls.return_value = mock_client

    chunks = [
        SourceChunk(source_id="exp:bullet:0", source_type="cv_bullet", content="Built REST APIs"),
    ]

    from career_copilot.services.tailoring import tailor_rag

    result = await tailor_rag("backend engineer", chunks, client=mock_client)

    assert isinstance(result, TailoringResult)
    assert len(result.tailored_bullets) == 1
    assert result.tailored_bullets[0].source_id == "exp:bullet:0"


@pytest.mark.asyncio
@patch("career_copilot.services.tailoring.OllamaClient")
async def test_tailor_rag_drops_invalid_sources(mock_client_cls):
    mock_client = AsyncMock()
    mock_client.chat.return_value = {
        "tailored_bullets": [
            {"text": "Real bullet", "source_id": "exp:bullet:0", "relevance": "high"},
            {"text": "Invented", "source_id": "fake:0", "relevance": "high"},
        ],
        "why_i_fit": "Good fit.",
        "gaps": [],
    }
    mock_client_cls.return_value = mock_client

    chunks = [
        SourceChunk(source_id="exp:bullet:0", source_type="cv_bullet", content="Built REST APIs"),
    ]

    from career_copilot.services.tailoring import tailor_rag

    result = await tailor_rag("backend engineer", chunks, client=mock_client)

    assert len(result.tailored_bullets) == 1
    assert result.tailored_bullets[0].text == "Real bullet"
