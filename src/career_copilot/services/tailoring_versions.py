from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from career_copilot.models.db import Application, TailoringVersion


async def create_version(
    session: AsyncSession, application_id: int, tailoring_result: dict
) -> TailoringVersion:
    # Lock the parent application row so concurrent calls number versions one at a time;
    # without it, two requests can both read the same MAX and create duplicate numbers.
    # The lock is released when the transaction commits below.
    await session.execute(
        select(Application.id).where(Application.id == application_id).with_for_update()
    )
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


async def list_versions(session: AsyncSession, application_id: int) -> list[TailoringVersion]:
    result = await session.execute(
        select(TailoringVersion)
        .where(TailoringVersion.application_id == application_id)
        .order_by(TailoringVersion.version_number.desc())
    )
    return list(result.scalars().all())


async def get_version(session: AsyncSession, version_id: int) -> TailoringVersion | None:
    result = await session.execute(
        select(TailoringVersion).where(TailoringVersion.id == version_id)
    )
    return result.scalar_one_or_none()


async def delete_version(session: AsyncSession, version: TailoringVersion) -> None:
    await session.delete(version)
    await session.commit()


async def get_latest_version(session: AsyncSession, application_id: int) -> TailoringVersion | None:
    result = await session.execute(
        select(TailoringVersion)
        .where(TailoringVersion.application_id == application_id)
        .order_by(TailoringVersion.version_number.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
