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
from career_copilot.services.favorites import (
    get_favorited_texts,
    list_all_favorites,
    list_favorites,
    toggle_favorite,
)
from career_copilot.services.pdf import generate_cv_pdf
from career_copilot.services.retrieval import retrieve
from career_copilot.services.tailoring import get_source_chunks, tailor_rag
from career_copilot.services.tailoring_versions import (
    create_version,
    delete_version,
    get_latest_version,
    get_version,
    list_versions,
)
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


@router.get("/dashboard/favorites")
async def dashboard_favorites(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    favorites = await list_all_favorites(session)
    apps_by_id: dict[int, object] = {}
    for fav in favorites:
        if fav.application_id not in apps_by_id:
            app = await get_application(session, fav.application_id)
            apps_by_id[fav.application_id] = app
    return templates.TemplateResponse(
        request,
        "dashboard/favorites.html",
        {"favorites": favorites, "apps_by_id": apps_by_id},
    )


@router.post("/dashboard/favorites/toggle")
async def dashboard_toggle_favorite(
    request: Request,
    application_id: int = Form(),
    bullet_text: str = Form(),
    source_id: str = Form(),
    relevance: str = Form("medium"),
    session: AsyncSession = Depends(get_session),
):
    is_favorited = await toggle_favorite(session, application_id, bullet_text, source_id, relevance)
    return templates.TemplateResponse(
        request,
        "dashboard/_bullet_star.html",
        {
            "bullet": {
                "text": bullet_text,
                "source_id": source_id,
                "relevance": relevance,
            },
            "app_id": application_id,
            "is_favorited": is_favorited,
        },
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
    versions = await list_versions(session, application_id)
    favorited = await get_favorited_texts(session, application_id)
    return templates.TemplateResponse(
        request,
        "dashboard/detail.html",
        {
            "app": application,
            "statuses": statuses,
            "versions": versions,
            "favorited_texts": favorited,
        },
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
    versions = await list_versions(session, application_id)
    favorited = await get_favorited_texts(session, application_id)
    ctx = {
        "app": application,
        "statuses": statuses,
        "versions": versions,
        "favorited_texts": favorited,
    }
    return templates.TemplateResponse(request, "dashboard/detail.html", ctx)


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
    result_dict = result.model_dump()
    await store_tailoring_result(session, application, result_dict)
    version = await create_version(session, application.id, result_dict)

    is_htmx = request.headers.get("HX-Request") == "true"
    versions = await list_versions(session, application.id)
    favorited = await get_favorited_texts(session, application_id)
    if is_htmx:
        return templates.TemplateResponse(
            request,
            "dashboard/_tailoring_result.html",
            {
                "app": application,
                "version": version,
                "versions": versions,
                "favorited_texts": favorited,
            },
        )

    statuses = [s.value for s in ApplicationStatus]
    return templates.TemplateResponse(
        request,
        "dashboard/detail.html",
        {
            "app": application,
            "statuses": statuses,
            "versions": versions,
            "favorited_texts": favorited,
        },
    )


@router.post("/dashboard/{application_id}/notes/add")
async def dashboard_add_note(
    request: Request,
    application_id: int,
    note_text: str = Form(),
    session: AsyncSession = Depends(get_session),
):
    application = await get_application(session, application_id)
    if not application:
        return HTMLResponse("Not found", status_code=404)

    note_text = note_text.strip()
    if note_text:
        existing = application.notes or ""
        new_notes = f"{existing}\n{note_text}" if existing.strip() else note_text
        data = ApplicationUpdate(notes=new_notes)
        application = await update_application(session, application, data)

    return templates.TemplateResponse(
        request, "dashboard/_notes_section.html", {"app": application}
    )


@router.post("/dashboard/{application_id}/notes/remove")
async def dashboard_remove_note(
    request: Request,
    application_id: int,
    note_index: int = Form(),
    session: AsyncSession = Depends(get_session),
):
    application = await get_application(session, application_id)
    if not application:
        return HTMLResponse("Not found", status_code=404)

    lines = (application.notes or "").split("\n")
    notes = [n for n in lines if n.strip()]
    if 0 <= note_index < len(notes):
        notes.pop(note_index)

    new_notes = "\n".join(notes) if notes else None
    data = ApplicationUpdate(notes=new_notes)
    application = await update_application(session, application, data)

    return templates.TemplateResponse(
        request, "dashboard/_notes_section.html", {"app": application}
    )


@router.get("/dashboard/{application_id}/starred")
async def dashboard_starred_bullets(
    request: Request,
    application_id: int,
    session: AsyncSession = Depends(get_session),
):
    application = await get_application(session, application_id)
    if not application:
        return HTMLResponse("Not found", status_code=404)

    favorites = await list_favorites(session, application_id)
    versions = await list_versions(session, application_id)

    starred_result = {
        "tailored_bullets": [
            {"text": f.bullet_text, "source_id": f.source_id, "relevance": f.relevance}
            for f in favorites
        ],
    }
    if versions:
        latest = versions[0]
        if latest.tailoring_result:
            starred_result["why_i_fit"] = latest.tailoring_result.get("why_i_fit", "")
            starred_result["gaps"] = latest.tailoring_result.get("gaps", [])

    active_fit = starred_result.get("why_i_fit", "")
    version_fits = []
    for v in reversed(versions):
        if v.tailoring_result:
            version_fits.append(
                {
                    "version_number": v.version_number,
                    "version_id": v.id,
                    "why_i_fit": v.tailoring_result.get("why_i_fit", ""),
                    "gaps": v.tailoring_result.get("gaps", []),
                    "is_active": v.tailoring_result.get("why_i_fit", "") == active_fit,
                }
            )

    application.tailoring_result = starred_result
    favorited = await get_favorited_texts(session, application_id)
    return templates.TemplateResponse(
        request,
        "dashboard/_tailoring_result.html",
        {
            "app": application,
            "version": None,
            "versions": versions,
            "favorited_texts": favorited,
            "is_starred_view": True,
            "version_fits": version_fits,
        },
    )


@router.post("/dashboard/{application_id}/use-fit/{version_id}")
async def dashboard_use_fit(
    request: Request,
    application_id: int,
    version_id: int,
    session: AsyncSession = Depends(get_session),
):
    application = await get_application(session, application_id)
    if not application:
        return HTMLResponse("Not found", status_code=404)

    version = await get_version(session, version_id)
    if not version or version.application_id != application_id:
        return HTMLResponse("Version not found", status_code=404)

    result = dict(application.tailoring_result or {})
    result["why_i_fit"] = version.tailoring_result.get("why_i_fit", "")
    result["gaps"] = version.tailoring_result.get("gaps", [])
    await store_tailoring_result(session, application, result)

    favorites = await list_favorites(session, application_id)
    versions = await list_versions(session, application_id)

    starred_result = {
        "tailored_bullets": [
            {"text": f.bullet_text, "source_id": f.source_id, "relevance": f.relevance}
            for f in favorites
        ],
        "why_i_fit": result["why_i_fit"],
        "gaps": result["gaps"],
    }

    version_fits = []
    for v in reversed(versions):
        if v.tailoring_result:
            version_fits.append(
                {
                    "version_number": v.version_number,
                    "version_id": v.id,
                    "why_i_fit": v.tailoring_result.get("why_i_fit", ""),
                    "gaps": v.tailoring_result.get("gaps", []),
                    "is_active": v.tailoring_result.get("why_i_fit", "") == result["why_i_fit"],
                }
            )

    application.tailoring_result = starred_result
    favorited = await get_favorited_texts(session, application_id)
    return templates.TemplateResponse(
        request,
        "dashboard/_tailoring_result.html",
        {
            "app": application,
            "version": None,
            "versions": versions,
            "favorited_texts": favorited,
            "is_starred_view": True,
            "version_fits": version_fits,
        },
    )


@router.get("/dashboard/{application_id}/versions/{version_id}")
async def dashboard_version_detail(
    request: Request,
    application_id: int,
    version_id: int,
    session: AsyncSession = Depends(get_session),
):
    application = await get_application(session, application_id)
    if not application:
        return HTMLResponse("Not found", status_code=404)

    version = await get_version(session, version_id)
    if not version or version.application_id != application_id:
        return HTMLResponse("Version not found", status_code=404)

    versions = await list_versions(session, application_id)
    application.tailoring_result = version.tailoring_result

    favorited = await get_favorited_texts(session, application_id)
    return templates.TemplateResponse(
        request,
        "dashboard/_tailoring_result.html",
        {
            "app": application,
            "version": version,
            "versions": versions,
            "favorited_texts": favorited,
        },
    )


@router.delete("/dashboard/{application_id}/versions/{version_id}")
async def dashboard_delete_version(
    request: Request,
    application_id: int,
    version_id: int,
    session: AsyncSession = Depends(get_session),
):
    application = await get_application(session, application_id)
    if not application:
        return HTMLResponse("Not found", status_code=404)

    version = await get_version(session, version_id)
    if not version or version.application_id != application_id:
        return HTMLResponse("Version not found", status_code=404)

    await delete_version(session, version)

    latest = await get_latest_version(session, application_id)
    if latest:
        await store_tailoring_result(session, application, latest.tailoring_result)
        versions = await list_versions(session, application_id)
        favorited = await get_favorited_texts(session, application_id)
        return templates.TemplateResponse(
            request,
            "dashboard/_tailoring_result.html",
            {
                "app": application,
                "version": latest,
                "versions": versions,
                "favorited_texts": favorited,
            },
        )

    await store_tailoring_result(session, application, None)
    return templates.TemplateResponse(
        request, "dashboard/_tailor_button.html", {"app": application}
    )


@router.get("/dashboard/{application_id}/cv.pdf")
async def download_cv_pdf(
    application_id: int,
    session: AsyncSession = Depends(get_session),
):
    application = await get_application(session, application_id)
    if not application or not application.tailoring_result:
        return HTMLResponse("Application not found or not yet tailored", status_code=404)

    favorited = await get_favorited_texts(session, application_id)
    pdf_bytes = generate_cv_pdf(
        application.tailoring_result,
        application.company,
        application.role,
        favorite_texts=set(favorited),
    )
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
