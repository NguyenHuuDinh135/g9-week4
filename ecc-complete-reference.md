# Everything Claude Code (ECC) — Complete Reference Guide

> Version 1.10.0 | 48 Agents | 168 Skills | 79 Commands | Production Hooks

---

## Table of Contents

1. [Mental Model](#1-mental-model)
2. [Commands — Full I/O Reference](#2-commands)
3. [Agents — Auto-Dispatch Reference](#3-agents)
4. [Skills — Domain Knowledge](#4-skills)
5. [Hooks — Automated Pipeline](#5-hooks)
6. [Workflows — Live Recipes](#6-workflows)
7. [Multi-Model Collaboration](#7-multi-model)
8. [Continuous Learning](#8-learning)
9. [Session Management](#9-sessions)
10. [Selective Install](#10-selective-install)

---

## 1. Mental Model

| Layer | What | How to invoke | Runs when |
|-------|------|---------------|-----------|
| **Commands** | Quick actions | `/command-name` | User types it |
| **Skills** | Deep domain knowledge | Auto-loaded by context | File type, topic detected |
| **Agents** | Autonomous multi-step workers | Auto-dispatched or manual | Context triggers |
| **Hooks** | Automated checks | Always (pre/post tool use) | Every tool call |

---

## 2. Commands

### 2.1 `/plan`

| Field | Detail |
|-------|--------|
| **Purpose** | Lên kế hoạch trước khi code. KHÔNG viết code. |
| **Input** | Mô tả feature bằng ngôn ngữ tự nhiên |
| **Output** | Plan: requirements, risks, phases, dependencies, complexity |
| **Agent** | `planner` |
| **Blocks code?** | YES — chờ user confirm |

**Live workflow:**
```
User: /plan Add WebSocket real-time notifications

Claude (planner):
═══════════════════════════════════════
## Requirements
- Push notifications to connected clients
- Handle reconnection gracefully

## Phases
Phase 1: WebSocket server (2h)
Phase 2: Event system + queue (3h)
Phase 3: Client SDK (2h)
Phase 4: Tests (1h)

## Risks
- HIGH: Scaling beyond 10K concurrent
- MEDIUM: Message ordering

## Complexity: MEDIUM (8h)
WAITING FOR CONFIRMATION: Proceed? (yes/no/modify)
═══════════════════════════════════════

User: yes → starts implementation
User: modify: skip phase 3 → updates plan
```

---

### 2.2 `/prp-plan`

| Field | Detail |
|-------|--------|
| **Purpose** | Deep planning với codebase analysis + artifact output |
| **Input** | `<feature description>` hoặc `path/to/prd.md` |
| **Output** | `.claude/PRPs/plans/{name}.plan.md` |
| **Phases** | DETECT → PARSE → EXPLORE (8 searches) → RESEARCH → DESIGN → GENERATE |

**Live workflow:**
```
User: /prp-plan Add rate limiting middleware

Phase 2 EXPLORE (searches 8 categories):
  ✓ Similar: src/middleware/auth.ts (pattern to mirror)
  ✓ Naming: kebab-case middleware files
  ✓ Error handling: AppError at src/errors/
  ✓ Tests: vitest, __tests__/ directory

Phase 6 GENERATE:
  Saved: .claude/PRPs/plans/rate-limiting.plan.md
  Contains: 12 mandatory reading files, 5 patterns to mirror,
            8 tasks with VALIDATE criteria

→ Next: /prp-implement .claude/PRPs/plans/rate-limiting.plan.md
```

---

### 2.3 `/multi-plan` (CCG Plan)

| Field | Detail |
|-------|--------|
| **Purpose** | Multi-model collaborative planning |
| **Input** | Feature description |
| **Output** | `.claude/plan/{name}.md` + SESSION_IDs |
| **Models** | Codex (backend) + Gemini (frontend) in parallel |

**Live workflow:**
```
User: /multi-plan Build payment checkout with Stripe

Phase 2 (parallel):
  ┌─ Codex: "PaymentIntents + idempotency + webhooks"
  └─ Gemini: "Animated checkout, card input, loading states"

Cross-validation: consensus on PaymentIntents, divergence on confirmation UX
Resolution: server creates intent, client confirms via Stripe.js

Saved: .claude/plan/stripe-checkout.md
→ Next: /multi-execute .claude/plan/stripe-checkout.md
```

---

### 2.4 `/tdd`

| Field | Detail |
|-------|--------|
| **Purpose** | Test-Driven Development |
| **Input** | Function/feature description |
| **Output** | Tests (RED) → Implementation (GREEN) → Refactored (IMPROVE) |
| **Agent/Skill** | `tdd-guide` + `tdd-workflow` |

**Live workflow:**
```
User: /tdd validateApiKey function

Step 1 RED: Writes 3 test cases (expired, malformed, valid)
Step 2: Runs → ✗ 3 FAILED
Step 3 GREEN: Writes minimal implementation
Step 4: Runs → ✓ 3 PASSED
Step 5 REFACTOR: Extracts constants, improves naming
Step 6: Runs → ✓ 3 PASSED
Step 7: Coverage → 100% ✓
```

---

### 2.5 `/feature-dev`

| Field | Detail |
|-------|--------|
| **Purpose** | Full guided feature development (7 phases) |
| **Input** | Feature request |
| **Output** | Working feature, tested, reviewed |
| **Agents** | `code-explorer` → `code-architect` → `code-reviewer` |

**Live workflow:**
```
User: /feature-dev Add search autocomplete

Phase 1 Discovery: Identifies fuzzy search + debounce needs
Phase 2 Exploration: code-explorer traces existing search hook
Phase 3 Questions: "Debounce 300ms? Max 10 suggestions?"
Phase 4 Architecture: code-architect blueprints 3 components
Phase 5 Implementation: Builds hook + component + endpoint
Phase 6 Review: code-reviewer finds "MEDIUM: add loading state"
Phase 7 Summary: Done with follow-up items listed
```

---

### 2.6 `/multi-execute` (CCG Execute)

| Field | Detail |
|-------|--------|
| **Purpose** | Multi-model execution with dual audit |
| **Input** | `.claude/plan/{name}.md` or task description |
| **Output** | Production code, audited |
| **Flow** | Read Plan → Context → Prototype (parallel) → Claude Implements → Dual Audit |

**Live workflow:**
```
User: /multi-execute .claude/plan/stripe-checkout.md

Phase 3 (parallel background):
  ┌─ Codex: produces diff for API routes + webhook
  └─ Gemini: produces diff for CheckoutForm + PaymentStatus

Phase 4: Claude refactors both → applies to files → runs tsc + vitest ✓

Phase 5 (parallel audit):
  ┌─ Codex: "PASS — idempotency correct"
  └─ Gemini: "1 issue: missing aria-label" → fixed

Result: All files created, both auditors pass ✓
```

---

### 2.7 `/multi-frontend`

| Field | Detail |
|-------|--------|
| **Purpose** | Frontend workflow, Gemini-led |
| **Input** | UI task description |
| **Trust rule** | Gemini = frontend authority |

**Live workflow:**
```
User: /multi-frontend Bento grid dashboard with animations

[Mode: Ideation] Gemini proposes: CSS Grid vs Masonry → User picks Grid
[Mode: Plan] Gemini plans component structure
[Mode: Execute] Claude implements
[Mode: Optimize] Gemini reviews: "Add prefers-reduced-motion"
[Mode: Review] Final pass ✓
```

---

### 2.8 `/multi-backend`

| Field | Detail |
|-------|--------|
| **Purpose** | Backend workflow, Codex-led |
| **Input** | Backend task |
| **Trust rule** | Codex = backend authority |

**Live workflow:**
```
User: /multi-backend Retry queue for failed webhooks

[Mode: Ideation] Codex proposes: Redis queue vs SQS → User picks Redis
[Mode: Execute] Claude implements RetryQueue service
[Mode: Optimize] Codex: "Add circuit breaker after 5 failures"
```

---

### 2.9 `/code-review`

| Field | Detail |
|-------|--------|
| **Purpose** | Security + quality review |
| **Input** | Blank (local) or PR number/URL |
| **Output** | CRITICAL/HIGH/MEDIUM/LOW findings |

**Live workflow — Local:**
```
User: /code-review

CRITICAL: src/api/users.ts:42 — SQL injection
HIGH: src/config/index.ts:8 — Hardcoded API key
MEDIUM: src/services/cache.ts:15 — Function 67 lines

Verdict: BLOCKED (1 CRITICAL)
```

**Live workflow — PR:**
```
User: /code-review 87

7-category review across 12 files
Decision: REQUEST CHANGES (1 security, 1 missing test)
Posted to GitHub ✓
Saved: .claude/PRPs/reviews/pr-87-review.md
```

---

### 2.10 `/verify`

| Field | Detail |
|-------|--------|
| **Purpose** | Full verification loop |
| **Input** | Optional: `quick` |
| **Output** | PASS/FAIL per check |

**Live workflow:**
```
User: /verify

[1/5] Types:    tsc --noEmit     ✓ PASS
[2/5] Lint:     eslint           ✓ PASS
[3/5] Tests:    vitest run       ✓ PASS (47/47)
[4/5] Build:    pnpm build       ✓ PASS
[5/5] Security: scan             ✓ PASS

VERDICT: ALL PASS — safe to commit
```

---

### 2.11 `/build-fix`

| Field | Detail |
|-------|--------|
| **Purpose** | Auto-fix build errors one at a time |
| **Input** | None (auto-detects build system) |
| **Agent** | `build-error-resolver` |
| **Safety** | Stops if fix introduces MORE errors |

**Live workflow:**
```
User: /build-fix

Running pnpm build... 5 errors
Error 1: TS2307 Cannot find module → fix import → 4 remain
Error 2: TS2345 Type mismatch → add nullish coalescing → 3 remain
...
Summary: 5/5 fixed, build PASS ✓
```

---

### 2.12 `/prp-commit`

| Field | Detail |
|-------|--------|
| **Purpose** | Smart commit with natural language targeting |
| **Input** | Optional: what to stage |

**Examples:**
| You type | What happens |
|----------|--------------|
| `/prp-commit` | Stages all, auto-generates message |
| `/prp-commit staged` | Commits only already-staged |
| `/prp-commit *.ts` | Stages TypeScript files |
| `/prp-commit except tests` | Everything except test files |
| `/prp-commit the auth changes` | Finds auth-related files |

---

### 2.13 `/prp-pr`

| Field | Detail |
|-------|--------|
| **Purpose** | Create GitHub PR |
| **Input** | Optional: `[base-branch] [--draft]` |
| **Phases** | VALIDATE → DISCOVER → PUSH → CREATE → VERIFY |

**Live workflow:**
```
User: /prp-pr --draft

✓ On feat/jwt-auth, 5 commits ahead
Found .github/PULL_REQUEST_TEMPLATE.md
Pushed: git push -u origin HEAD ✓
Created: PR #45 "feat: JWT authentication"
URL: github.com/org/repo/pull/45
```

---

### 2.14 `/gan-build`

| Field | Detail |
|-------|--------|
| **Purpose** | GAN-style iterative build |
| **Input** | `"brief"` + `--max-iterations N` `--pass-threshold N` |
| **Agents** | `gan-planner` → `gan-generator` ↔ `gan-evaluator` |

**Live workflow:**
```
User: /gan-build "Task manager with Kanban" --max-iterations 8

Iter 1: Generator builds → Evaluator: 3.8/10
Iter 2: Adds drag-drop → 5.2/10
Iter 3: Adds animations → 6.1/10
Iter 4: Adds responsive + micro-interactions → 7.3/10 PASS ✓
```

---

### 2.15 `/gan-design`

| Field | Detail |
|-------|--------|
| **Purpose** | Visual quality focused (higher threshold 7.5) |
| **Rubric** | Design: 0.35, Originality: 0.30, Craft: 0.25, Functionality: 0.10 |

**Live workflow:**
```
User: /gan-design "3D museum with CSS perspective"

Generator: "Visual excellence > feature completeness"
Evaluator: "Would this win a design award?"
6 iterations → 7.6/10 PASS ✓
```

---

### 2.16 `/santa-loop`

| Field | Detail |
|-------|--------|
| **Purpose** | Adversarial dual-review (2 models must both approve) |
| **Input** | `[file-or-glob]` |
| **Max rounds** | 3 |

**Live workflow:**
```
User: /santa-loop src/services/payment/

Round 1:
  Reviewer A (Claude): NAUGHTY — "Race condition"
  Reviewer B (Codex): NAUGHTY — "Missing idempotency"
→ Fixed, committed

Round 2:
  Reviewer A: NICE ✓
  Reviewer B: NICE ✓
CONVERGED — ship it ✓
```

---

### 2.17 `/loop-start`

| Field | Detail |
|-------|--------|
| **Purpose** | Start autonomous loop |
| **Input** | `[pattern] [--mode safe|fast]` |
| **Patterns** | `sequential`, `continuous-pr`, `rfc-dag`, `infinite` |

**Live workflow:**
```
User: /loop-start continuous-pr --mode safe

✓ Tests pass, hooks active
Pattern: pick task → implement → test → PR → next
Stop: queue empty OR 3 consecutive failures
Saved: .claude/plans/continuous-pr-runbook.md
Start: node loop.js | Monitor: /loop-status
```

---

### 2.18 `/review-pr`

| Field | Detail |
|-------|--------|
| **Purpose** | Multi-agent PR review (6 reviewers) |
| **Input** | `[PR-number] [--focus=...]` |
| **Agents** | code-reviewer, comment-analyzer, pr-test-analyzer, silent-failure-hunter, type-design-analyzer, code-simplifier |

**Live workflow:**
```
User: /review-pr 87

6 agents in parallel...
Critical (1): SQL injection
Important (2): missing test, swallowed error
Advisory (1): simplify nested ternary
All findings confidence >= 80%
```

---

### 2.19 `/orchestrate`

| Field | Detail |
|-------|--------|
| **Input** | `feature|bugfix|refactor|security|custom <agents> <desc>` |

**Live workflow:**
```
User: /orchestrate custom "architect,tdd-guide,code-reviewer" "Redesign cache"

architect → designs cache architecture
tdd-guide → implements with TDD
code-reviewer → reviews result
Each output feeds the next ✓
```

---

### 2.20 `/devfleet`

| Field | Detail |
|-------|--------|
| **Purpose** | Fleet of parallel dev agents |
| **Input** | Task description |

**Live workflow:**
```
User: /devfleet "Implement 5 API endpoints"

Shows DAG: 5 parallel workers
Gets approval → dispatches
Reports: mission IDs, files changed, next steps
```

---

### 2.21 Session & Utility Commands

| Command | Input | Output | Live Example |
|---------|-------|--------|-------------|
| `/save-session` | None | Session state file | 9-section state → `~/.claude/session-data/` |
| `/resume-session` | date/path | Structured briefing | Loads last session, waits for direction |
| `/aside <q>` | Question | Quick answer | Answers without losing task context |
| `/checkpoint create <n>` | Name | Git checkpoint | Marks milestone |
| `/test-coverage` | None | Coverage + generated tests | Finds gaps, generates tests to 80%+ |
| `/refactor-clean` | None | Dead code removed | knip analysis → safe delete loop |
| `/quality-gate [path]` | Path + flags | Format/lint/type | Quick quality check |
| `/model-route` | Task desc | Model recommendation | haiku/sonnet/opus suggestion |
| `/context-budget` | None | Context usage report | Token savings suggestions |
| `/docs <query>` | Library question | Live docs | Context7 fetches current API docs |
| `/update-codemaps` | None | Architecture docs | Token-lean codemap files |
| `/learn` | None | Extracted skill | Session pattern → learned skill |
| `/evolve` | `--generate` | Skill/command/agent candidates | Clusters instincts |
| `/prune` | `--dry-run` | Deleted old instincts | Housekeeping |
| `/skill-create` | `--commits N` | SKILL.md from git | Project conventions |
| `/hookify <behavior>` | Behavior | Hook rule file | Prevent repeated mistakes |
| `/prompt-optimize` | Prompt | Optimized version | ECC component recommendations |

---

### 2.22 Language-Specific Commands

| Command | Trigger | Agent |
|---------|---------|-------|
| `/go-build` | Go build fails | `go-build-resolver` |
| `/go-review` | Go code changed | `go-reviewer` |
| `/rust-build` | Cargo fails | `rust-build-resolver` |
| `/rust-review` | Rust changed | `rust-reviewer` |
| `/kotlin-build` | Gradle fails | `kotlin-build-resolver` |
| `/kotlin-review` | Kotlin changed | `kotlin-reviewer` |
| `/cpp-build` | CMake/gcc fails | `cpp-build-resolver` |
| `/cpp-review` | C++ changed | `cpp-reviewer` |
| `/flutter-build` | Dart analyze fails | `dart-build-resolver` |
| `/flutter-review` | Flutter changed | `flutter-reviewer` |
| `/python-review` | Python changed | `python-reviewer` |
| `/gradle-build` | Gradle fails | `java-build-resolver` |

---

## 3. Agents

### Auto-Dispatch (no user action needed)

| Trigger | Agent |
|---------|-------|
| Code written/modified | `code-reviewer` |
| .ts/.js touched | `typescript-reviewer` |
| .py touched | `python-reviewer` |
| .go touched | `go-reviewer` |
| Build fails | `build-error-resolver` |
| Auth/payment code | `security-reviewer` |
| Complex feature | `planner` |
| Bug fix | `tdd-guide` |
| Architecture question | `architect` |

### All 48 Agents

| Category | Agents |
|----------|--------|
| **Planning** | planner, code-architect, code-explorer |
| **Quality** | code-reviewer, typescript-reviewer, python-reviewer, go-reviewer, rust-reviewer, kotlin-reviewer, java-reviewer, cpp-reviewer, flutter-reviewer, csharp-reviewer |
| **Security** | security-reviewer, healthcare-reviewer |
| **Build Fix** | build-error-resolver, go-build-resolver, rust-build-resolver, kotlin-build-resolver, java-build-resolver, cpp-build-resolver, dart-build-resolver, pytorch-build-resolver |
| **Testing** | tdd-guide, e2e-runner |
| **Design** | architect, a11y-architect |
| **GAN** | gan-planner, gan-generator, gan-evaluator |
| **Ops** | loop-operator, harness-optimizer, performance-optimizer |
| **Docs** | doc-updater, docs-lookup |
| **Maintenance** | refactor-cleaner, code-simplifier |
| **Analysis** | comment-analyzer, silent-failure-hunter, type-design-analyzer, pr-test-analyzer, conversation-analyzer |
| **Open Source** | opensource-forker, opensource-sanitizer, opensource-packager |
| **Other** | database-reviewer, seo-specialist, chief-of-staff |

---

## 4. Skills (168 total)

Skills auto-activate based on file types and context.

| Domain | Key Skills |
|--------|-----------|
| **AI/Agents** | claude-api, agentic-engineering, autonomous-loops, cost-aware-llm-pipeline, prompt-optimizer |
| **Web** | frontend-patterns, frontend-design, e2e-testing, backend-patterns, nestjs-patterns |
| **Python** | python-patterns, python-testing, django-patterns, fastapi-python |
| **Database** | postgres-patterns, database-migrations, jpa-patterns, clickhouse-io |
| **Security** | security-review, security-scan, security-bounty-hunter, defi-amm-security |
| **DevOps** | deployment-patterns, docker-patterns, github-ops, dashboard-builder |
| **Mobile** | android-clean-architecture, dart-flutter-patterns, kotlin-coroutines-flows, swiftui-patterns |
| **Research** | deep-research, exa-search, research-ops, market-research |
| **Content** | article-writing, brand-voice, content-engine, seo |
| **ECC Meta** | configure-ecc, workspace-surface-audit, agent-sort, continuous-learning-v2 |

---

## 5. Hooks

### Pipeline

```
PRE-TOOL-USE                     POST-TOOL-USE
├─ Bash: GateGuard (first cmd)   ├─ Write/Edit: prettier
├─ Bash: quality checks          ├─ Write/Edit: eslint --fix
├─ Bash: tmux/push guards        └─ Write/Edit: tsc --noEmit
└─ Write: 800 line max

STOP                             OTHER
└─ Final build verification      └─ GitKraken sync on all events
```

### GateGuard

First Bash each session requires:
1. User request in 1 sentence
2. What command verifies/produces

Bypass: `ECC_GATEGUARD=off`

---

## 6. Workflows

### A: Feature Zero → PR
```
/plan → confirm → /tdd → implement → /verify → /code-review → /prp-commit → /prp-pr
```

### B: Critical Feature (Multi-Model)
```
/multi-plan → confirm → /multi-execute → /santa-loop → /prp-commit → /prp-pr
```

### C: Quick Bug Fix
```
/tdd (reproduce) → fix → /verify → /prp-commit
```

### D: Design-First UI
```
/gan-design "brief" → iterations until 7.5 → /verify → /prp-pr
```

### E: Large Refactor
```
/plan → /devfleet (parallel) → /refactor-clean → /test-coverage → /santa-loop → /prp-pr
```

### F: End of Day
```
/save-session → [next day] → /resume-session
```

---

## 7. Multi-Model

| Model | Role | Authority |
|-------|------|-----------|
| **Claude** | Code sovereign (all writes) | Orchestration, refactoring |
| **Codex** | Backend authority | Logic, security, performance |
| **Gemini** | Frontend authority | UI/UX, accessibility, design |

Rules: External models produce dirty prototypes → Claude refactors to production. External models have ZERO write access.

---

## 8. Learning

```
/learn → instinct → confidence builds → /evolve → skill/command/agent
/prune → delete old instincts
/skill-create → SKILL.md from git history
```

---

## 9. Sessions

| Command | When |
|---------|------|
| `/save-session` | End of work |
| `/resume-session` | Start next day |
| `/checkpoint create` | Milestone |
| `/checkpoint verify` | Compare progress |

---

## 10. Selective Install

```
/agent-sort     → DAILY vs LIBRARY classification per repo
/configure-ecc  → Interactive project-level installer
```

---

## Quick Reference

| I want to... | Command |
|--------------|---------|
| Plan a feature | `/plan` or `/prp-plan` |
| Build with tests first | `/tdd` |
| Multi-model build | `/multi-execute` |
| Review my code | `/code-review` |
| Review a PR | `/review-pr 123` |
| Verify before commit | `/verify` |
| Fix build errors | `/build-fix` |
| Smart commit | `/prp-commit` |
| Create PR | `/prp-pr` |
| Iterative build | `/gan-build "brief"` |
| Adversarial review | `/santa-loop` |
| Remove dead code | `/refactor-clean` |
| Save progress | `/save-session` |
| Resume tomorrow | `/resume-session` |
| Quick side question | `/aside <q>` |
| Look up docs | `/docs <query>` |
