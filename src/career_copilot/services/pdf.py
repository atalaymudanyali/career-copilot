from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from career_copilot.models.domain import CV

PROJECT_ROOT = Path(__file__).resolve().parents[3]

MAX_BULLETS_PER_EXPERIENCE = 4

PERMANENT_PROJECTS = [
    {
        "title": "Career Copilot",
        "tech": "Python, FastAPI, PostgreSQL, pgvector, Docker, MCP",
        "bullets": [
            "Built an AI career tool using RAG with pgvector semantic search that"
            " tailors CV bullets to job descriptions while enforcing source"
            " traceability on every output through structured validation",
            "Full-stack containerized application: FastAPI, PostgreSQL + pgvector,"
            " async SQLAlchemy, HTMX dashboard with versioning and favorites,"
            " PDF export, and an MCP server with 14 tools for use from"
            " Claude Desktop",
        ],
    },
]


def load_cv() -> CV:
    cv_path = PROJECT_ROOT / "data" / "cv.json"
    return CV.model_validate_json(cv_path.read_text())


def generate_cv_pdf(
    tailoring_result: dict,
    company: str,
    role: str,
    favorite_texts: set[str] | None = None,
    composed: bool = False,
) -> bytes:
    from weasyprint import HTML

    cv = load_cv()
    favorite_texts = favorite_texts or set()

    bullets_by_source: dict[str, list[str]] = {}
    project_bullets: list[str] = []

    all_bullets = tailoring_result.get("tailored_bullets", [])

    if composed:
        for bullet in all_bullets:
            source_id = bullet["source_id"]
            parts = source_id.split(":")
            if parts[0] == "project":
                continue
            if parts[0] == "custom":
                if bullet["text"] not in project_bullets:
                    project_bullets.append(bullet["text"])
            else:
                exp_id = parts[0]
                if exp_id not in bullets_by_source:
                    bullets_by_source[exp_id] = []
                if bullet["text"] not in bullets_by_source[exp_id]:
                    bullets_by_source[exp_id].append(bullet["text"])
    else:
        relevance_order = {"high": 0, "medium": 1, "low": 2}
        sorted_bullets = sorted(
            all_bullets, key=lambda b: relevance_order.get(b.get("relevance", "medium"), 1)
        )

        fav_bullets = [b for b in sorted_bullets if b["text"] in favorite_texts]
        rest_bullets = [b for b in sorted_bullets if b["text"] not in favorite_texts]

        for bullet in fav_bullets + rest_bullets:
            is_fav = bullet["text"] in favorite_texts
            if not is_fav and bullet.get("relevance", "medium") == "low":
                continue
            source_id = bullet["source_id"]
            parts = source_id.split(":")
            if parts[0] == "project":
                continue
            exp_id = parts[0]
            if exp_id not in bullets_by_source:
                bullets_by_source[exp_id] = []
            if len(bullets_by_source[exp_id]) < MAX_BULLETS_PER_EXPERIENCE:
                if bullet["text"] not in bullets_by_source[exp_id]:
                    bullets_by_source[exp_id].append(bullet["text"])

    env = Environment(loader=FileSystemLoader(str(PROJECT_ROOT / "templates")), autoescape=True)
    template = env.get_template("cv/document.html")

    html_content = template.render(
        cv=cv,
        bullets_by_source=bullets_by_source,
        project_bullets=project_bullets,
        permanent_projects=PERMANENT_PROJECTS,
        why_i_fit=tailoring_result.get("why_i_fit", ""),
        company=company,
        role=role,
    )

    return HTML(string=html_content).write_pdf()
