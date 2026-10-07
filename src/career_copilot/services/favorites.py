from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from career_copilot.models.db import FavoriteBullet


async def toggle_favorite(
    session: AsyncSession,
    application_id: int,
    bullet_text: str,
    source_id: str,
    relevance: str = "medium",
) -> bool:
    existing = await session.execute(
        select(FavoriteBullet).where(
            FavoriteBullet.application_id == application_id,
            FavoriteBullet.bullet_text == bullet_text,
        )
    )
    favorite = existing.scalar_one_or_none()

    if favorite:
        await session.delete(favorite)
        await session.commit()
        return False

    new_fav = FavoriteBullet(
        application_id=application_id,
        bullet_text=bullet_text,
        source_id=source_id,
        relevance=relevance,
    )
    session.add(new_fav)
    await session.commit()
    return True


async def add_favorite(
    session: AsyncSession,
    application_id: int,
    bullet_text: str,
    source_id: str,
    relevance: str = "medium",
) -> bool:
    """Star a bullet. Idempotent: starring twice leaves it starred. Returns True if newly added.

    INSERT ... ON CONFLICT DO NOTHING is one atomic statement, so concurrent calls can't
    race into a duplicate-key error the way check-then-insert can.
    """
    statement = (
        insert(FavoriteBullet)
        .values(
            application_id=application_id,
            bullet_text=bullet_text,
            source_id=source_id,
            relevance=relevance,
        )
        .on_conflict_do_nothing(index_elements=["application_id", "bullet_text"])
    )
    result = await session.execute(statement)
    await session.commit()
    return result.rowcount == 1


async def remove_favorite(session: AsyncSession, application_id: int, bullet_text: str) -> bool:
    """Unstar a bullet. Idempotent: repeating is harmless. Returns True if one was removed."""
    result = await session.execute(
        delete(FavoriteBullet).where(
            FavoriteBullet.application_id == application_id,
            FavoriteBullet.bullet_text == bullet_text,
        )
    )
    await session.commit()
    return result.rowcount > 0


async def list_favorites(
    session: AsyncSession,
    application_id: int,
) -> list[FavoriteBullet]:
    result = await session.execute(
        select(FavoriteBullet)
        .where(FavoriteBullet.application_id == application_id)
        .order_by(FavoriteBullet.created_at.desc())
    )
    return list(result.scalars().all())


async def list_all_favorites(
    session: AsyncSession,
) -> list[FavoriteBullet]:
    result = await session.execute(
        select(FavoriteBullet).order_by(
            FavoriteBullet.application_id,
            FavoriteBullet.created_at.desc(),
        )
    )
    return list(result.scalars().all())


async def edit_favorite(
    session: AsyncSession,
    application_id: int,
    old_text: str,
    new_text: str,
) -> bool:
    existing = await session.execute(
        select(FavoriteBullet).where(
            FavoriteBullet.application_id == application_id,
            FavoriteBullet.bullet_text == old_text,
        )
    )
    favorite = existing.scalar_one_or_none()
    if not favorite:
        return False
    favorite.bullet_text = new_text
    await session.commit()
    return True


async def get_favorited_texts(
    session: AsyncSession,
    application_id: int,
) -> set[str]:
    result = await session.execute(
        select(FavoriteBullet.bullet_text).where(FavoriteBullet.application_id == application_id)
    )
    return set(result.scalars().all())
