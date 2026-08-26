from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from career_copilot.models.db import TailoringVersion


async def create_version(
    session: AsyncSession, application_id: int, tailoring_result: dict
) -> TailoringVersion:
    max_version = await session.execute(
        select(func.max(TailoringVersion.version_number)).where(
            TailoringVersion.application_id == application_id
        )
    )
    current_max = max_version.scalar() or 0

    version = TailoringVersion(
        application_id=application_id,
        version_number=current_max + 1,
        tailoring_result=tailoring_result,
    )
    session.add(version)
    await session.commit()
    await session.refresh(version)
    return version


async def list_versions(
    session: AsyncSession, application_id: int
) -> list[TailoringVersion]:
    result = await session.execute(
        select(TailoringVersion)
        .where(TailoringVersion.application_id == application_id)
        .order_by(TailoringVersion.version_number.desc())
    )
    return list(result.scalars().all())


async def get_version(
    session: AsyncSession, version_id: int
) -> TailoringVersion | None:
    result = await session.execute(
        select(TailoringVersion).where(TailoringVersion.id == version_id)
    )
    return result.scalar_one_or_none()


async def get_latest_version(
    session: AsyncSession, application_id: int
) -> TailoringVersion | None:
    result = await session.execute(
        select(TailoringVersion)
        .where(TailoringVersion.application_id == application_id)
        .order_by(TailoringVersion.version_number.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
