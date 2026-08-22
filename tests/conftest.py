from pathlib import Path

import pytest


@pytest.fixture
def data_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_jd() -> str:
    return """
    We are looking for a Backend Developer with experience in:
    - Python, FastAPI or Django
    - PostgreSQL and Redis
    - Docker and Kubernetes
    - REST API design
    - CI/CD pipelines
    - Experience with LLMs/AI integration is a plus
    - Strong communication skills
    """
