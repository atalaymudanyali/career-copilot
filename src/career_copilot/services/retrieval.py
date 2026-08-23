from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from career_copilot.models.db import Chunk
from career_copilot.models.domain import SourceChunk
from career_copilot.services.llm import OllamaClient


async def retrieve(
    jd_text: str,
    session: AsyncSession,
    k: int = 15,
) -> list[SourceChunk]:
    client = OllamaClient()
    [jd_embedding] = await client.embed([jd_text])

    result = await session.execute(
        select(Chunk).order_by(Chunk.embedding.cosine_distance(jd_embedding)).limit(k)
    )
    chunks = result.scalars().all()

    return [
        SourceChunk(
            source_id=c.source_id,
            source_type=c.source_type,
            content=c.content,
        )
        for c in chunks
    ]
