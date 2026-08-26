# Career Copilot

AI-powered career tool that tailors CV bullets to job descriptions — grounded exclusively in real experience.

Paste a job description, get back your existing experience reordered and rephrased to match, with skill gaps identified. The tool **never invents** skills or experience; every output bullet traces back to a specific source in your CV data with a mandatory `source_id`.

## Features

- **MCP server** — 14 tools accessible from Claude Desktop, Claude Code, or Cursor for conversational CV tailoring, gap analysis, application tracking, versioning, favorites, and PDF generation
- **RAG-powered tailoring** — embeds your job description, retrieves the most relevant CV chunks via pgvector, and generates tailored bullets with source traceability
- **Tailoring versioning** — every tailor run creates a versioned snapshot; browse and compare past versions without losing history
- **Bullet favorites** — star individual bullets from any version; favorited bullets get priority in PDF generation
- **Application tracker** — CRUD for job applications with status tracking (saved, applied, interviewing, offered, rejected)
- **Dashboard** — dark-theme server-rendered UI with Jinja2 + HTMX for managing applications, viewing tailoring results, and filtering by status
- **Pipeline view** — kanban board that groups applications by status for at-a-glance tracking
- **PDF export** — generates a tailored CV as a downloadable PDF; favorited bullets go first, remaining slots filled by relevance
- **CLI mode** — tailor directly from the terminal without a browser

## Quick Start

### Prerequisites

- [Docker](https://docker.com) and Docker Compose
- [Ollama](https://ollama.com) running locally with models pulled

### Setup

```bash
# Clone and install
git clone https://github.com/atalaymudanyali/career-copilot.git
cd career-copilot

# Pull the required Ollama models
ollama pull llama3.1:8b
ollama pull nomic-embed-text

# Start the stack (Postgres + pgvector + FastAPI)
docker compose up --build
```

The app is available at **http://localhost:8000**.

### First Run

1. **Ingest your CV data** — embeds and stores your CV chunks in pgvector:
   ```bash
   curl -X POST http://localhost:8000/ingest
   ```

2. **Open the dashboard** — go to http://localhost:8000/dashboard

3. **Add an application** — click "+ New Application", enter the company, role, and job description

4. **Tailor your CV** — open an application and click "Tailor CV for This Job"

5. **Download the PDF** — after tailoring, click "Download Tailored CV (PDF)" to get a formatted CV

6. **View your pipeline** — go to http://localhost:8000/dashboard/pipeline for a kanban view

### CLI Mode (no Docker needed)

```bash
uv sync

# Tailor from a file
career-copilot tailor --jd path/to/job-description.txt

# Pipe from clipboard or another command
cat job-description.txt | career-copilot tailor

# Use a different model
career-copilot tailor --jd jd.txt --model mistral

# Use API mode (requires Docker stack running)
career-copilot tailor --jd jd.txt --api
```

### MCP Server (Claude Desktop / Claude Code / Cursor)

The MCP server exposes all functionality as conversational tools. No Docker required for basic use.

**Setup for Claude Desktop:**

1. Install dependencies: `uv sync`
2. Copy the config into Claude Desktop's settings:

```json
{
  "mcpServers": {
    "career-copilot": {
      "command": "uv",
      "args": ["--directory", "/path/to/career-copilot", "run", "career-copilot-mcp"]
    }
  }
}
```

On Windows, the config file is at `%APPDATA%\Claude\claude_desktop_config.json`.
On macOS, it's at `~/Library/Application Support/Claude/claude_desktop_config.json`.

3. Restart Claude Desktop — tools appear under the Connectors menu.

**Available tools:**

| Tool | Needs | What it does |
|------|-------|-------------|
| `get_cv_summary` | Nothing | Candidate overview |
| `list_skills` | Nothing | Skills by category |
| `list_source_chunks` | Nothing | Raw CV/project chunks |
| `tailor_cv` | Ollama | Tailor bullets for a job description |
| `analyze_skill_gaps` | Ollama | Gap analysis for a job description |
| `generate_cv_pdf` | Ollama + WeasyPrint | Tailor + generate PDF in one call |
| `list_applications` | Docker | List tracked applications |
| `add_application` | Docker | Save a new application |
| `get_application` | Docker | Full application details |
| `update_application_status` | Docker | Change application status |
| `list_tailoring_versions` | Docker | List version history for an application |
| `get_tailoring_version` | Docker | Get a specific version's full result |
| `list_favorite_bullets` | Docker | List starred bullets (all or per-app) |
| `toggle_favorite_bullet` | Docker | Star or unstar a bullet |

**Example prompts:**
- "Tailor my CV for this role: [paste JD]"
- "What skills am I missing for this job? [paste JD]"
- "Generate a PDF for the Backend Developer role at Google: [paste JD]"
- "Save this job posting" / "Show my applications" / "Update #1 to interviewing"
- "Show my tailoring versions for application #3" / "Star this bullet for app #1"

### Edit Your CV Data

- **`data/cv.json`** — your structured CV (contact, education, skills, experience)
- **`data/projects/*.md`** — one markdown file per project with YAML frontmatter

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (includes Ollama connectivity) |
| POST | `/ingest` | Embed CV chunks and store in pgvector |
| POST | `/tailor` | Retrieve relevant chunks and generate tailored bullets |
| GET | `/dashboard` | Application list with status filters |
| GET | `/dashboard/pipeline` | Kanban board view |
| GET | `/dashboard/{id}` | Application detail with inline editing |
| GET | `/dashboard/{id}/cv.pdf` | Download tailored CV as PDF |
| POST | `/api/applications` | Create application (JSON API) |
| GET | `/api/applications` | List applications (JSON API) |
| PATCH | `/api/applications/{id}` | Update application (JSON API) |
| DELETE | `/api/applications/{id}` | Delete application (JSON API) |
| GET | `/docs` | Interactive API documentation (Swagger UI) |

## Architecture

```
career-copilot/
├── data/                          # Your real CV/project data
│   ├── cv.json                    # Structured CV
│   └── projects/*.md              # Project descriptions (YAML frontmatter)
├── src/career_copilot/
│   ├── cli.py                     # Typer CLI (local + API mode)
│   ├── mcp_server.py              # MCP server (14 tools for Claude/Cursor)
│   ├── config.py                  # pydantic-settings configuration
│   ├── db.py                      # Async database session management
│   ├── main.py                    # FastAPI application
│   ├── templating.py              # Shared Jinja2 template config
│   ├── api/
│   │   ├── health.py              # GET /health
│   │   ├── ingest.py              # POST /ingest
│   │   ├── tailor.py              # POST /tailor
│   │   ├── applications.py        # JSON API for applications
│   │   └── dashboard.py           # Server-rendered dashboard routes
│   ├── models/
│   │   ├── domain.py              # Pydantic models + enums
│   │   └── db.py                  # SQLAlchemy models (Chunk, Application, TailoringVersion, FavoriteBullet)
│   ├── prompts/templates.py       # LLM prompt templates
│   └── services/
│       ├── llm.py                 # Ollama client (chat + embed)
│       ├── data_loader.py         # CV/project file parser
│       ├── ingestion.py           # Embed + store chunks
│       ├── retrieval.py           # Semantic search via pgvector
│       ├── tailoring.py           # Tailoring orchestration + validation
│       ├── applications.py        # Application CRUD operations
│       ├── tailoring_versions.py  # Tailoring version CRUD
│       ├── favorites.py           # Bullet favorites service
│       └── pdf.py                 # CV template rendering + PDF generation (favorites-aware)
├── templates/
│   ├── base.html                  # Base layout (Tailwind CDN + HTMX)
│   ├── index.html                 # Landing page
│   ├── cv/document.html           # CV PDF template (embedded CSS)
│   └── dashboard/
│       ├── list.html              # Application table + filter pills
│       ├── detail.html            # Application detail + inline editing
│       ├── pipeline.html          # Kanban board view
│       ├── 404.html               # Not found page
│       ├── _app_row.html          # Table row partial (HTMX)
│       ├── _form_create.html      # Create form partial (HTMX)
│       ├── _pipeline_card.html    # Pipeline card partial
│       ├── _tailoring_result.html # Tailoring result partial (HTMX)
│       ├── _bullet_star.html      # Star/unstar toggle button
│       ├── _notes_section.html    # Bullet-style notes with linkify
│       └── _tailor_button.html    # Empty state tailor button
├── alembic/                       # Database migrations
├── claude-desktop-config.example.json  # Example MCP config for Claude Desktop
├── Dockerfile                     # Multi-stage build with uv + WeasyPrint
├── docker-compose.yml             # App + Postgres + pgvector
└── tests/                         # pytest test suite (77 tests)
```

## "Never Invent" Enforcement

This is the core design constraint, enforced at three levels:

1. **Prompt-level**: The system prompt explicitly instructs the LLM to only rephrase source chunks and list gaps for anything not found
2. **Schema-level**: JSON output requires a `source_id` for every bullet (enforced via Ollama's `format: "json"`)
3. **Validation-level**: Post-generation code checks every `source_id` resolves to a real chunk — unresolvable bullets are dropped with a warning

## Tech Stack

| Component | Choice | Why |
|-----------|--------|-----|
| API | FastAPI | Async, auto-docs, Pydantic integration |
| Frontend | Jinja2 + HTMX + Tailwind CSS | Server-rendered, no build step, dynamic UI without JS framework |
| CLI | Typer + Rich | Clean CLI with formatted tables and spinners |
| LLM | Ollama (local) | Free, no API costs, no rate limits, full GPU |
| Embeddings | nomic-embed-text | 768-dim vectors, runs on Ollama |
| Vector DB | PostgreSQL + pgvector | Cosine similarity search for RAG |
| ORM | SQLAlchemy 2.0 (async) | Type-safe async database access |
| Migrations | Alembic | Versioned schema changes |
| MCP | mcp[cli] | Model Context Protocol server for AI assistants |
| PDF | WeasyPrint | HTML/CSS to PDF with Cairo + Pango |
| HTTP | httpx | Async HTTP client for Ollama API |
| Config | pydantic-settings | Type-safe, env-driven configuration |
| Container | Docker Compose | One-command deployment |
| Tests | pytest | 101 tests with mocked external services |
| Lint | Ruff | Fast Python linter and formatter |

## Roadmap

- [x] **V0** — CLI tailoring tool with structured output and source validation
- [x] **V1** — RAG with PostgreSQL + pgvector, FastAPI service, Docker Compose
- [x] **V2** — Application tracker, dashboard (Jinja2/HTMX), pipeline view, PDF export
- [x] **V3** — MCP server (10 tools for Claude/Cursor), page-fill fix, skill gap analysis
- [x] **V4** — Dark theme redesign, tailoring versioning, bullet favorites with PDF priority, 14 MCP tools

## License

MIT
