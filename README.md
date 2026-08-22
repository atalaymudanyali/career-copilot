# Career Copilot

AI-powered career tool that tailors CV bullets to job descriptions — grounded exclusively in real experience.

Paste a job description, get back your existing experience reordered and rephrased to match, with skill gaps identified. The tool **never invents** skills or experience; every output bullet traces back to a specific source in your CV data with a mandatory `source_id`.

## How It Works

1. Your CV and project descriptions live in structured local files (`data/`)
2. You provide a job description (file path or stdin)
3. The LLM receives your real experience as source chunks and the job description
4. It returns tailored bullets (each with a `source_id`), a "why I fit" summary, and a gaps list
5. Post-generation validation drops any bullet whose `source_id` doesn't resolve to a real chunk

## Quick Start

### Prerequisites

- [Python 3.12+](https://python.org)
- [uv](https://docs.astral.sh/uv/) (package manager)
- [Ollama](https://ollama.com) running locally with a model pulled

### Setup

```bash
# Clone and install
git clone https://github.com/PLACEHOLDER/career-copilot.git
cd career-copilot
uv sync

# Pull the default model
ollama pull llama3.1:8b

# (Optional) Copy and edit the env file
cp .env.example .env
```

### Edit Your CV Data

- **`data/cv.json`** — your structured CV (contact, education, skills, experience)
- **`data/projects/*.md`** — one markdown file per project with YAML frontmatter

### Usage

```bash
# Tailor from a file
career-copilot tailor --jd path/to/job-description.txt

# Pipe from clipboard or another command
cat job-description.txt | career-copilot tailor

# Use a different model
career-copilot tailor --jd jd.txt --model mistral

# View your source chunks (what the LLM can reference)
career-copilot chunks
```

## Architecture

```
career-copilot/
├── data/                          # Your real CV/project data
│   ├── cv.json                    # Structured CV
│   └── projects/*.md              # Project descriptions (YAML frontmatter)
├── src/career_copilot/
│   ├── cli.py                     # Typer CLI entry point
│   ├── config.py                  # pydantic-settings configuration
│   ├── models/domain.py           # Pydantic data models
│   ├── prompts/templates.py       # LLM prompt templates
│   └── services/
│       ├── llm.py                 # Ollama HTTP client
│       ├── data_loader.py         # CV/project file parser
│       └── tailoring.py           # Core tailoring orchestration
└── tests/                         # pytest test suite
```

## "Never Invent" Enforcement

This is the core design constraint, enforced at three levels:

1. **Prompt-level**: The system prompt explicitly instructs the LLM to only rephrase source chunks and list gaps for anything not found
2. **Schema-level**: JSON output requires a `source_id` for every bullet (enforced via Ollama's `format: "json"`)
3. **Validation-level**: Post-generation code checks every `source_id` resolves to a real chunk — unresolvable bullets are dropped with a warning

## Tech Stack

| Component | Choice | Why |
|-----------|--------|-----|
| CLI | Typer + Rich | Clean CLI with formatted tables and spinners |
| LLM | Ollama (local) | Free, no API costs, no rate limits, full GPU |
| HTTP | httpx | Async HTTP client for Ollama API |
| Config | pydantic-settings | Type-safe, env-driven configuration |
| Data | JSON + Markdown/YAML frontmatter | Human-readable, version-controllable |
| Tests | pytest | Standard, with fixtures for test data |
| Lint | Ruff | Fast Python linter and formatter |

## Roadmap

- [x] **V0** — CLI tailoring tool with structured output and source validation
- [ ] **V1** — RAG with PostgreSQL + pgvector, FastAPI service, Docker Compose
- [ ] **V2** — Application tracker, skill gap analyzer, Jinja2/HTMX dashboard, Prometheus/Grafana
- [ ] **V3** — MCP server for conversational use from Claude/Cursor

## License

MIT
