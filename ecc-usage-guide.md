# ECC Usage Guide — Your Setup

**Version:** 1.10.0 | **Model:** Opus 4.6 (1M context) via Bedrock  
**48 agents** | **168 skills** | **79 commands** | **Production hooks**

---

## 1. Mental Model — 3 Layers

| Layer | What | How to invoke |
|-------|------|---------------|
| **Commands** (`/slash`) | Quick actions, one-shot | Type `/command-name` |
| **Skills** (deep reference) | Domain knowledge, workflows | Auto-loaded by context or via `/skill-name` |
| **Agents** (autonomous workers) | Multi-step specialized tasks | Auto-dispatched or via `Agent()` tool |

---

## 2. Commands — Top 20 You'll Use Daily

### Development Flow
| Command | Purpose |
|---------|---------|
| `/plan` | Plan before coding — PRD, architecture, tasks |
| `/feature-dev` | Full feature dev workflow (plan → TDD → review) |
| `/tdd` | Write tests first, then implement |
| `/code-review` | Review current changes |
| `/verify` | Run full verification loop (lint, test, build) |
| `/build-fix` | Auto-fix build errors |

### Git & PR
| Command | Purpose |
|---------|---------|
| `/prp-plan` | Plan PR scope with deep codebase analysis |
| `/prp-implement` | Implement planned PR |
| `/prp-commit` | Smart commit with conventional format |
| `/prp-pr` | Create PR with full summary |
| `/review-pr` | Review an existing PR |

### Multi-Agent
| Command | Purpose |
|---------|---------|
| `/multi-plan` | Parallel planning across domains (Codex + Gemini) |
| `/multi-execute` | Execute tasks with multi-model collaboration |
| `/multi-frontend` | Frontend-specific work (Gemini-led) |
| `/multi-backend` | Backend-specific work (Codex-led) |
| `/orchestrate` | Coordinate complex multi-agent workflows |
| `/devfleet` | Launch fleet of dev agents |

### Maintenance
| Command | Purpose |
|---------|---------|
| `/prune` | Remove old instincts |
| `/refactor-clean` | Dead code removal with test safety |
| `/quality-gate` | Run quality checks on path |
| `/test-coverage` | Analyze and improve coverage to 80%+ |

---

## 3. Agents — When They Auto-Activate

You don't need to call agents manually — they trigger by context:

```
You write code         → code-reviewer fires
You ask to build       → build-error-resolver if it fails
You touch auth/crypto  → security-reviewer flags it
You start a feature    → planner creates implementation plan
You fix a bug          → tdd-guide ensures test-first
```

### Language-Specific Reviewers (auto-dispatch)
- **typescript-reviewer** — TS/JS projects
- **python-reviewer** — Python
- **go-reviewer** / **go-build-resolver** — Go
- **rust-reviewer** / **rust-build-resolver** — Rust
- **kotlin-reviewer** / **kotlin-build-resolver** — Kotlin/Android
- **java-reviewer** / **java-build-resolver** — Java/Spring
- **cpp-reviewer** / **cpp-build-resolver** — C/C++
- **flutter-reviewer** / **dart-build-resolver** — Flutter/Dart

### Specialized Agents
- **database-reviewer** — Schema design, query optimization
- **healthcare-reviewer** — Clinical safety, PHI compliance
- **seo-specialist** — Technical SEO audits
- **pytorch-build-resolver** — CUDA/tensor errors
- **e2e-runner** — Playwright E2E tests
- **loop-operator** — Run autonomous loops safely
- **gan-planner/generator/evaluator** — GAN-style iterative dev

---

## 4. Skills — Grouped by Domain

### AI/Agent Engineering
`agentic-engineering`, `ai-first-engineering`, `autonomous-loops`, `continuous-agent-loop`, `enterprise-agent-ops`, `agent-harness-construction`, `cost-aware-llm-pipeline`, `prompt-optimizer`, `token-budget-advisor`, `claude-api`

### Web/Frontend
`frontend-patterns`, `frontend-design`, `frontend-slides`, `backend-patterns`, `nestjs-patterns`, `e2e-testing`, `remotion-video-creation`

### Mobile
`android-clean-architecture`, `compose-multiplatform-patterns`, `dart-flutter-patterns`, `kotlin-coroutines-flows`, `swift-concurrency-6-2`, `swiftui-patterns`, `liquid-glass-design`, `foundation-models-on-device`

### Database
`postgres-patterns`, `database-migrations`, `jpa-patterns`, `clickhouse-io`

### Security
`security-review`, `security-scan`, `security-bounty-hunter`, `defi-amm-security`, `healthcare-phi-compliance`, `hipaa-compliance`, `llm-trading-agent-security`, `nodejs-keccak256`

### DevOps
`deployment-patterns`, `docker-patterns`, `dmux-workflows`, `github-ops`, `dashboard-builder`

### Content/Marketing
`article-writing`, `brand-voice`, `content-engine`, `crosspost`, `x-api`, `seo`, `investor-materials`, `investor-outreach`, `lead-intelligence`

### Media
`fal-ai-media`, `manim-video`, `remotion-video-creation`, `ui-demo`, `video-editing`, `videodb`

### Industry-Specific
`carrier-relationship-management`, `customs-trade-compliance`, `energy-procurement`, `inventory-demand-planning`, `logistics-exception-management`, `production-scheduling`, `quality-nonconformance`, `returns-reverse-logistics`, `nutrient-document-processing`

---

## 5. Hooks — What Runs Automatically

Your hooks.json (46KB) has a **consolidated dispatcher** pattern:

| Hook | Trigger | What It Does |
|------|---------|--------------|
| `pre:bash:dispatcher` | Before any Bash | GateGuard fact-forcing, quality checks, tmux guards |
| `pre:write` | Before file writes | Size guard (800 line max), format checks |
| `post:write/edit` | After file changes | Auto-format, lint |
| GitKraken hooks | All events | Sync with GitKraken CLI |

### GateGuard
First Bash command each session requires declaring:
1. What the user asked for
2. What the command verifies

Bypass: set `ECC_GATEGUARD=off` or add to `ECC_DISABLED_HOOKS`.

---

## 6. Workflow Recipes

### Recipe A: New Feature (Full Pipeline)
```
/plan                  → Create implementation plan
/tdd                   → Write tests first
[implement]            → Code the feature
/code-review           → Auto-review
/verify                → Full quality gate
/prp-commit            → Commit with conventional format
/prp-pr                → Create PR
```

### Recipe B: Quick Bug Fix
```
/tdd                   → Write failing test for the bug
[fix]                  → Minimal fix
/verify                → Ensure nothing broke
/prp-commit            → Commit
```

### Recipe C: Large Refactor
```
/plan                  → Scope the refactor
/multi-execute         → Parallel agents on independent modules
/refactor-clean        → Remove dead code
/quality-gate          → Validate
```

### Recipe D: Research then Build
```
[deep-research skill]  → Research with Exa + firecrawl
/plan                  → Architecture from findings
/feature-dev           → Full implementation pipeline
```

### Recipe E: Autonomous Loop
```
/loop-start            → Start autonomous development loop
/loop-status           → Check progress
[loop-operator agent monitors and intervenes if stalled]
```

---

## 7. Advanced Features

### GAN-Style Iterative Development
```
/gan-design            → Planner creates spec + rubric (design-focused)
/gan-build             → Generator implements, Evaluator tests live app
                         Iterates until quality threshold met (default 7.0)
```

### Multi-Model Collaboration
```
/multi-plan            → Codex + Gemini analyze in parallel → plan
/multi-execute         → Codex prototypes backend, Gemini prototypes frontend
                         Claude refactors to production → dual audit
/multi-frontend        → Gemini-led frontend workflow
/multi-backend         → Codex-led backend workflow
```

### Santa Loop (Adversarial Review)
```
/santa-loop            → 2 independent reviewers (different models)
                         Both must return NICE before code ships
                         Max 3 rounds of fix → re-review
```

### Continuous Learning
```
/learn                 → Extract patterns from current session
/learn-eval            → Evaluate learned patterns
/evolve                → Evolve instincts into skills/commands/agents
/prune                 → Delete old unreviewed instincts
```

### Session Management
```
/save-session          → Persist session state (9 sections)
/resume-session        → Resume from saved state
/sessions              → List saved sessions
/checkpoint            → Save progress checkpoint
```

### Harness Optimization
```
/harness-audit         → Analyze harness reliability/cost
/context-budget        → Monitor context usage
/model-route           → Route to optimal model per task
```

---

## 8. Selective Install (cho du an cu the)

ECC supports **agent-sort** to only install what a project needs:

```
/agent-sort            → Analyze repo, recommend DAILY vs LIBRARY skills
/configure-ecc         → Interactive installer for project-level config
```

This avoids loading all 168 skills for every project.

---

## 9. Tips

1. **Don't call agents manually** — harness auto-dispatches based on context
2. **Parallel is default** — `/multi-*` commands run multiple agents simultaneously
3. **GateGuard is your friend** — prevents destructive commands, declare intent then proceed
4. **Skills auto-load** — working with Go? Go skills automatically activate
5. **`/verify` before every commit** — verification loop runs lint + test + build
6. **`/plan` for anything > 1 file** — avoid coding before thinking

---

## 10. Model Routing

| Model | When Used | Cost |
|-------|-----------|------|
| **Opus 4.6** (current) | Main session, complex reasoning, architecture | Highest |
| **Sonnet 4.6** | Implementation work, multi-agent workers | Medium |
| **Haiku 4.5** | Lightweight agents, frequent invocation | Lowest |
| **Codex** (external) | Backend authority, logic, algorithms | Via wrapper |
| **Gemini** (external) | Frontend authority, UI/UX design | Via wrapper |

`/model-route` recommends optimal model per task.

---

## 11. Command Comparison

| Need | Quick/Simple | Deep/Thorough |
|------|-------------|---------------|
| Plan | `/plan` | `/prp-plan` |
| Implement | `/tdd` | `/feature-dev` |
| Multi-model plan | — | `/multi-plan` |
| Multi-model build | — | `/multi-execute` |
| Frontend | `/tdd` | `/multi-frontend` |
| Backend | `/tdd` | `/multi-backend` |
| Review (local) | `/code-review` | `/santa-loop` |
| Review (PR) | `/code-review 123` | `/review-pr 123` |
| Commit | `git commit` | `/prp-commit` |
| PR | `gh pr create` | `/prp-pr` |
| Iterative build | — | `/gan-build` |
| Iterative design | — | `/gan-design` |
| Autonomous | — | `/loop-start` |
| Fleet | — | `/devfleet` |
