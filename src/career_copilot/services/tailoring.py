import json
import logging

from career_copilot.models.domain import (
    SourceChunk,
    TailoredBullet,
    TailoringResult,
)
from career_copilot.prompts.templates import SYSTEM_PROMPT, build_user_prompt
from career_copilot.services.data_loader import build_source_chunks, load_cv, load_projects
from career_copilot.services.llm import OllamaClient

logger = logging.getLogger(__name__)


def validate_source_ids(
    bullets: list[TailoredBullet],
    valid_ids: set[str],
) -> tuple[list[TailoredBullet], list[TailoredBullet]]:
    valid = []
    invalid = []
    for bullet in bullets:
        if bullet.source_id in valid_ids:
            valid.append(bullet)
        else:
            invalid.append(bullet)
    return valid, invalid


async def tailor(job_description: str, client: OllamaClient | None = None) -> TailoringResult:
    llm = client or OllamaClient()

    cv = load_cv()
    projects = load_projects()
    chunks = build_source_chunks(cv, projects)

    valid_source_ids = {chunk.source_id for chunk in chunks}

    chunks_json = json.dumps(
        [chunk.model_dump() for chunk in chunks],
        indent=2,
    )
    user_prompt = build_user_prompt(chunks_json, job_description)

    raw_response = await llm.chat(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        json_mode=True,
    )

    result = TailoringResult.model_validate(raw_response)

    valid_bullets, invalid_bullets = validate_source_ids(result.tailored_bullets, valid_source_ids)
    for bullet in invalid_bullets:
        logger.warning(
            "Dropped bullet with unresolvable source_id '%s': %s",
            bullet.source_id,
            bullet.text,
        )

    return TailoringResult(
        tailored_bullets=valid_bullets,
        why_i_fit=result.why_i_fit,
        gaps=result.gaps,
    )


def get_source_chunks() -> list[SourceChunk]:
    cv = load_cv()
    projects = load_projects()
    return build_source_chunks(cv, projects)
