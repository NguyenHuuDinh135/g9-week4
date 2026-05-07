# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

Week 4 group project for GeekBrain AI Q&A system — a RAG + Tools + Memory pipeline that answers questions about a fictional fintech startup running 6 production services. Deadline: Friday 2026-05-08 presentation.

**Grading:** L1 (2pts) + L2 (3pts) + L3 (4pts) + L4 (1pt) = 10. L1-L3 = 90% of grade. Bonus up to +1.0.

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

## Commands

### Setup data layer
```bash
cd W4/data_package/scripts
uv sync
uv run python seed_data.py --db-type sqlite    # creates geekbrain.db with 4 tables
uv run uvicorn monitoring_api:app --port 8000   # start monitoring API
```

### Verify data
```bash
# Database: 36 rows in monthly_costs, 8 in incidents, 18 in sla_targets, 540 in daily_metrics
sqlite3 W4/data_package/scripts/geekbrain.db "SELECT COUNT(*) FROM monthly_costs;"

# API endpoints
curl http://localhost:8000/services
curl http://localhost:8000/status/PaymentGW
curl http://localhost:8000/metrics/PaymentGW
curl http://localhost:8000/incidents
```

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

## Recommended Code Structure

```
src/
├── config.py          # AWS region, model IDs, KB ID, API URL
├── rag/
│   ├── retriever.py   # Bedrock KB Retrieve wrapper (top-K chunks)
│   └── generator.py   # Claude LLM call with system prompt
├── tools/
│   ├── database_tool.py   # Read-only SQL against geekbrain.db
│   └── metrics_tool.py    # HTTP GET to monitoring API
├── memory/
│   └── conversation.py    # Sliding window (last 5 turns)
├── agent.py           # Orchestrator: route question → KB / tool / both
└── main.py            # CLI or web entry point
tests/
├── test_l1_retrieval.py
├── test_l2_conflicts.py
├── test_l3_tools.py
└── test_l4_memory.py
```

## Deliverables

1. **Working system** — demoable live on Friday, no hardcoded responses
2. **Evidence Pack** — `docs/W4_evidence.md` with architecture diagram, decision log, per-level screenshots + logs
3. **Slides** — derived from Evidence Pack, commit link posted to Slack before presentation slot

## Six Services

PaymentGW, OrderSvc, AuthSvc, NotificationSvc, ReportingSvc, FraudDetector
