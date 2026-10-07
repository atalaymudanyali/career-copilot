"""Decide which reported gaps are real, using the candidate's own data.

Known technologies come from cv.json skills and every project's `tech:` list, plus a
user-editable data/skill_equivalents.json for "close enough" skills (Kafka covers
RabbitMQ). Gaps that match are not hidden: they're returned as covered, with the
reason, so the user can see and correct a wrong match.
"""

import json
import re
from functools import lru_cache
from pathlib import Path

from career_copilot.config import settings
from career_copilot.models.domain import CV, CoveredGap, Project

# Years or seniority are real gaps even when they name a skill the candidate has:
# "5+ years of Python" mentions Python but is still an experience gap.
_EXPERIENCE_GAP = re.compile(r"\b\d+\s*\+?\s*(?:years?|yrs)\b|\bsenior(?:ity)?\b", re.IGNORECASE)


def load_equivalents(path: Path | None = None) -> dict[str, list[str]]:
    path = path or settings.skill_equivalents_path
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {key: list(alternatives) for key, alternatives in data.items()}


def _terms(name: str) -> list[str]:
    """'Kafka/Redpanda' -> ['Kafka/Redpanda', 'Kafka', 'Redpanda'];
    'OpenAI API (GPT-4, Whisper, TTS)' -> ['OpenAI API (...)', 'OpenAI API', 'GPT-4', ...]."""
    parts = [name, *re.split(r"[/(),]", name)]
    return [part.strip() for part in parts if len(part.strip()) >= 2]


def build_skill_index(
    cv: CV, projects: list[Project], equivalents: dict[str, list[str]]
) -> dict[str, str]:
    """Map each matchable term (lowercase) to a human-readable reason it's covered.

    Earlier sources win, so a term in your skills is explained as a skill, not as a
    project technology or an equivalent.
    """
    index: dict[str, str] = {}

    def add(name: str, reason: str) -> None:
        for term in _terms(name):
            index.setdefault(term.lower(), reason)

    for items in cv.skills.model_dump().values():
        for skill in items:
            add(skill, f"Skills: {skill}")
    for project in projects:
        for tech in project.tech:
            add(tech, f"Project: {project.title} ({tech})")
    for covered_by, alternatives in equivalents.items():
        for alternative in alternatives:
            add(alternative, f"Equivalent: {covered_by} covers {alternative}")
    return index


@lru_cache(maxsize=512)
def _term_pattern(term: str) -> re.Pattern:
    # Whole-word match with an optional plural: "Java" doesn't match "JavaScript",
    # "Go" doesn't match "Google", but "message broker" matches "message brokers".
    return re.compile(rf"(?<!\w){re.escape(term)}(?:e?s)?(?!\w)", re.IGNORECASE)


def split_gaps(gaps: list[str], index: dict[str, str]) -> tuple[list[str], list[CoveredGap]]:
    """Separate real gaps from ones the candidate's data already covers."""
    terms = sorted(index, key=len, reverse=True)  # most specific match explains best
    missing: list[str] = []
    covered: list[CoveredGap] = []
    for gap in gaps:
        if _EXPERIENCE_GAP.search(gap):
            missing.append(gap)
            continue
        match = next((term for term in terms if _term_pattern(term).search(gap)), None)
        if match is None:
            missing.append(gap)
        else:
            covered.append(CoveredGap(gap=gap, covered_by=index[match]))
    return missing, covered


def format_equivalents(equivalents: dict[str, list[str]]) -> str:
    return "\n".join(
        f"- {covered_by} covers: {', '.join(alternatives)}"
        for covered_by, alternatives in equivalents.items()
    )
