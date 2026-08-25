from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from career_copilot.db import get_session
from career_copilot.models.domain import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
)
from career_copilot.services.applications import (
    create_application,
    delete_application,
    get_application,
    list_applications,
    update_application,
)

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.post("", status_code=201, response_model=ApplicationResponse)
async def create(data: ApplicationCreate, session: AsyncSession = Depends(get_session)):
    application = await create_application(session, data)
    return application


@router.get("", response_model=list[ApplicationResponse])
async def list_all(status: str | None = None, session: AsyncSession = Depends(get_session)):
    return await list_applications(session, status)


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_by_id(application_id: int, session: AsyncSession = Depends(get_session)):
    application = await get_application(session, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.patch("/{application_id}", response_model=ApplicationResponse)
async def update(
    application_id: int,
    data: ApplicationUpdate,
    session: AsyncSession = Depends(get_session),
):
    application = await get_application(session, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return await update_application(session, application, data)


@router.delete("/{application_id}", status_code=204)
async def delete(application_id: int, session: AsyncSession = Depends(get_session)):
    application = await get_application(session, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    await delete_application(session, application)
