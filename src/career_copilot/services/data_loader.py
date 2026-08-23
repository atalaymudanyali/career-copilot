import json
from pathlib import Path

import frontmatter

from career_copilot.config import settings
from career_copilot.models.domain import CV, Project, SourceChunk


def load_cv(cv_path: Path | None = None) -> CV:
    path = cv_path or settings.cv_path
    with open(path) as f:
        return CV.model_validate(json.load(f))


def load_projects(projects_dir: Path | None = None) -> list[Project]:
    directory = projects_dir or settings.projects_dir
    projects = []
    for md_file in sorted(directory.glob("*.md")):
        post = frontmatter.load(str(md_file))
        projects.append(
            Project(
                id=post.metadata.get("id", md_file.stem),
                title=post.metadata.get("title", md_file.stem),
                tech=post.metadata.get("tech", []),
                date=str(post.metadata.get("date", "")),
                description=post.content.strip(),
            )
        )
    return projects


def build_source_chunks(cv: CV, projects: list[Project]) -> list[SourceChunk]:
    chunks = []

    for exp in cv.experience:
        if exp.context:
            chunks.append(
                SourceChunk(
                    source_id=f"{exp.id}:context",
                    source_type="cv_context",
                    content=f"[{exp.role} at {exp.company}] {exp.context}",
                )
            )
        for i, bullet in enumerate(exp.bullets):
            chunks.append(
                SourceChunk(
                    source_id=f"{exp.id}:bullet:{i}",
                    source_type="cv_bullet",
                    content=f"[{exp.role} at {exp.company}] {bullet}",
                )
            )

    for proj in projects:
        chunks.append(
            SourceChunk(
                source_id=f"project:{proj.id}",
                source_type="project_description",
                content=(
                    f"[Project: {proj.title} | Tech: {', '.join(proj.tech)}] {proj.description}"
                ),
            )
        )

    all_skills = []
    for category, skills in cv.skills.model_dump().items():
        if skills:
            all_skills.append(f"{category}: {', '.join(skills)}")
    if all_skills:
        chunks.append(
            SourceChunk(
                source_id="skills:all",
                source_type="skill",
                content=f"[Skills] {'; '.join(all_skills)}",
            )
        )

    return chunks
