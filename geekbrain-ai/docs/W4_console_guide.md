# Hướng dẫn Hands-on: Tạo Bedrock Knowledge Base trên AWS Console

> Region: **us-east-1 (N. Virginia)**

## Điều kiện tiên quyết

1. AWS Account với quyền admin hoặc IAM permissions cho: S3, Bedrock, OpenSearch Serverless, IAM
2. Request model access cho **Titan Text Embeddings V2** và **Claude Sonnet** tại:
   - Console → Amazon Bedrock → Model access → Manage model access → Check 2 models → Request access
   - Chờ ~5 phút cho status chuyển sang "Access granted"

---

## Bước 1: Tạo S3 Bucket và Upload Documents

### 1.1 Tạo Bucket

1. Mở **S3 Console** → Create bucket
2. Cấu hình:
   - Bucket name: `geekbrain-ai-w4-kb-docs` (hoặc tên unique)
   - Region: `us-east-1`
   - Block all public access: **ON** (giữ mặc định)
   - Bucket Versioning: **Enable**
   - Server-side encryption: **SSE-S3 (AES-256)**
3. Click **Create bucket**

### 1.2 Upload 36 .md Files

1. Mở bucket vừa tạo → Create folder → Name: `knowledge_base` → Create
2. Mở folder `knowledge_base` → Upload → Add files
3. Chọn tất cả 36 file `.md` từ `data_package/knowledge_base/`
4. Click **Upload**

> **Verify:** Bucket → knowledge_base/ → 36 objects

---

## Bước 2: Tạo Knowledge Base trên Bedrock Console

### 2.1 Mở Bedrock KB

1. Mở **Amazon Bedrock Console** → Left menu → Orchestration → Knowledge bases
2. Click **Create knowledge base**

### 2.2 Provide knowledge base details

| Field | Value |
|-------|-------|
| Knowledge base name | `geekbrain-ai-w4-kb` |
| Description | `RAG knowledge base for GeekBrain AI fintech Q&A system` |
| IAM permissions | **Create and use a new service role** |
| Service role name | `AmazonBedrockExecutionRoleForKnowledgeBase_geekbrain` |

Click **Next**

### 2.3 Configure data source

| Field | Value |
|-------|-------|
| Data source name | `geekbrain-s3-source` |
| S3 URI | `s3://geekbrain-ai-w4-kb-docs/knowledge_base/` |

**Chunking strategy:**
- Chọn **Fixed size chunking**
- Max tokens: `512`
- Overlap percentage: `20`

Click **Next**

### 2.4 Select embeddings model and configure vector store

| Field | Value |
|-------|-------|
| Embeddings model | **Titan Text Embeddings V2** |
| Vector dimensions | `1024` (mặc định cho Titan V2) |
| Vector database | **Quick create a new vector store** |

> Quick create sẽ tự tạo OpenSearch Serverless collection. Đơn giản nhất cho dev.

Click **Next** → Review → **Create knowledge base**

> **Chờ 3-5 phút** cho OpenSearch Serverless collection được provision.

---

## Bước 3: Sync (Ingestion) Data Source

1. Sau khi KB status = **Ready**, click vào tên KB
2. Trong tab **Data sources** → Chọn data source `geekbrain-s3-source`
3. Click **Sync**
4. Chờ status chuyển từ `In progress` → `Completed`

> **Expected:** 36 files ingested, ~100-150 chunks created

### Verify Sync

- Status: **Available**
- Last sync: Timestamp vừa sync
- Number of documents: **36**

---

## Bước 4: Test Retrieve trên Console

### 4.1 Test trong Bedrock Console

1. Mở KB → Tab **Test knowledge base** (panel bên phải)
2. Chọn model: **Claude 3.5 Sonnet** (hoặc Claude Sonnet 4)
3. Nhập câu hỏi test:

**Test L1 - Simple retrieval:**
```
What is the deployment policy for production services?
```

**Test L2 - Conflict resolution:**
```
What is the API rate limit for the platform?
```
(Nên trả lời 1000 req/min từ v2, không phải 500 từ v1 archived)

**Test L2 - Multi-source:**
```
Tell me about the NotificationSvc architecture and its current issues.
```

### 4.2 Test với AWS CLI

```bash
# Retrieve only (no generation)
aws bedrock-agent-runtime retrieve \
  --knowledge-base-id <KB_ID> \
  --retrieval-query '{"text": "deployment policy"}' \
  --retrieval-configuration '{"vectorSearchConfiguration": {"numberOfResults": 5}}' \
  --region us-east-1

# Retrieve and Generate
aws bedrock-agent-runtime retrieve-and-generate \
  --input '{"text": "What is the incident response policy?"}' \
  --retrieve-and-generate-configuration '{
    "type": "KNOWLEDGE_BASE",
    "knowledgeBaseConfiguration": {
      "knowledgeBaseId": "<KB_ID>",
      "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-sonnet-4-20250514"
    }
  }' \
  --region us-east-1
```

---

## Bước 5: Lấy KB ID cho Code

### Từ Console:
1. Bedrock → Knowledge bases → Click KB name
2. Copy **Knowledge base ID** (format: `XXXXXXXXXX`)

### Từ CLI:
```bash
aws bedrock-agent list-knowledge-bases --region us-east-1 \
  --query 'knowledgeBaseSummaries[?name==`geekbrain-ai-w4-kb`].knowledgeBaseId' \
  --output text
```

Dùng KB ID này trong `src/config.py`:
```python
BEDROCK_KB_ID = "XXXXXXXXXX"  # from env var in production
```

---

## Bước 6: Cấu hình IAM cho Application (nếu chạy local)

Nếu chạy app từ local machine, cần IAM user/role với permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:Retrieve",
        "bedrock:RetrieveAndGenerate"
      ],
      "Resource": "*"
    }
  ]
}
```

**Setup AWS credentials:**
```bash
aws configure
# AWS Access Key ID: <your-key>
# AWS Secret Access Key: <your-secret>
# Default region: us-east-1
# Default output format: json
```

---

## Troubleshooting

### "Access denied" khi sync
- Kiểm tra IAM role của KB có permission đọc S3 bucket
- Kiểm tra S3 bucket policy không block Bedrock service

### "Model access not granted"
- Bedrock Console → Model access → Verify "Access granted" cho Titan Embeddings V2

### Sync thành công nhưng retrieve trả về empty
- Kiểm tra S3 URI đúng prefix (`knowledge_base/`)
- Kiểm tra file không rỗng
- Thử Re-sync

### OpenSearch Serverless collection stuck "Creating"
- Chờ thêm 5-10 phút (lần đầu tạo có thể lâu hơn)
- Nếu >15 phút → Delete và tạo lại KB

### "ValidationException" khi Retrieve
- Verify KB status = "Available" (không phải "Creating" hoặc "Updating")
- Verify data source đã sync thành công

---

## Chi phí ước tính (Dev)

| Resource | Cost |
|----------|------|
| OpenSearch Serverless (2 OCU minimum) | ~$7/day (~$210/month) |
| S3 (36 small .md files) | < $0.01/month |
| Bedrock Titan Embeddings (ingestion) | ~$0.02 one-time |
| Bedrock Claude Sonnet (per query) | ~$0.003-0.015/query |

> **Lưu ý:** OpenSearch Serverless có minimum 2 OCU = ~$0.29/hour. Nhớ **DELETE** KB + Collection sau khi demo xong để tránh phát sinh chi phí.

### Cleanup (sau demo)
```bash
# Từ Terraform
cd infra && terraform destroy

# Hoặc manual trên Console:
# 1. Bedrock → Knowledge bases → Delete KB
# 2. OpenSearch Serverless → Collections → Delete collection
# 3. S3 → Empty bucket → Delete bucket
# 4. IAM → Roles → Delete AmazonBedrockExecutionRoleForKnowledgeBase_geekbrain
```
