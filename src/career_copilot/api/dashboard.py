from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from career_copilot.db import get_session
from career_copilot.models.domain import ApplicationCreate, ApplicationStatus, ApplicationUpdate
from career_copilot.services.applications import (
    create_application,
    delete_application,
    get_application,
    list_applications,
    store_tailoring_result,
    update_application,
)
from career_copilot.services.pdf import generate_cv_pdf
from career_copilot.services.retrieval import retrieve
from career_copilot.services.tailoring import get_source_chunks, tailor_rag
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


@router.get("/dashboard/pipeline")
async def dashboard_pipeline(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    all_apps = await list_applications(session)
    statuses = [s.value for s in ApplicationStatus]
    apps_by_status: dict[str, list] = {s: [] for s in statuses}
    for app in all_apps:
        if app.status in apps_by_status:
            apps_by_status[app.status].append(app)
    return templates.TemplateResponse(
        request,
        "dashboard/pipeline.html",
        {"statuses": statuses, "apps_by_status": apps_by_status},
    )


@router.get("/dashboard/{application_id}")
async def dashboard_detail(
    request: Request,
    application_id: int,
    session: AsyncSession = Depends(get_session),
):
    application = await get_application(session, application_id)
    if not application:
        return templates.TemplateResponse(request, "dashboard/404.html", status_code=404)
    statuses = [s.value for s in ApplicationStatus]
    return templates.TemplateResponse(
        request, "dashboard/detail.html", {"app": application, "statuses": statuses}
    )


@router.patch("/dashboard/{application_id}")
async def dashboard_update(
    request: Request,
    application_id: int,
    session: AsyncSession = Depends(get_session),
):
    application = await get_application(session, application_id)
    if not application:
        return HTMLResponse("Not found", status_code=404)

    form_data = await request.form()
    update_fields = {}
    for field in ("status", "notes", "company", "role", "jd_text", "url"):
        if field in form_data:
            value = form_data[field]
            update_fields[field] = value if value != "" else None

    data = ApplicationUpdate(**update_fields)
    application = await update_application(session, application, data)

    statuses = [s.value for s in ApplicationStatus]
    return templates.TemplateResponse(
        request, "dashboard/detail.html", {"app": application, "statuses": statuses}
    )


@router.post("/dashboard/{application_id}/tailor")
async def dashboard_tailor(
    request: Request,
    application_id: int,
    session: AsyncSession = Depends(get_session),
):
    application = await get_application(session, application_id)
    if not application:
        return HTMLResponse("Not found", status_code=404)

    chunks = await retrieve(application.jd_text, session)
    all_chunks = get_source_chunks()
    retrieved_ids = {c.source_id for c in chunks}
    filler_chunks = [c for c in all_chunks if c.source_id not in retrieved_ids]
    result = await tailor_rag(application.jd_text, chunks, filler_chunks=filler_chunks)
    await store_tailoring_result(session, application, result.model_dump())

    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        return templates.TemplateResponse(
            request, "dashboard/_tailoring_result.html", {"app": application}
        )

    statuses = [s.value for s in ApplicationStatus]
    return templates.TemplateResponse(
        request, "dashboard/detail.html", {"app": application, "statuses": statuses}
    )


@router.get("/dashboard/{application_id}/cv.pdf")
async def download_cv_pdf(
    application_id: int,
    session: AsyncSession = Depends(get_session),
):
    application = await get_application(session, application_id)
    if not application or not application.tailoring_result:
        return HTMLResponse("Application not found or not yet tailored", status_code=404)

    pdf_bytes = generate_cv_pdf(application.tailoring_result, application.company, application.role)
    filename = f"CV_{application.company}_{application.role}.pdf".replace(" ", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.delete("/dashboard/{application_id}")
async def dashboard_delete(
    application_id: int,
    session: AsyncSession = Depends(get_session),
):
    application = await get_application(session, application_id)
    if application:
        await delete_application(session, application)
    return RedirectResponse(url="/dashboard", status_code=303)
