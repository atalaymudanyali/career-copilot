from unittest.mock import AsyncMock, patch

import httpx
import pytest

from career_copilot.services.llm import OllamaClient


@pytest.mark.asyncio
async def test_embed_returns_vectors():
    fake_embeddings = [[0.1] * 768, [0.2] * 768]
    mock_response = httpx.Response(
        200,
        json={"embeddings": fake_embeddings},
        request=httpx.Request("POST", "http://localhost:11434/api/embed"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        client = OllamaClient()
        result = await client.embed(["text one", "text two"])

    assert len(result) == 2
    assert len(result[0]) == 768
    assert len(result[1]) == 768


@pytest.mark.asyncio
async def test_embed_single_text():
    fake_embeddings = [[0.5] * 768]
    mock_response = httpx.Response(
        200,
        json={"embeddings": fake_embeddings},
        request=httpx.Request("POST", "http://localhost:11434/api/embed"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        client = OllamaClient()
        result = await client.embed(["single text"])

    assert len(result) == 1
    assert len(result[0]) == 768


@pytest.mark.asyncio
async def test_embed_calls_correct_endpoint():
    fake_embeddings = [[0.1] * 768]
    mock_response = httpx.Response(
        200,
        json={"embeddings": fake_embeddings},
        request=httpx.Request("POST", "http://localhost:11434/api/embed"),
    )

    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as mock_post:
        client = OllamaClient(base_url="http://myhost:11434")
        await client.embed(["test"])

    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[0][0] == "http://myhost:11434/api/embed"
    assert call_args[1]["json"]["model"] == "nomic-embed-text"
    assert call_args[1]["json"]["input"] == ["test"]
