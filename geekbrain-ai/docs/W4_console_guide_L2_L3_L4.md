# Hướng dẫn Test L2, L3, L4

> Bổ sung cho [W4_console_guide.md](./W4_console_guide.md) (cover L1)

---

## Level 2: Multi-Source RAG + Conflict Resolution

### Yêu cầu
L2 yêu cầu system phải:
1. Retrieve từ nhiều documents liên quan
2. Nhận diện document cũ (archived) vs mới (current)
3. Trả lời ưu tiên thông tin từ document mới nhất

### Test Cases

#### Test 2.1: API Rate Limit Conflict
```
Q: What is the API rate limit?
Expected: 1000 requests/min (from api_reference_v2.md)
NOT: 500 requests/min (from api_reference_v1_archived.md)
```

**Verify:** Response phải mention "1000 req/min" và optionally note rằng v1 nói 500 nhưng đã archived.

#### Test 2.2: Multi-document Synthesis
```
Q: Describe the NotificationSvc architecture and any known issues.
Expected: Combines architecture info from KB documents + mentions current degraded state from API
```

#### Test 2.3: Source Citation
```
Q: What authentication method does the platform use?
Expected: Answer cites specific document source(s)
```

### Cách đạt L2 trong Code
- System prompt (trong `config.py`) chứa instruction: "prefer newer version when documents conflict"
- File naming convention: `*_archived.md` = deprecated
- Retriever returns source filename → LLM can see which is archived

### Console Test (Bedrock KB)
1. Bedrock Console → KB → Test
2. Hỏi "What is the API rate limit?"
3. Check xem retrieved chunks có include cả v1 và v2 không
4. Check xem generated answer có prefer v2 không

---

## Level 3: Tool-Augmented RAG

### Yêu cầu
L3 yêu cầu system phải:
1. Detect khi nào cần gọi Database tool (historical data, costs, SLA)
2. Detect khi nào cần gọi Metrics API tool (current live data)
3. Return chính xác numerical values (no hallucination)
4. Combine tool results với KB documents khi cần

### Setup trước khi test

```bash
# Terminal 1: Start monitoring API
cd data_package/scripts
uv run uvicorn monitoring_api:app --port 8000

# Terminal 2: Verify database
sqlite3 data_package/scripts/geekbrain.db "SELECT COUNT(*) FROM monthly_costs;"
# Expected: 36

# Terminal 3: Run the agent
cd src
python -m src.main
```

### Test Cases

#### Test 3.1: Database — Cost Query
```
Q: What is the total cost of PaymentGW in Q1 2026?
Expected: $16,500
Source: DB (SUM of monthly_costs where service='PaymentGW' AND month IN ('2026-01','2026-02','2026-03'))
```

#### Test 3.2: Database — Incident Count
```
Q: How many incidents did PaymentGW have in Q1 2026?
Expected: 3 incidents (INC-001, INC-003, INC-005)
Source: DB (incidents table)
```

#### Test 3.3: API — Current Metrics
```
Q: What is the current p99 latency of PaymentGW?
Expected: ~185ms (±5% jitter, so 176-194ms range is acceptable)
Source: API /metrics/PaymentGW
```

#### Test 3.4: API — Degraded Service Detection
```
Q: Is NotificationSvc healthy right now?
Expected: NO — degraded, HIGH_LATENCY + ELEVATED_ERROR_RATE alerts active
Source: API /status/NotificationSvc
```

#### Test 3.5: API — SLA Breach Detection
```
Q: Is NotificationSvc meeting its SLA targets?
Expected: NO — p99 ~3200ms (target 2000ms), error rate ~2.1% (target 1.0%)
Source: DB (sla_targets) + API (current metrics) — requires BOTH tools
```

#### Test 3.6: Combined KB + Tools
```
Q: What are the cost optimization recommendations and how much are we currently spending?
Expected: KB docs about cost_optimization_initiative + DB query for actual costs
```

### Numerical Accuracy Table

| Query | Expected Value | Acceptable Range | Tool |
|-------|---------------|-----------------|------|
| PaymentGW Q1 cost | $16,500 | exact | DB |
| All services Q1 cost | $56,350 | exact | DB |
| Highest cost March 2026 | PaymentGW $7,500 | exact | DB |
| PaymentGW p99 latency | ~185ms | 176-194ms | API |
| NotificationSvc p99 | ~3200ms | 3040-3360ms | API |
| NotificationSvc error rate | ~2.1% | 2.0-2.2% | API |
| AuthSvc requests/min | ~28,000 | 26,600-29,400 | API |

### Troubleshooting L3

- **Agent không gọi tool:** Check system prompt có describe rõ WHEN to use each tool
- **SQL error:** Check database_tool.py chỉ cho phép SELECT
- **API timeout:** Verify monitoring_api.py đang chạy trên port 8000
- **Sai số liệu:** Metrics API có ±5% jitter mỗi lần call — gọi 2-3 lần lấy average

---

## Level 4: Conversation Memory

### Yêu cầu
L4 yêu cầu system phải:
1. Nhớ context từ câu hỏi trước (sliding window 5 turns)
2. Resolve pronoun references ("it", "that service", "its cost")
3. Build on previous answers without repeating full context

### Test Cases

#### Test 4.1: Pronoun Resolution
```
Turn 1: "Tell me about PaymentGW"
Turn 2: "What is its current latency?"
Expected Turn 2: Returns PaymentGW latency (~185ms), not asking "which service?"
```

#### Test 4.2: Follow-up Drill-down
```
Turn 1: "Which services had incidents in Q1 2026?"
Turn 2: "Show me details of the most severe one"
Expected Turn 2: Shows the P1/critical incident details from the list in Turn 1
```

#### Test 4.3: Context Switching
```
Turn 1: "What's the status of NotificationSvc?"
Turn 2: "What about AuthSvc?"
Turn 3: "Compare their error rates"
Expected Turn 3: Compares NotificationSvc (~2.1%) vs AuthSvc error rates
```

#### Test 4.4: Memory Window Limit
```
Turns 1-6: Ask about 6 different topics
Turn 7: Reference something from Turn 1
Expected: May NOT remember Turn 1 (outside 5-turn window) — this is acceptable behavior
```

#### Test 4.5: Memory Clear
```
Turn 1: "Tell me about PaymentGW"
Command: "clear" (resets memory)
Turn 2: "What is its current latency?"
Expected: Should ask clarification (no context about "its")
```

### Implementation Details

```python
# ConversationMemory trong src/memory/conversation.py
# - Sliding window: deque(maxlen=10) → 5 user + 5 assistant messages
# - History passed to Bedrock Converse API as previous messages
# - LLM sees last 5 turns + current query + KB context + tool results
```

### Console Test Flow (screenshot-worthy)

```
You: Tell me about PaymentGW architecture
Assistant: [KB] PaymentGW is the payment gateway service that...

You: How much did it cost in Q1 2026?
Assistant: [DB] PaymentGW total cost in Q1 2026 was $16,500...

You: Is it healthy right now?
Assistant: [API] PaymentGW is currently healthy with p99 latency ~185ms...

You: What about NotificationSvc?
Assistant: [API] NotificationSvc is currently DEGRADED with alerts...

You: Compare their costs
Assistant: [DB] PaymentGW Q1: $16,500 vs NotificationSvc Q1: $X,XXX...
```

---

## Evidence Collection Checklist

Cho mỗi level, cần:

### L1 Evidence
- [ ] Screenshot: KB sync successful (36 docs)
- [ ] Screenshot: Test query in Bedrock Console
- [ ] Log: CLI output showing retrieval + answer

### L2 Evidence
- [ ] Screenshot: Query about API rate limit → answer says 1000 (not 500)
- [ ] Log: Retrieved chunks showing both v1 and v2 docs
- [ ] Screenshot: System prompt showing conflict resolution instructions

### L3 Evidence
- [ ] Screenshot: Cost query → exact $16,500 answer
- [ ] Screenshot: Live metrics query → ~185ms latency
- [ ] Screenshot: NotificationSvc degraded detection
- [ ] Log: Tool call trace showing SQL query executed
- [ ] Log: Tool call trace showing API call made

### L4 Evidence
- [ ] Screenshot: Multi-turn conversation with pronoun resolution
- [ ] Screenshot: Follow-up question correctly using previous context
- [ ] Log: Memory buffer contents showing sliding window
- [ ] Screenshot: Memory clear resets context

---

## Quick Demo Script (5 phút)

Dùng script này cho presentation:

```
1. [L1] "What is the deployment policy?" → KB retrieval
2. [L2] "What is the API rate limit?" → conflict resolution (1000 not 500)
3. [L3] "How much did PaymentGW cost in Q1 2026?" → DB tool ($16,500)
4. [L3] "What is its current p99 latency?" → API tool (~185ms) + memory (remembers PaymentGW)
5. [L3] "Is NotificationSvc meeting its SLA?" → DB + API combined
6. [L4] "Compare it with PaymentGW" → memory resolves "it" = NotificationSvc
```
