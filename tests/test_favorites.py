from unittest.mock import AsyncMock, MagicMock

import pytest

from career_copilot.services.favorites import (
    get_favorited_texts,
    list_all_favorites,
    list_favorites,
    toggle_favorite,
)


def _mock_session():
    session = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_toggle_favorite_add():
    session = _mock_session()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result

    is_fav = await toggle_favorite(session, 1, "Built APIs", "exp1:b1", "high")
    assert is_fav is True
    session.add.assert_called_once()
    added = session.add.call_args[0][0]
    assert added.bullet_text == "Built APIs"
    assert added.source_id == "exp1:b1"
    assert added.relevance == "high"
    assert added.application_id == 1
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_toggle_favorite_remove():
    session = _mock_session()
    existing = MagicMock()
    existing.bullet_text = "Built APIs"
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing
    session.execute.return_value = mock_result

    is_fav = await toggle_favorite(session, 1, "Built APIs", "exp1:b1")
    assert is_fav is False
    session.delete.assert_awaited_once_with(existing)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_toggle_favorite_scoped_to_application():
    session = _mock_session()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result

    await toggle_favorite(session, 5, "Deployed services", "exp2:b3")
    added = session.add.call_args[0][0]
    assert added.application_id == 5


@pytest.mark.asyncio
async def test_list_favorites():
    session = _mock_session()
    f1 = MagicMock(bullet_text="Built APIs", application_id=1)
    f2 = MagicMock(bullet_text="Led team", application_id=1)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [f1, f2]
    session.execute.return_value = mock_result

    favorites = await list_favorites(session, 1)
    assert len(favorites) == 2
    assert favorites[0].bullet_text == "Built APIs"


@pytest.mark.asyncio
async def test_list_favorites_empty():
    session = _mock_session()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result

    favorites = await list_favorites(session, 1)
    assert favorites == []


@pytest.mark.asyncio
async def test_list_all_favorites():
    session = _mock_session()
    f1 = MagicMock(bullet_text="Built APIs", application_id=1)
    f2 = MagicMock(bullet_text="Led team", application_id=2)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [f1, f2]
    session.execute.return_value = mock_result

    favorites = await list_all_favorites(session)
    assert len(favorites) == 2


@pytest.mark.asyncio
async def test_get_favorited_texts():
    session = _mock_session()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        "Built APIs",
        "Led team",
    ]
    session.execute.return_value = mock_result

    texts = await get_favorited_texts(session, 1)
    assert texts == {"Built APIs", "Led team"}


@pytest.mark.asyncio
async def test_get_favorited_texts_empty():
    session = _mock_session()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result

    texts = await get_favorited_texts(session, 1)
    assert texts == set()
