from career_copilot.models.domain import TailoredBullet, TailoringResult
from career_copilot.services.tailoring import validate_source_ids


def test_validate_source_ids_all_valid():
    bullets = [
        TailoredBullet(text="Built APIs", source_id="intern:bullet:0", relevance="high"),
        TailoredBullet(text="Used Docker", source_id="project:test", relevance="medium"),
    ]
    valid_ids = {"intern:bullet:0", "project:test", "skills:all"}

    valid, invalid = validate_source_ids(bullets, valid_ids)
    assert len(valid) == 2
    assert len(invalid) == 0


def test_validate_source_ids_drops_invalid():
    bullets = [
        TailoredBullet(text="Real bullet", source_id="intern:bullet:0", relevance="high"),
        TailoredBullet(text="Invented bullet", source_id="nonexistent:0", relevance="high"),
    ]
    valid_ids = {"intern:bullet:0"}

    valid, invalid = validate_source_ids(bullets, valid_ids)
    assert len(valid) == 1
    assert valid[0].text == "Real bullet"
    assert len(invalid) == 1
    assert invalid[0].source_id == "nonexistent:0"


def test_validate_source_ids_all_invalid():
    bullets = [
        TailoredBullet(text="Fake", source_id="fake:0", relevance="high"),
    ]
    valid_ids = {"real:0"}

    valid, invalid = validate_source_ids(bullets, valid_ids)
    assert len(valid) == 0
    assert len(invalid) == 1


def test_tailoring_result_parsing():
    raw = {
        "tailored_bullets": [
            {"text": "Built REST APIs", "source_id": "intern:bullet:0", "relevance": "high"},
        ],
        "why_i_fit": "Strong backend experience with API development.",
        "gaps": ["Kubernetes", "GraphQL"],
    }
    result = TailoringResult.model_validate(raw)
    assert len(result.tailored_bullets) == 1
    assert result.tailored_bullets[0].source_id == "intern:bullet:0"
    assert result.why_i_fit.startswith("Strong")
    assert "Kubernetes" in result.gaps


def test_tailoring_result_defaults():
    raw = {
        "tailored_bullets": [],
        "why_i_fit": "No strong match.",
    }
    result = TailoringResult.model_validate(raw)
    assert result.gaps == []
    assert result.tailored_bullets == []
