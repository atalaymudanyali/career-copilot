from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from career_copilot.models.domain import CV

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def load_cv() -> CV:
    cv_path = PROJECT_ROOT / "data" / "cv.json"
    return CV.model_validate_json(cv_path.read_text())


def generate_cv_pdf(tailoring_result: dict, company: str, role: str) -> bytes:
    from weasyprint import HTML

    cv = load_cv()

    bullets_by_source: dict[str, list[str]] = {}
    for bullet in tailoring_result.get("tailored_bullets", []):
        exp_id = bullet["source_id"].split(":")[0]
        bullets_by_source.setdefault(exp_id, []).append(bullet["text"])

    env = Environment(loader=FileSystemLoader(str(PROJECT_ROOT / "templates")), autoescape=True)
    template = env.get_template("cv/document.html")

    html_content = template.render(
        cv=cv,
        bullets_by_source=bullets_by_source,
        why_i_fit=tailoring_result.get("why_i_fit", ""),
        company=company,
        role=role,
    )

    return HTML(string=html_content).write_pdf()
