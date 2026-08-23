from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from career_copilot.db import get_session
from career_copilot.services.ingestion import ingest_chunks

router = APIRouter()


@router.post("/ingest")
async def ingest(session: AsyncSession = Depends(get_session)) -> dict:
    return await ingest_chunks(session)
