# ECC Workflow Guide — W4 GeekBrain AI System

> Hướng dẫn dùng Everything Claude Code để build hệ thống AI RAG + Tools + Memory cho GeekBrain

---

## Project Overview

**Goal:** Build AI system trả lời câu hỏi về GeekBrain (fintech startup, 6 production services)

**4 Levels:**
- L1 (2đ): Simple RAG — tìm fact trong 1 document
- L2 (3đ): Multi-Source RAG — tổng hợp nhiều docs, resolve conflicts
- L3 (4đ): Tool-Augmented RAG — query DB + monitoring API
- L4 (1đ): Memory — multi-turn conversation

**Data Sources:**
| Source | Content | Access |
|--------|---------|--------|
| Knowledge Base (36 .md) | Company info, policies, postmortems | RAG retrieval |
| Database (4 CSV) | Costs, incidents, SLA, daily metrics | SQL tools |
| Monitoring API (FastAPI) | Live status, latency, error rate | HTTP tools |

**Tech Stack:** S3 + Bedrock KB + Bedrock (Claude) + Lambda + SQLite/RDS

---

## Day-by-Day ECC Workflow

---

### Day 1 (Thứ Ba): Khám phá Data + Architecture

#### Step 1: Đọc documents

```
/aside What are the main topic clusters across 36 knowledge base docs?
```

```
/aside Which documents have contradicting information I need to handle in L2?
```

#### Step 2: Plan toàn bộ architecture

```
/plan Build AI Q&A system for GeekBrain with 4 levels:
L1 - Simple RAG (Bedrock KB + Claude)
L2 - Multi-source RAG (conflict resolution via prompt)
L3 - Tool-augmented (DB query tool + monitoring API tool)
L4 - Multi-turn memory (sliding window buffer)

Data: 36 markdown docs, 4 CSV files (costs/incidents/sla/metrics), 1 FastAPI monitoring API
Stack: Python, AWS Bedrock, SQLite for local dev
Deadline: Friday presentation
```

**Expected plan output:**
```
Phase 1: Data layer setup (seed DB, start API) — 1h
Phase 2: L1 Simple RAG (S3 + Bedrock KB + Claude) — 2h
Phase 3: L2 Multi-source (prompt engineering + K increase) — 1h
Phase 4: L3 Tools (2 tool functions + routing) — 3h
Phase 5: L4 Memory (conversation buffer) — 1h
Phase 6: Evidence Pack + slides — 2h

Risks:
- HIGH: Tool routing — LLM calls wrong tool
- MEDIUM: Bedrock KB sync time
- LOW: Memory overflow on long conversations
```

#### Step 3: Setup data layer

```bash
cd data_package/scripts
uv sync
uv run uvicorn monitoring_api:app --port 8000
uv run python seed_data.py --db-type sqlite
```

Verify:
```
/aside The monitoring API is running. What endpoints does it expose and what data is ONLY available from the API?
```

---

### Day 2 (Thứ Năm): Build L1 → L2 → L3

---

#### L1: Simple RAG (Target: trước 12:00)

**ECC Command:**
```
/tdd Build L1 RAG pipeline:
- Upload 36 knowledge_base/*.md to S3 bucket
- Create Bedrock Knowledge Base with Titan Embeddings v2
- Implement retrieve_and_answer(question) → returns answer + source document name
- System prompt: answer from context only, cite source document
Test cases:
  "Who is the Team Platform lead?" → "Alex Chen" citing team_platform.md
  "What authentication does PaymentGW use?" → "API key + HMAC-SHA256"
  "What is the deployment freeze window?" → "Friday 18:00 to Monday 08:00"
```

**TDD cycle sẽ diễn ra:**
```
RED: 3 test cases written, all FAIL (not implemented)
GREEN: Implement retriever.py + generator.py
  - retriever: calls Bedrock KB Retrieve API, returns top-K chunks
  - generator: sends chunks + question to Claude, gets answer
PASS: All 3 tests pass with correct answers + citations
REFACTOR: Extract config, add retry logic
```

**Code structure:**
```
src/
├── config.py          # AWS region, model IDs, KB ID
├── rag/
│   ├── retriever.py   # Bedrock KB Retrieve wrapper
│   └── generator.py   # Claude LLM call
├── tools/             # (L3)
├── memory/            # (L4)
├── agent.py           # Orchestrator (L3+)
└── main.py            # CLI entry point
tests/
├── test_l1_retrieval.py
├── test_l2_conflicts.py
├── test_l3_tools.py
└── test_l4_memory.py
```

**If Bedrock API errors:**
```
/build-fix
```

**If confused about Bedrock API:**
```
/docs how to use Bedrock Knowledge Base Retrieve API with Python boto3
```

---

#### L2: Multi-Source RAG (Target: trước 15:00)

**ECC Command:**
```
/tdd Improve RAG for L2 multi-source:
- Increase retrieval K from 3 to 10 chunks
- Update system prompt for conflict resolution:
  "When sources conflict, check dates and version numbers. 
   Prefer most recent. Documents marked 'archived' or 'v1' are superseded.
   State which version you trust and cite both sources."
Tests:
  "What is PaymentGW's API rate limit?" → must answer 1000 (from v2), 
    acknowledge v1 said 500
  "Can Team Commerce deploy on Friday night for a P1 bug?" → must combine 
    deployment_policy.md + incident_response_policy.md
```

**TDD cycle:**
```
RED: test_conflict_resolution(), test_multi_doc_synthesis() → FAIL
GREEN: 
  - retriever.py: change top_k=10
  - generator.py: update system prompt with conflict resolution instructions
PASS: Rate limit → 1000 (v2) ✓, Friday deploy → emergency exception ✓
```

**Verify:**
```
/verify
```

---

#### L3: Tool-Augmented RAG (Target: first tool call trước 17:00)

**ECC Command:**
```
/feature-dev Add L3 tool integration:
Requirements:
- Tool 1: query_database(sql) — read-only SQL against SQLite (geekbrain.db)
- Tool 2: get_service_metrics(service_name) — GET /metrics/{service} from localhost:8000
- Agent orchestrator: LLM decides retrieve-from-KB vs call-tool based on question type
- Tool descriptions must be SPECIFIC about when to use each

Test cases (numerical accuracy required):
  "What was PaymentGW's total cost in Q1 2026?" → DB tool → $16,500
  "What is PaymentGW's current p99 latency?" → Metrics tool → ~185ms
  "Is NotificationSvc meeting its latency SLA?" → BOTH tools → No (3200ms vs 2000ms target)
```

**Feature-dev phases:**
```
Phase 1 Discovery: 2 tools + orchestration needed
Phase 2 Exploration: reads monitoring_api.py endpoints, seed_data.py schema
Phase 3 Questions: "Use Bedrock Agents or raw function calling?" 
  → Raw function calling (more control, faster to iterate)
Phase 4 Architecture:
  src/tools/database_tool.py
  src/tools/metrics_tool.py  
  src/agent.py (orchestrator with tool definitions)
Phase 5 Implementation (TDD per tool)
Phase 6 Review: code-reviewer checks tool descriptions, error handling
```

**Critical: Tool definitions for LLM routing:**
```python
tools = [
    {
        "name": "query_database",
        "description": "Query HISTORICAL structured data from the database. "
                      "Contains: monthly infrastructure costs per service (Oct 2025-Mar 2026), "
                      "incident records (8 total), SLA targets per service, "
                      "daily metrics (Jan-Mar 2026). "
                      "Use for: past costs, totals, averages, incident history, SLA numbers. "
                      "Do NOT use for current/live system state.",
        "input_schema": {
            "type": "object",
            "properties": {"sql": {"type": "string", "description": "Read-only SQL query"}},
            "required": ["sql"]
        }
    },
    {
        "name": "get_service_metrics",
        "description": "Get CURRENT LIVE status and metrics of a service RIGHT NOW. "
                      "Returns: current p99 latency, error rate, requests/min, CPU, memory. "
                      "Use for: what is happening now, current health, live performance. "
                      "Do NOT use for historical data or past costs.",
        "input_schema": {
            "type": "object", 
            "properties": {"service_name": {"type": "string"}},
            "required": ["service_name"]
        }
    }
]
```

**After implementation, verify accuracy:**
```
/verify
```

---

### Day 3 (Sáng thứ Sáu): L4 + Evidence + Polish

---

#### L4: Memory (1 hour max)

**ECC Command:**
```
/tdd Add conversation memory for multi-turn L4:
- Strategy: sliding window (last 5 turns)
- Prepend conversation history to LLM context each turn
- Pronouns like "its", "that service", "their team" must resolve from history

Test conversation:
  Turn 1: "Which service had highest cost in March 2026?" → PaymentGW ($7,500)
  Turn 2: "Why did its costs spike?" → resolves "its" = PaymentGW, retrieves postmortem
  Turn 3: "Which team is responsible?" → Team Platform, Alex Chen
  Turn 4: "Are there any open action items from their postmortem?" → resolves context chain
```

**Simple implementation:**
```python
class ConversationMemory:
    def __init__(self, window_size=5):
        self.history = []
        self.window_size = window_size
    
    def add_turn(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
    
    def get_context(self) -> list:
        return self.history[-self.window_size * 2:]
    
    def clear(self):
        self.history = []
```

---

#### Evidence Pack

```
/prp-plan Write W4 Evidence Pack markdown at docs/W4_evidence.md:
- Section 1: Cover (team, LLM used, framework, repo link)
- Section 2: Architecture diagram + component list + data flow
- Section 3: Decision log (3 decisions, including 1 failure)
- Section 4: Per-level evidence with screenshots + logs
- Section 5: Reflection (hardest level, what we'd do differently)
```

---

#### Final verification

```
/verify

# Then manual end-to-end test
python main.py
> Who leads Team Platform?                    # L1
> What is the API rate limit for PaymentGW?   # L2 (conflict)
> What was PaymentGW's total cost in Q1?      # L3 (DB tool)
> What is its current latency?                # L4 (memory: "its" = PaymentGW)
```

---

#### Commit and save

```
/prp-commit "feat: complete L1-L4 AI system with RAG, tools, and memory"
/save-session
```

---

## ECC Commands by Phase

### Planning Phase

| Action | Command |
|--------|---------|
| Understand the project | `/plan` with full requirements |
| Quick data questions | `/aside <question>` |
| Look up AWS docs | `/docs how does Bedrock KB work` |

### Build Phase

| Action | Command |
|--------|---------|
| Implement with tests first | `/tdd <description with test cases>` |
| Guided feature development | `/feature-dev <description>` |
| Fix build/runtime errors | `/build-fix` |
| Auto code review | Happens automatically after writes |
| Check quality | `/verify` |

### Polish Phase

| Action | Command |
|--------|---------|
| Generate architecture docs | `/update-codemaps` |
| Final quality gate | `/verify` |
| Smart commit | `/prp-commit "message"` |
| Save progress | `/save-session` |

---

## Numerical Accuracy Reference (L3)

Your system MUST return these exact values:

| Question | Tool | SQL/Call | Answer |
|----------|------|---------|--------|
| PaymentGW total cost Q1 2026 | DB | `SELECT SUM(total_cost) FROM monthly_costs WHERE service='PaymentGW' AND month IN ('2026-01','2026-02','2026-03')` | $16,500 |
| Highest cost service March 2026 | DB | `SELECT service, total_cost FROM monthly_costs WHERE month='2026-03' ORDER BY total_cost DESC LIMIT 1` | PaymentGW, $7,500 |
| PaymentGW current p99 latency | API | `GET /metrics/PaymentGW` | ~185ms (±5% jitter) |
| NotificationSvc SLA latency target | DB | `SELECT target FROM sla_targets WHERE service='NotificationSvc' AND metric='latency_p99_ms'` | 2000ms |
| NotificationSvc current latency | API | `GET /metrics/NotificationSvc` | ~3200ms (degraded!) |
| Total incidents for PaymentGW | DB | `SELECT COUNT(*) FROM incidents WHERE service='PaymentGW'` | 3 |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        USER QUESTION                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    AGENT ORCHESTRATOR                         │
│  Decides: retrieve from KB? call tool? both?                 │
│  + Conversation Memory [L4] (sliding window, 5 turns)        │
└──────┬──────────────────┬───────────────────┬───────────────┘
       │                  │                   │
       ▼                  ▼                   ▼
┌──────────────┐  ┌───────────────┐  ┌────────────────┐
│  BEDROCK KB  │  │ DATABASE TOOL │  │ METRICS TOOL   │
│  (L1, L2)    │  │ (L3)          │  │ (L3)           │
│              │  │               │  │                │
│ S3 → Embed  │  │ SQLite DB:    │  │ FastAPI:       │
│ → Retrieve  │  │ monthly_costs │  │ /status/{svc}  │
│ top-K chunks │  │ incidents     │  │ /metrics/{svc} │
│              │  │ sla_targets   │  │ /incidents     │
│              │  │ daily_metrics │  │                │
└──────────────┘  └───────────────┘  └────────────────┘
       │                  │                   │
       └──────────────────┴───────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    BEDROCK LLM (Claude)                       │
│  Input: system prompt + KB chunks + tool results + history   │
│  Output: answer with source citations                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     ANSWER + CITATIONS                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Common Mistakes & ECC Prevention

| Mistake | Consequence | ECC Prevention |
|---------|-------------|----------------|
| Build KB without reading docs | Miss conflicts for L2 | `/plan` forces data exploration first |
| Tool descriptions too vague ("gets data") | LLM calls wrong tool | `/code-review` catches vague descriptions |
| Skip numerical accuracy testing | L3 score = 0 | `/tdd` with exact expected values |
| Jump to L3 before L1 works | Nothing works | `/plan` enforces sequential phases |
| Hardcode responses | Trainer asks unseen questions | `/tdd` tests diverse questions |
| Monitoring API not running during demo | Tool calls fail | `/verify` checks connectivity |
| Forget Evidence Pack screenshots | Cap at 3/5 evidence score | `/save-session` tracks what's done |
| Code quality issues | Lost points in QnA | Auto `code-reviewer` catches issues |

---

## Bonus Features with ECC

### Bonus A: Observability Dashboard (+0.5)

```
/feature-dev Build observability UI showing pipeline internals:
- What chunks were retrieved (with scores)
- Which tool was called, with what params, and response
- Full LLM input (system prompt + context assembled)
- LLM reasoning and final output
Stack: Streamlit or simple HTML with server-sent events
```

### Bonus B: Agent Reasoning (+0.5)

```
/tdd Implement multi-step investigation for open-ended questions:
Input: "Is NotificationSvc in a healthy state?"
Agent must:
1. Plan approach (check status, metrics, incidents, SLA)
2. Execute each step (multiple tool calls)
3. Synthesize findings into structured report
4. Show reasoning steps visibly in output

Test: answer must include: current status, latency vs SLA, recent incidents, team info
```

### Bonus C: KB Auto-Sync (+0.5)

```
/tdd Implement KB re-sync when S3 docs change:
- S3 event notification → Lambda → StartIngestionJob on Bedrock KB
- Test: upload new doc → trigger sync → query returns new content
```

---

## Presentation Prep

### Architecture slide (3 min)

```
/aside Summarize our architecture in 3 bullet points for a presentation slide
```

### Decision log for Evidence Pack

Important decisions to document:
1. **Bedrock KB vs custom RAG** — why chose Bedrock KB (fast setup, managed embeddings)
2. **Raw function calling vs Bedrock Agents** — why raw (more control over routing)
3. **SQLite vs RDS** — why SQLite (local dev speed, no AWS cost for DB layer)
4. **What failed** — e.g., "LangChain RetrievalQA was too opaque, switched to raw Bedrock API"

### If live demo fails

Evidence Pack screenshots are accepted fallback. Always have screenshots ready.

---

## Session Management

| When | Command | Why |
|------|---------|-----|
| End of Thứ Ba | `/save-session` | Preserve data exploration findings |
| End of Thứ Năm | `/save-session` | L1-L3 progress, what works/doesn't |
| Start of Thứ Sáu | `/resume-session` | Pick up exactly where stopped |
| Before presentation | `/verify` | Final check everything works |

---

## Quick Cheat Sheet

| Moment | Command |
|--------|---------|
| Start project | `/plan` |
| Before coding anything | `/tdd` (tests first!) |
| Confused about AWS | `/docs <bedrock question>` |
| Quick question | `/aside <question>` |
| Build breaks | `/build-fix` |
| Before commit | `/verify` |
| Smart commit | `/prp-commit "L3 tools done"` |
| End of day | `/save-session` |
| Next morning | `/resume-session` |
| Final check | `/verify` then demo |
