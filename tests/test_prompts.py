import json

from career_copilot.prompts.templates import SYSTEM_PROMPT, build_user_prompt


def test_system_prompt_contains_key_rules():
    assert "source_id" in SYSTEM_PROMPT
    assert "gaps" in SYSTEM_PROMPT
    assert "Never invent" in SYSTEM_PROMPT or "never invent" in SYSTEM_PROMPT.lower()


def test_build_user_prompt_includes_chunks_and_jd():
    chunks = json.dumps([{"source_id": "test:0", "content": "Built APIs"}])
    jd = "Looking for a Python developer"

    prompt = build_user_prompt(chunks, jd)
    assert "test:0" in prompt
    assert "Built APIs" in prompt
    assert "Python developer" in prompt
    assert "source_id" in prompt
