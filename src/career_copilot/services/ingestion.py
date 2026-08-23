from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from career_copilot.models.db import Chunk
from career_copilot.services.data_loader import (
    build_source_chunks,
    load_cv,
    load_projects,
)
from career_copilot.services.llm import OllamaClient


async def ingest_chunks(session: AsyncSession) -> dict:
    cv = load_cv()
    projects = load_projects()
    source_chunks = build_source_chunks(cv, projects)

    texts = [chunk.content for chunk in source_chunks]
    client = OllamaClient()
    embeddings = await client.embed(texts)

    created = 0
    skipped = 0

    for chunk, embedding in zip(source_chunks, embeddings):
        existing = await session.execute(select(Chunk).where(Chunk.source_id == chunk.source_id))
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        db_chunk = Chunk(
            source_id=chunk.source_id,
            source_type=chunk.source_type,
            content=chunk.content,
            embedding=embedding,
        )
        session.add(db_chunk)
        created += 1

    await session.commit()

    return {
        "total_chunks": len(source_chunks),
        "created": created,
        "skipped": skipped,
    }
