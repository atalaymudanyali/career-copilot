# Career Copilot

AI-powered career tool that tailors CV bullets to job descriptions — grounded exclusively in real experience.

Paste a job description, get back your existing experience reordered and rephrased to match, with skill gaps identified. The tool **never invents** skills or experience; every output bullet traces back to a specific source in your CV data with a mandatory `source_id`.

## How It Works

1. Your CV and project descriptions live in structured local files (`data/`)
2. You provide a job description (file path, stdin, or API request)
3. **V1 (RAG):** The job description is embedded and matched against your CV chunks via pgvector cosine similarity — only the most relevant chunks are sent to the LLM
4. The LLM returns tailored bullets (each with a `source_id`), a "why I fit" summary, and a gaps list
5. Post-generation validation drops any bullet whose `source_id` doesn't resolve to a real chunk

## Quick Start

### Prerequisites

- [Python 3.12+](https://python.org)
- [uv](https://docs.astral.sh/uv/) (package manager)
- [Ollama](https://ollama.com) running locally with models pulled
- [Docker](https://docker.com) (for V1 API mode)

### Setup

```bash
# Clone and install
git clone https://github.com/atalaymudanyali/career-copilot.git
cd career-copilot
uv sync

# Pull the required models
ollama pull llama3.1:8b
ollama pull nomic-embed-text

# Copy and edit the env file
cp .env.example .env
```

### Option A: CLI Only (V0 mode)

Works without Docker or a database — loads all CV data directly and sends it to Ollama.

```bash
# Tailor from a file
career-copilot tailor --jd path/to/job-description.txt

# Pipe from clipboard or another command
cat job-description.txt | career-copilot tailor

# Use a different model
career-copilot tailor --jd jd.txt --model mistral

# View your source chunks
career-copilot chunks
```

### Option B: API Mode (V1 — RAG pipeline)

Uses Docker Compose to run the FastAPI backend with PostgreSQL + pgvector for semantic search.

```bash
# Start the stack (Postgres + FastAPI app)
docker-compose up --build

# Ingest your CV data (embeds and stores in pgvector)
curl -X POST http://localhost:8000/ingest

# Tailor via API
curl -X POST http://localhost:8000/tailor \
  -H "Content-Type: application/json" \
  -d '{"job_description": "Looking for a backend engineer with REST API experience..."}'

# Or use the CLI in API mode
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
│   ├── api/
│   │   ├── health.py              # GET /health
│   │   ├── ingest.py              # POST /ingest
│   │   └── tailor.py              # POST /tailor
│   ├── models/
│   │   ├── domain.py              # Pydantic data models
│   │   └── db.py                  # SQLAlchemy models (pgvector)
│   ├── prompts/templates.py       # LLM prompt templates
│   └── services/
│       ├── llm.py                 # Ollama client (chat + embed)
│       ├── data_loader.py         # CV/project file parser
│       ├── ingestion.py           # Embed + store chunks
│       ├── retrieval.py           # Semantic search via pgvector
│       └── tailoring.py           # Tailoring orchestration
├── alembic/                       # Database migrations
├── Dockerfile                     # Multi-stage build with uv
├── docker-compose.yml             # App + Postgres + pgvector
└── tests/                         # pytest test suite (26 tests)
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
| CLI | Typer + Rich | Clean CLI with formatted tables and spinners |
| LLM | Ollama (local) | Free, no API costs, no rate limits, full GPU |
| Embeddings | nomic-embed-text | 768-dim vectors, runs on Ollama |
| Vector DB | PostgreSQL + pgvector | Cosine similarity search for RAG |
| ORM | SQLAlchemy 2.0 (async) | Type-safe async database access |
| Migrations | Alembic | Versioned schema changes |
| HTTP | httpx | Async HTTP client for Ollama API |
| Config | pydantic-settings | Type-safe, env-driven configuration |
| Container | Docker Compose | One-command deployment |
| Tests | pytest | 26 tests with mocked external services |
| Lint | Ruff | Fast Python linter and formatter |

## Roadmap

- [x] **V0** — CLI tailoring tool with structured output and source validation
- [x] **V1** — RAG with PostgreSQL + pgvector, FastAPI service, Docker Compose
- [ ] **V2** — Application tracker, skill gap analyzer, Jinja2/HTMX dashboard, Prometheus/Grafana
- [ ] **V3** — MCP server for conversational use from Claude/Cursor

## License

MIT
