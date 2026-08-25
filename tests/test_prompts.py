import json

from career_copilot.prompts.templates import (
    SYSTEM_PROMPT,
    build_user_prompt,
    build_user_prompt_with_fillers,
)


def test_system_prompt_contains_key_rules():
    assert "source_id" in SYSTEM_PROMPT
    assert "gaps" in SYSTEM_PROMPT
    assert "Never invent" in SYSTEM_PROMPT or "never invent" in SYSTEM_PROMPT.lower()


def test_system_prompt_contains_page_fill_rule():
    assert "PAGE FILL" in SYSTEM_PROMPT
    assert "EVERY" in SYSTEM_PROMPT


def test_build_user_prompt_includes_chunks_and_jd():
    chunks = json.dumps([{"source_id": "test:0", "content": "Built APIs"}])
    jd = "Looking for a Python developer"

    prompt = build_user_prompt(chunks, jd)
    assert "test:0" in prompt
    assert "Built APIs" in prompt
    assert "Python developer" in prompt
    assert "source_id" in prompt


def test_build_user_prompt_with_fillers_has_both_sections():
    relevant = json.dumps([{"source_id": "rel:0", "content": "FastAPI work"}])
    fillers = json.dumps([{"source_id": "fill:0", "content": "Spring Boot work"}])
    jd = "Python backend role"

    prompt = build_user_prompt_with_fillers(relevant, fillers, jd)
    assert "RELEVANT" in prompt
    assert "ADDITIONAL" in prompt
    assert "rel:0" in prompt
    assert "fill:0" in prompt
    assert "Python backend role" in prompt


def test_build_user_prompt_with_fillers_instructs_inclusion():
    relevant = json.dumps([{"source_id": "r:0", "content": "x"}])
    fillers = json.dumps([{"source_id": "f:0", "content": "y"}])

    prompt = build_user_prompt_with_fillers(relevant, fillers, "test jd")
    assert "MUST include" in prompt or "every source chunk" in prompt.lower()
