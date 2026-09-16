import json
import logging

from career_copilot.models.domain import (
    SourceChunk,
    TailoredBullet,
    TailoringResult,
)
from career_copilot.prompts.templates import (
    SYSTEM_PROMPT,
    build_user_prompt,
    build_user_prompt_with_fillers,
)
from career_copilot.services.data_loader import build_source_chunks, load_cv, load_projects
from career_copilot.services.llm import OllamaClient
from career_copilot.services.pdf import PERMANENT_PROJECTS

logger = logging.getLogger(__name__)

_NOT_A_GAP_KEYWORDS: set[str] = set()


def _build_gap_keywords() -> set[str]:
    if _NOT_A_GAP_KEYWORDS:
        return _NOT_A_GAP_KEYWORDS
    for proj in PERMANENT_PROJECTS:
        for tech in proj["tech"].split(", "):
            _NOT_A_GAP_KEYWORDS.add(tech.lower())
    _NOT_A_GAP_KEYWORDS.update([
        "solid", "tdd", "test-driven", "ci/cd", "ci cd",
        "github actions", "event-driven", "event driven",
        "message broker", "message queue",
    ])
    return _NOT_A_GAP_KEYWORDS


def filter_gaps(gaps: list[str]) -> list[str]:
    keywords = _build_gap_keywords()
    filtered = []
    for gap in gaps:
        gap_lower = gap.lower()
        if any(kw in gap_lower for kw in keywords):
            logger.info("Filtered gap (candidate has this): %s", gap)
            continue
        filtered.append(gap)
    return filtered


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
        gaps=filter_gaps(result.gaps),
    )


async def tailor_rag(
    job_description: str,
    chunks: list[SourceChunk],
    client: OllamaClient | None = None,
    filler_chunks: list[SourceChunk] | None = None,
) -> TailoringResult:
    llm = client or OllamaClient()

    all_chunks = chunks + (filler_chunks or [])
    valid_source_ids = {chunk.source_id for chunk in all_chunks}

    chunks_json = json.dumps(
        [chunk.model_dump() for chunk in chunks],
        indent=2,
    )

    if filler_chunks:
        filler_json = json.dumps(
            [chunk.model_dump() for chunk in filler_chunks],
            indent=2,
        )
        user_prompt = build_user_prompt_with_fillers(chunks_json, filler_json, job_description)
    else:
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
        gaps=filter_gaps(result.gaps),
    )


def get_source_chunks() -> list[SourceChunk]:
    cv = load_cv()
    projects = load_projects()
    return build_source_chunks(cv, projects)
