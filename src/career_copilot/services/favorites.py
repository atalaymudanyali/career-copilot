from sqlalchemy import select
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


async def get_favorited_texts(
    session: AsyncSession,
    application_id: int,
) -> set[str]:
    result = await session.execute(
        select(FavoriteBullet.bullet_text).where(FavoriteBullet.application_id == application_id)
    )
    return set(result.scalars().all())
