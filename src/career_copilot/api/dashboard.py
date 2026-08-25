from fastapi import APIRouter, Request

from career_copilot.templating import templates

router = APIRouter(tags=["dashboard"])


@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")
