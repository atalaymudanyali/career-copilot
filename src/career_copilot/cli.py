import asyncio
import sys
from pathlib import Path

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from career_copilot.models.domain import TailoringResult
from career_copilot.services.llm import OllamaClient
from career_copilot.services.tailoring import get_source_chunks, tailor

app = typer.Typer(
    name="career-copilot",
    help="AI-powered CV tailoring grounded in real experience.",
    no_args_is_help=True,
)
console = Console()


def render_result(result: TailoringResult) -> None:
    console.print()

    table = Table(title="Tailored Bullets", show_lines=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Bullet", ratio=3)
    table.add_column("Source", style="cyan", ratio=1)
    table.add_column("Relevance", justify="center", width=10)

    relevance_colors = {"high": "green", "medium": "yellow", "low": "red"}
    for i, bullet in enumerate(result.tailored_bullets, 1):
        color = relevance_colors.get(bullet.relevance, "white")
        table.add_row(
            str(i),
            bullet.text,
            bullet.source_id,
            Text(bullet.relevance.upper(), style=color),
        )
    console.print(table)

    console.print()
    console.print(Panel(result.why_i_fit, title="Why I Fit", border_style="blue"))

    if result.gaps:
        console.print()
        gap_table = Table(title="Skill Gaps (not in my experience)", show_lines=True)
        gap_table.add_column("Missing Skill/Requirement", style="red")
        for gap in result.gaps:
            gap_table.add_row(gap)
        console.print(gap_table)


def _read_jd(jd: Path | None) -> str:
    if jd:
        return jd.read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    console.print(
        "[yellow]Paste the job description below, then press Ctrl+Z and Enter (EOF):[/yellow]"
    )
    return sys.stdin.read()


def _tailor_via_api(job_description: str, api_url: str) -> TailoringResult:
    response = httpx.post(
        f"{api_url.rstrip('/')}/tailor",
        json={"job_description": job_description},
        timeout=120.0,
    )
    response.raise_for_status()
    return TailoringResult.model_validate(response.json())


@app.command("tailor")
def tailor_cmd(
    jd: Path | None = typer.Option(
        None,
        "--jd",
        "-j",
        help="Path to job description file. If omitted, reads from stdin.",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="Override the Ollama model to use.",
    ),
    api: bool = typer.Option(
        False,
        "--api",
        help="Use the FastAPI backend instead of local inference.",
    ),
    api_url: str = typer.Option(
        "http://localhost:8000",
        "--api-url",
        help="Base URL of the Career Copilot API.",
    ),
) -> None:
    """Tailor CV bullets to a job description."""
    job_description = _read_jd(jd).strip()
    if not job_description:
        console.print("[red]Error: empty job description.[/red]")
        raise typer.Exit(1)

    if api:
        with console.status("[bold green]Calling API...[/bold green]"):
            try:
                result = _tailor_via_api(job_description, api_url)
            except httpx.HTTPError as e:
                console.print(f"[red]API error: {e}[/red]")
                raise typer.Exit(1)
    else:
        client = OllamaClient(model=model) if model else None

        with console.status("[bold green]Checking Ollama connection...[/bold green]"):
            llm = client or OllamaClient()
            healthy = asyncio.run(llm.health_check())
            if not healthy:
                console.print(
                    f"[red]Error: cannot connect to Ollama at {llm.base_url}. Is it running?[/red]"
                )
                raise typer.Exit(1)

        with console.status(
            "[bold green]Tailoring your CV... (this may take a moment)[/bold green]"
        ):
            result = asyncio.run(tailor(job_description, client=client))

    render_result(result)


@app.command()
def chunks() -> None:
    """Show all source chunks that the LLM can reference."""
    source_chunks = get_source_chunks()

    table = Table(title="Source Chunks", show_lines=True)
    table.add_column("Source ID", style="cyan", ratio=1)
    table.add_column("Type", style="dim", width=20)
    table.add_column("Content", ratio=3)

    for chunk in source_chunks:
        table.add_row(chunk.source_id, chunk.source_type, chunk.content)

    console.print(table)
    console.print(f"\n[dim]Total: {len(source_chunks)} chunks[/dim]")
