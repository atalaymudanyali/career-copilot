from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from career_copilot.models.db import Application
from career_copilot.models.domain import ApplicationCreate, ApplicationUpdate


async def create_application(session: AsyncSession, data: ApplicationCreate) -> Application:
    application = Application(**data.model_dump())
    session.add(application)
    await session.commit()
    await session.refresh(application)
    return application


async def list_applications(session: AsyncSession, status: str | None = None) -> list[Application]:
    query = select(Application).order_by(Application.created_at.desc())
    if status:
        query = query.where(Application.status == status)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_application(session: AsyncSession, application_id: int) -> Application | None:
    result = await session.execute(select(Application).where(Application.id == application_id))
    return result.scalar_one_or_none()


async def update_application(
    session: AsyncSession, application: Application, data: ApplicationUpdate
) -> Application:
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(application, field, value)
    await session.commit()
    await session.refresh(application)
    return application


async def delete_application(session: AsyncSession, application: Application) -> None:
    await session.delete(application)
    await session.commit()
