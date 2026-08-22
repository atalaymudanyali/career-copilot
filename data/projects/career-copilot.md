---
id: career-copilot
title: Career Copilot
tech: [Python, FastAPI, PostgreSQL, pgvector, Ollama, Docker, Prometheus, Grafana]
date: 2026-08
---

AI-powered career tool that tailors CV bullets to job descriptions using retrieval-augmented generation, grounded exclusively in real experience. Enforces a "never invent" constraint through structured LLM output with mandatory source attribution and post-generation validation.

Built with a production-grade architecture: containerized FastAPI service backed by PostgreSQL with pgvector for semantic search, Ollama for local LLM inference, and Prometheus/Grafana for observability. Includes an application tracker with skill gap analysis across job postings.

Exposed as an MCP server with tools for semantic project search, bullet tailoring, application logging, and skill gap analysis — enabling conversational use from Claude or Cursor.
