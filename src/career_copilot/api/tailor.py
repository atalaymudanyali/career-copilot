from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from career_copilot.db import get_session
from career_copilot.models.domain import TailoringResult
from career_copilot.services.retrieval import retrieve
from career_copilot.services.tailoring import tailor_rag

router = APIRouter()


class TailorRequest(BaseModel):
    job_description: str


@router.post("/tailor")
async def tailor_endpoint(
    request: TailorRequest,
    session: AsyncSession = Depends(get_session),
) -> TailoringResult:
    chunks = await retrieve(request.job_description, session)
    return await tailor_rag(request.job_description, chunks)
