import json

import pytest

from career_copilot.models.domain import CV, ContactInfo, Project, Skills
from career_copilot.services.skills import (
    build_skill_index,
    format_equivalents,
    load_equivalents,
    split_gaps,
)


def _index(equivalents=None):
    cv = CV(
        name="Test",
        contact=ContactInfo(email="t@example.com"),
        skills=Skills(
            languages=["Java", "C#", "SQL"],
            tools=["Docker", "Git", "Kafka/Redpanda"],
            ai_ml=["OpenAI API (GPT-4, Whisper, TTS)"],
        ),
    )
    projects = [Project(id="triage", title="AI Triage Pipeline", tech=["React", "Prometheus"])]
    return build_skill_index(
        cv, projects, equivalents or {"PostgreSQL": ["MySQL", "relational database"]}
    )


def _covered(gap, index=None):
    missing, covered = split_gaps([gap], index or _index())
    return covered[0].covered_by if covered else None


def test_skill_and_project_technologies_are_covered():
    assert _covered("Experience with Docker") == "Skills: Docker"
    assert _covered("Prometheus monitoring") == "Project: AI Triage Pipeline (Prometheus)"


def test_compound_skill_names_are_split():
    assert _covered("Redpanda or similar streaming platform") == "Skills: Kafka/Redpanda"
    assert _covered("Whisper speech-to-text") == "Skills: OpenAI API (GPT-4, Whisper, TTS)"


def test_equivalents_cover_alternatives_and_plurals():
    assert _covered("MySQL") == "Equivalent: PostgreSQL covers MySQL"
    assert _covered("Relational databases") == "Equivalent: PostgreSQL covers relational database"


@pytest.mark.parametrize(
    "gap",
    ["JavaScript frameworks", "Google Cloud", "GitHub Actions", "NoSQL databases", "AWS Lambda"],
)
def test_whole_word_matching_avoids_false_matches(gap):
    # Java ≠ JavaScript, Git ≠ GitHub, SQL ≠ NoSQL; AWS isn't covered by anything
    assert _covered(gap) is None


@pytest.mark.parametrize("gap", ["5+ years of Java experience", "3 years Docker", "Senior C# role"])
def test_experience_and_seniority_gaps_stay_gaps(gap):
    missing, covered = split_gaps([gap], _index())
    assert missing == [gap] and covered == []


def test_cloud_providers_are_real_gaps_again():
    missing, _ = split_gaps(["AWS", "Azure DevOps", "GCP"], _index())
    assert missing == ["AWS", "Azure DevOps", "GCP"]


def test_skills_win_over_equivalents_for_the_explanation():
    index = _index({"Something": ["Docker"]})
    assert index["docker"] == "Skills: Docker"


def test_load_equivalents_missing_file_is_empty(tmp_path):
    assert load_equivalents(tmp_path / "nope.json") == {}


def test_load_and_format_equivalents(tmp_path):
    path = tmp_path / "eq.json"
    path.write_text(json.dumps({"Kafka": ["RabbitMQ", "message broker"]}))
    equivalents = load_equivalents(path)
    assert format_equivalents(equivalents) == "- Kafka covers: RabbitMQ, message broker"


def test_real_data_files_load():
    from career_copilot.services.data_loader import load_cv, load_projects

    index = build_skill_index(load_cv(), load_projects(), load_equivalents())
    assert _covered("RabbitMQ", index).startswith("Equivalent: Kafka/Redpanda")
    assert _covered("Grafana dashboards", index).startswith("Project: Event-Driven AI Triage")
    assert _covered("AWS", index) is None
