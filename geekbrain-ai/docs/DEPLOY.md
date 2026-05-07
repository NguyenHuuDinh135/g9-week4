# Deployment Architecture

## Overview

GeekBrain AI deploys to AWS via GitHub Actions CI/CD using OIDC authentication (no stored credentials). A single GitHub secret (`AWS_DEPLOY_ROLE_ARN`) connects to an IAM role that can provision all resources.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GitHub Actions                                │
│  (OIDC → AssumeRoleWithWebIdentity → dinh-geekbrain-ai-w4-deploy)   │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                ▼                   ▼                   ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐
│   ECR Repos      │  │  Terraform State │  │  S3: KB Docs         │
│  - api           │  │  (S3 + DynamoDB) │  │  (36 .md files)      │
│  - monitoring    │  │                  │  │                      │
└────────┬─────────┘  └──────────────────┘  └──────────┬───────────┘
         │                                             │
         ▼                                             ▼
┌──────────────────────────────────┐   ┌───────────────────────────────┐
│        Lambda Functions          │   │   Bedrock Knowledge Base      │
│                                  │   │                               │
│  ┌────────────┐ ┌─────────────┐  │   │  Titan Embed V2 (1024 dim)   │
│  │ API Lambda │ │ Monitoring  │  │   │  ┌─────────────────────────┐  │
│  │ (FastAPI + │ │ Lambda      │  │   │  │ OpenSearch Serverless   │  │
│  │  Mangum)   │ │ (FastAPI +  │  │   │  │ (Vector Search)        │  │
│  │            │ │  Mangum)    │  │   │  └─────────────────────────┘  │
│  └─────┬──────┘ └──────┬──────┘  │   └───────────────────────────────┘
└────────┼────────────────┼────────┘
         │                │
         ▼                ▼
┌──────────────────────────────────┐
│       API Gateway (HTTP API)     │
│                                  │
│  - /api/* → API Lambda           │
│  - /monitoring/* → Monitoring    │
└──────────────────┬───────────────┘
                   │
                   │   ┌───────────────────────────────┐
                   │   │     CloudFront CDN             │
                   │   │                               │
                   │   │  ┌─────────────────────────┐  │
                   │   │  │ S3: Frontend (Next.js)  │  │
                   │   │  │ (Static Export)         │  │
                   │   │  └─────────────────────────┘  │
                   │   └───────────────────────────────┘
                   │
              End Users
```

## AWS Resources Created

| Resource | Name | Purpose |
|----------|------|---------|
| ECR | `dinh-geekbrain-ai-w4-api` | API Lambda container image |
| ECR | `dinh-geekbrain-ai-w4-monitoring` | Monitoring Lambda container image |
| Lambda | `dinh-geekbrain-ai-w4-api` | Main RAG + Tools API |
| Lambda | `dinh-geekbrain-ai-w4-monitoring` | Live metrics FastAPI |
| API Gateway | `dinh-geekbrain-ai-w4-api` | HTTP API for main backend |
| API Gateway | `dinh-geekbrain-ai-w4-monitoring-api` | HTTP API for monitoring |
| S3 | `dinh-geekbrain-ai-w4-kb-docs` | Knowledge base source documents |
| S3 | `dinh-geekbrain-ai-w4-frontend` | Next.js static files |
| CloudFront | `dinh-geekbrain-ai-w4` | CDN for frontend |
| OpenSearch Serverless | `dinh-geekbrain-ai-w4-kb` | Vector store for embeddings |
| Bedrock KB | `dinh-geekbrain-ai-w4-kb` | RAG knowledge base |
| IAM Role | `dinh-geekbrain-ai-w4-bedrock-kb-role` | Bedrock KB execution |
| IAM Role | `dinh-geekbrain-ai-w4-lambda-exec` | Lambda execution |
| IAM Role | `dinh-geekbrain-ai-w4-github-deploy` | CI/CD deploy (OIDC) |

## CI/CD Pipeline (4 Phases)

```
Phase 1: Base Infrastructure
├── Terraform Init (S3 backend)
├── Remove obsolete state resources
└── Terraform Apply -target (ECR, S3, CloudFront, OpenSearch Collection)

Phase 2: OpenSearch Index Creation
└── python3 create_index.py <endpoint>  (retries 10x @ 30s for policy propagation)

Phase 3: Build & Push Docker Images
├── Build monitoring image → ECR
├── Build API image (+ geekbrain.db) → ECR
└── Push both images

Phase 4: Full Terraform Apply
├── Terraform Apply (creates KB, Lambda, API Gateway)
├── Build frontend (Next.js)
├── Deploy to S3 + Invalidate CloudFront
└── Trigger KB Ingestion
```

## Bootstrap (One-Time Setup)

Run locally before first CI deploy:

```bash
cd geekbrain-ai/infra/bootstrap
terraform init
terraform apply
```

This creates:
- S3 bucket for Terraform state (`dinh-geekbrain-ai-w4-tfstate`)
- DynamoDB lock table (`dinh-geekbrain-ai-w4-tflock`)
- GitHub OIDC provider
- Deploy IAM role with required permissions

Then add the output `deploy_role_arn` as GitHub secret `AWS_DEPLOY_ROLE_ARN`.

## OpenSearch Index Creation Strategy

OpenSearch Serverless does NOT auto-create indexes. The vector index must exist before Bedrock KB can be created. Our approach:

1. **Separated from Terraform** — avoids Terraform provisioner failures blocking the entire apply
2. **Runs as CI step** with aggressive retry (10 attempts x 30s = 5 min max)
3. **Idempotent** — skips if index already exists (`resource_already_exists_exception`)
4. **SigV4 authenticated** — uses the deploy role's temporary credentials
5. **Data access policy** includes the deploy role ARN explicitly

### Why 403 Happens

OpenSearch Serverless data access policies take 2-5 minutes to propagate after:
- Collection first becomes ACTIVE
- Access policy is created/modified
- New principal is added

The retry loop handles this propagation window gracefully.

## Environment Variables (Lambda)

| Variable | Source | Lambda |
|----------|--------|--------|
| `BEDROCK_KB_ID` | Terraform output | API |
| `AWS_REGION_NAME` | `us-east-1` | API |
| `BEDROCK_MODEL_ID` | `anthropic.claude-sonnet-4-20250514` | API |
| `DATABASE_PATH` | `/var/task/geekbrain.db` | API |
| `MONITORING_API_URL` | Monitoring API Gateway URL | API |
| `ENVIRONMENT` | `production` | Monitoring |

## Secrets

| Secret | Location | Value |
|--------|----------|-------|
| `AWS_DEPLOY_ROLE_ARN` | GitHub Secrets | `arn:aws:iam::<account>:role/dinh-geekbrain-ai-w4-github-deploy` |

No other secrets are needed. All AWS service-to-service auth uses IAM roles.

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| 403 on index creation | Access policy propagation | Script retries automatically (5 min) |
| Lambda "no such image" | Image not pushed yet | Phase 3 runs before Phase 4 |
| KB creation fails | Index doesn't exist | Phase 2 creates index before Phase 4 |
| CloudFront 403 | OAI not configured | Check S3 bucket policy |
| TF state lock | Previous run crashed | `terraform force-unlock <id>` |
