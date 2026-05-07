# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

Week 4 group project for GeekBrain AI Q&A system — a RAG + Tools + Memory pipeline that answers questions about a fictional fintech startup running 6 production services. Deadline: Friday 2026-05-08 presentation.

**Grading:** L1 (2pts) + L2 (3pts) + L3 (4pts) + L4 (1pt) = 10. L1-L3 = 90% of grade. Bonus up to +1.0.

## Monorepo Structure

```
geekbrain-ai/                    # Turborepo + bun workspaces
├── apps/
│   ├── web/                     # Next.js 16 (App Router, Turbopack, RSC)
│   │   ├── app/                 # Routes (layout.tsx, page.tsx)
│   │   ├── components/
│   │   │   ├── assistant-ui/    # 10 chat thread components (@assistant-ui registry)
│   │   │   ├── tool-ui/        # 12 widget categories (chart, data-table, terminal, etc.)
│   │   │   └── theme-provider.tsx
│   │   └── components.json      # shadcn config (style: radix-nova, RTL enabled)
│   └── api/                     # Python backend (RAG + Tools + Memory)
│       ├── main.py              # CLI entry point
│       ├── pyproject.toml       # Python deps (boto3, httpx)
│       └── src/
│           ├── config.py        # AWS region, model IDs, KB ID, system prompt
│           ├── agent.py         # Orchestrator: route → KB / tool / both (Bedrock tool_use)
│           ├── rag/
│           │   ├── retriever.py # Bedrock KB Retrieve API (top-K chunks)
│           │   └── generator.py # Bedrock Converse API (Claude Sonnet)
│           ├── tools/
│           │   ├── database_tool.py  # Read-only SQL against geekbrain.db
│           │   └── metrics_tool.py   # HTTP GET to monitoring API
│           └── memory/
│               └── conversation.py   # Sliding window (last 5 turns) [L4]
├── packages/
│   ├── ui/src/components/       # 82 shared UI components (shadcn + magicui + animate-ui)
│   ├── eslint-config/
│   └── typescript-config/
├── infra/                       # Terraform (S3, Bedrock KB, OpenSearch Serverless, IAM)
├── data_package/
│   ├── knowledge_base/          # 36 .md files (policies, postmortems, architecture)
│   ├── structured_data/         # 4 CSVs (monthly_costs, incidents, sla_targets, daily_metrics)
│   └── scripts/                 # seed_data.py, monitoring_api.py (FastAPI)
├── questions/                   # L1-L5 evaluation question sets (.json)
└── docs/                        # Project guides, console hands-on, mentoring
```

## Commands

### Monorepo (from root)
```bash
bun install                      # install all workspace deps
bun run dev                      # turbo dev (Next.js on :3000)
bun run build                    # turbo build (all workspaces)
bun run lint                     # turbo lint
bun run typecheck                # turbo typecheck
```

### Web app (from apps/web/)
```bash
bun run dev                      # next dev --turbopack
bun run build                    # next build
bun run typecheck                # tsc --noEmit
```

### Add shadcn components
```bash
bunx --bun shadcn@latest add <component> -c apps/web
bunx --bun shadcn@latest add @magicui/<name> -c apps/web
bunx --bun shadcn@latest add @prompt-kit/<name> -c apps/web
bunx --bun shadcn@latest add @tool-ui/<name> -c apps/web
bunx --bun shadcn@latest add @assistant-ui/<name> -c apps/web
bunx --bun shadcn@latest add @animate-ui/<name> -c apps/web
```

### Backend API (from apps/api/)
```bash
uv sync                                          # install Python deps (boto3, httpx)
uv run python main.py                            # start CLI chat interface
```

### Data layer (from data_package/scripts/)
```bash
uv sync                                          # install Python deps
uv run python seed_data.py --db-type sqlite      # creates geekbrain.db (4 tables)
uv run uvicorn monitoring_api:app --port 8000    # start monitoring API
```

### Infrastructure (from infra/)
```bash
terraform init                                   # download providers
terraform plan                                   # preview changes
terraform apply                                  # create S3 + KB + OpenSearch
./scripts/sync_kb.sh                             # trigger KB ingestion
```

### Verify data
```bash
sqlite3 data_package/scripts/geekbrain.db "SELECT COUNT(*) FROM monthly_costs;"  # expect 36
curl http://localhost:8000/services
curl http://localhost:8000/status/PaymentGW
curl http://localhost:8000/metrics/PaymentGW
```

## Architecture

```
USER QUESTION
      │
      ▼
AGENT ORCHESTRATOR (decides: KB retrieve / tool call / both)
  + Conversation Memory [L4] (sliding window, last 5 turns)
      │
      ├──→ BEDROCK KB (L1, L2): S3 docs → Titan Embeddings → OpenSearch → top-K chunks
      ├──→ DATABASE TOOL (L3): SQLite (geekbrain.db) — costs, incidents, SLA, daily metrics
      └──→ METRICS TOOL (L3): FastAPI localhost:8000 — live status, latency, error rate
      │
      ▼
BEDROCK LLM (Claude Sonnet): system prompt + chunks + tool results + history → answer with citations
```

## Three Data Sources (Critical Boundary)

| Source | Contains | Does NOT contain |
|--------|----------|-----------------|
| Knowledge Base (36 .md files) | Policies, team structure, architecture, postmortems | Dollar amounts, daily metrics, current system state |
| Database (4 CSV → SQLite) | Exact costs, incident records, SLA targets, daily metrics | Current live data, qualitative analysis |
| Monitoring API (FastAPI) | Current status, latency, error rate, requests/min | Historical data, costs, policies |

If a question asks for numbers or live data, documents cannot answer it — only tools can.

## Key Data Points for L3 Numerical Accuracy

| Question | Answer | Source |
|----------|--------|--------|
| PaymentGW total cost Q1 2026 | $16,500 | DB: SUM where month IN ('2026-01','2026-02','2026-03') |
| Total cost all services Q1 2026 | $56,350 | DB: SUM all Q1 |
| Highest cost service March 2026 | PaymentGW $7,500 | DB |
| PaymentGW current p99 latency | ~185ms (±5% jitter) | API |
| NotificationSvc latency SLA target | 2000ms | DB: sla_targets |
| NotificationSvc current p99 | ~3200ms (degraded) | API |
| NotificationSvc error rate target | 1.0% | DB |
| NotificationSvc current error rate | ~2.1% | API |
| AuthSvc requests per minute | ~28,000 (highest) | API |
| PaymentGW incidents in Q1 | 3 (INC-001, INC-003, INC-005) | DB |

## Known Document Conflicts (L2)

- **API rate limit:** `api_reference_v1_archived.md` says 500 req/min; `api_reference_v2.md` says 1000 req/min. v2 is correct.
- **NotificationSvc** is currently degraded (HIGH_LATENCY + ELEVATED_ERROR_RATE alerts) — API shows this, documents do not.

## Database Schema

Tables created by `seed_data.py`:

- `monthly_costs` (service, month, compute_cost, storage_cost, network_cost, third_party_cost, total_cost)
- `incidents` (incident_id, service, date, severity, duration_minutes, root_cause, resolution, team_responsible, reported_by)
- `sla_targets` (service, metric, target, measurement_window)
- `daily_metrics` (date, service, latency_p99_ms, error_rate_percent, requests_per_minute, availability_percent)

## Monitoring API Endpoints

- `GET /services` — list of 6 service names
- `GET /status/{service_name}` — uptime, active_alerts, status (healthy/degraded)
- `GET /metrics/{service_name}` — latency p50/p95/p99, error_rate, rpm, cpu, memory (with ±5% jitter per call)
- `GET /incidents` — all 8 incident records
- `GET /incidents/{service_name}` — filtered by service

## Tool Definitions for LLM

Tool descriptions must clearly distinguish WHEN to use each:
- **Database Query:** "HISTORICAL structured data — past costs, incident records, SLA target numbers, daily metrics. NOT for current/live state."
- **Service Metrics:** "CURRENT LIVE status and metrics RIGHT NOW — latency, error rate, rpm, cpu, memory. NOT for historical data or past costs."

## Frontend Stack

- **Framework:** Next.js 16 (App Router, RSC, Turbopack)
- **UI:** shadcn/ui (radix-nova style) + 5 community registries
- **State:** zustand, @assistant-ui/react
- **Styling:** Tailwind CSS v4, CSS variables, RTL-ready
- **Package manager:** bun 1.3.11
- **Build:** Turborepo

### Component Libraries Installed

| Registry | Location | Components |
|----------|----------|------------|
| shadcn/ui base | `packages/ui/src/components/` | 55 core (button, dialog, table, etc.) |
| @magicui | `packages/ui/src/components/` | 16 animated (bento-grid, dock, marquee, etc.) |
| @animate-ui | `packages/ui/src/components/animate-ui/` | backgrounds, buttons, effects, texts |
| @prompt-kit | `packages/ui/src/components/` | chat-container, code-block, markdown, etc. |
| @assistant-ui | `apps/web/components/assistant-ui/` | thread, reasoning, markdown-text, tool-fallback |
| @tool-ui | `apps/web/components/tool-ui/` | 12 categories (chart, data-table, terminal, etc.) |

## Path Aliases

```
@/*                → apps/web/*
@workspace/ui/*    → packages/ui/src/*
```

## Backend API (apps/api/)

Python backend implementing the full L1-L4 pipeline:

| Module | Level | Purpose |
|--------|-------|---------|
| `src/config.py` | All | AWS config, model IDs, system prompt with conflict resolution rules |
| `src/rag/retriever.py` | L1 | Bedrock KB Retrieve API → top-K chunks |
| `src/rag/generator.py` | L1 | Bedrock Converse API (Claude Sonnet) |
| `src/tools/database_tool.py` | L3 | Read-only SQL with injection protection |
| `src/tools/metrics_tool.py` | L3 | HTTP client for monitoring API (httpx) |
| `src/memory/conversation.py` | L4 | Sliding window deque (5 turns) |
| `src/agent.py` | L2-L4 | Orchestrator with Bedrock tool_use loop (max 5 iterations) |
| `main.py` | All | CLI entry point |

### Environment Variables
```bash
BEDROCK_KB_ID=<your-kb-id>       # from terraform output or console
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-20250514
MONITORING_API_URL=http://localhost:8000
DATABASE_PATH=../../data_package/scripts/geekbrain.db
```

## Infrastructure (infra/)

Terraform module provisioning:
- S3 bucket + auto-upload 36 .md KB docs
- OpenSearch Serverless collection (VECTORSEARCH)
- Bedrock Knowledge Base (Titan Embed V2, fixed chunking 512 tokens / 20% overlap)
- IAM role + policies (S3 read, Bedrock invoke, AOSS access)

Outputs: `knowledge_base_id`, `data_source_id`, `s3_bucket_name`, `opensearch_collection_endpoint`

## Six Services

PaymentGW, OrderSvc, AuthSvc, NotificationSvc, ReportingSvc, FraudDetector

## Deliverables

1. **Working system** — demoable live on Friday, no hardcoded responses
2. **Evidence Pack** — `docs/W4_evidence.md` with architecture diagram, decision log, per-level screenshots + logs
3. **Slides** — derived from Evidence Pack, commit link posted to Slack before presentation slot
