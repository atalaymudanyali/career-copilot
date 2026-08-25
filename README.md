# Career Copilot

AI-powered career tool that tailors CV bullets to job descriptions — grounded exclusively in real experience.

Paste a job description, get back your existing experience reordered and rephrased to match, with skill gaps identified. The tool **never invents** skills or experience; every output bullet traces back to a specific source in your CV data with a mandatory `source_id`.

## Features

- **RAG-powered tailoring** — embeds your job description, retrieves the most relevant CV chunks via pgvector, and generates tailored bullets with source traceability
- **Application tracker** — CRUD for job applications with status tracking (saved, applied, interviewing, offered, rejected)
- **Dashboard** — server-rendered UI with Jinja2 + HTMX for managing applications, viewing tailoring results, and filtering by status
- **Pipeline view** — kanban board that groups applications by status for at-a-glance tracking
- **PDF export** — generates a tailored CV as a downloadable PDF matching your real CV layout, powered by WeasyPrint
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
│   │   └── db.py                  # SQLAlchemy models (Chunk, Application)
│   ├── prompts/templates.py       # LLM prompt templates
│   └── services/
│       ├── llm.py                 # Ollama client (chat + embed)
│       ├── data_loader.py         # CV/project file parser
│       ├── ingestion.py           # Embed + store chunks
│       ├── retrieval.py           # Semantic search via pgvector
│       ├── tailoring.py           # Tailoring orchestration + validation
│       ├── applications.py        # Application CRUD operations
│       └── pdf.py                 # CV template rendering + PDF generation
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
│       └── _tailoring_result.html # Tailoring result partial (HTMX)
├── alembic/                       # Database migrations
├── Dockerfile                     # Multi-stage build with uv + WeasyPrint
├── docker-compose.yml             # App + Postgres + pgvector
└── tests/                         # pytest test suite (50 tests)
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
| PDF | WeasyPrint | HTML/CSS to PDF with Cairo + Pango |
| HTTP | httpx | Async HTTP client for Ollama API |
| Config | pydantic-settings | Type-safe, env-driven configuration |
| Container | Docker Compose | One-command deployment |
| Tests | pytest | 50 tests with mocked external services |
| Lint | Ruff | Fast Python linter and formatter |

## Roadmap

- [x] **V0** — CLI tailoring tool with structured output and source validation
- [x] **V1** — RAG with PostgreSQL + pgvector, FastAPI service, Docker Compose
- [x] **V2** — Application tracker, dashboard (Jinja2/HTMX), pipeline view, PDF export
- [ ] **V3** — Tailoring versioning, bullet favorites, MCP server for Claude/Cursor

## License

MIT
