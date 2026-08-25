from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession

from career_copilot.db import get_session
from career_copilot.models.domain import ApplicationCreate
from career_copilot.services.applications import create_application, list_applications
from career_copilot.templating import templates

router = APIRouter(tags=["dashboard"])


@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@router.get("/dashboard")
async def dashboard_list(
    request: Request,
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    applications = await list_applications(session, status)
    return templates.TemplateResponse(
        request,
        "dashboard/list.html",
        {"applications": applications, "status_filter": status},
    )


@router.post("/dashboard")
async def dashboard_create(
    request: Request,
    company: str = Form(),
    role: str = Form(),
    jd_text: str = Form(),
    url: str | None = Form(None),
    notes: str | None = Form(None),
    session: AsyncSession = Depends(get_session),
):
    data = ApplicationCreate(company=company, role=role, jd_text=jd_text, url=url, notes=notes)
    application = await create_application(session, data)

    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        return templates.TemplateResponse(request, "dashboard/_app_row.html", {"app": application})

    return templates.TemplateResponse(
        request,
        "dashboard/list.html",
        {"applications": await list_applications(session)},
    )
