---
id: event-triage-pipeline
title: Event-Driven AI Triage Pipeline
tech: [Python, FastAPI, Kafka/Redpanda, Gemini, PostgreSQL, React, Docker, Kubernetes, Prometheus, Grafana, GitHub Actions]
date: 2026-09
---

Event-driven microservices pipeline where an AI agent consumes e-commerce support ticket events from Kafka (Redpanda), triages them through a multi-step LLM agent (classify → assess urgency → draft response), and writes structured decisions to PostgreSQL with idempotent writes and dead-letter topic for failed events.

Full-stack delivery: React dashboard for ticket submission and admin triage, FastAPI REST API with Prometheus metrics middleware, pre-built Grafana dashboard with 16 panels, and two deployment paths — Docker Compose for quick demo, Kubernetes (kind) with plain YAML manifests for infrastructure showcase. CI via GitHub Actions with pre-push hooks.
