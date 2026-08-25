import pytest
from pydantic import ValidationError

from career_copilot.models.domain import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationStatus,
    ApplicationUpdate,
)


def test_application_status_values():
    assert ApplicationStatus.SAVED == "saved"
    assert ApplicationStatus.APPLIED == "applied"
    assert ApplicationStatus.INTERVIEWING == "interviewing"
    assert ApplicationStatus.OFFERED == "offered"
    assert ApplicationStatus.REJECTED == "rejected"


def test_application_create_valid():
    app = ApplicationCreate(
        company="Acme Corp",
        role="Backend Engineer",
        jd_text="Looking for a backend engineer...",
    )
    assert app.company == "Acme Corp"
    assert app.url is None
    assert app.notes is None


def test_application_create_missing_required():
    with pytest.raises(ValidationError):
        ApplicationCreate(company="Acme Corp")


def test_application_update_partial():
    update = ApplicationUpdate(status=ApplicationStatus.APPLIED)
    assert update.status == "applied"
    assert update.company is None
    assert update.role is None


def test_application_update_invalid_status():
    with pytest.raises(ValidationError):
        ApplicationUpdate(status="invalid_status")


def test_application_response_with_tailoring():
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    resp = ApplicationResponse(
        id=1,
        company="Acme Corp",
        role="Backend Engineer",
        status="saved",
        jd_text="Looking for...",
        url=None,
        notes=None,
        tailoring_result={
            "tailored_bullets": [
                {"text": "Built APIs", "source_id": "exp:bullet:0", "relevance": "high"}
            ],
            "why_i_fit": "Strong backend experience.",
            "gaps": ["Kubernetes"],
        },
        applied_at=None,
        created_at=now,
        updated_at=now,
    )
    assert resp.tailoring_result is not None
    assert len(resp.tailoring_result.tailored_bullets) == 1


def test_application_response_without_tailoring():
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    resp = ApplicationResponse(
        id=1,
        company="Test",
        role="Dev",
        status="saved",
        jd_text="JD text",
        url=None,
        notes=None,
        applied_at=None,
        created_at=now,
        updated_at=now,
    )
    assert resp.tailoring_result is None
