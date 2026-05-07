#!/usr/bin/env bash
set -euo pipefail

# Sync (ingest) Bedrock Knowledge Base after terraform apply
# Usage: ./sync_kb.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"

cd "$INFRA_DIR"

KB_ID=$(terraform output -raw knowledge_base_id)
DS_ID=$(terraform output -raw data_source_id)

echo "Starting ingestion job..."
echo "  Knowledge Base ID: $KB_ID"
echo "  Data Source ID:    $DS_ID"

INGESTION_JOB=$(aws bedrock-agent start-ingestion-job \
  --knowledge-base-id "$KB_ID" \
  --data-source-id "$DS_ID" \
  --output json)

JOB_ID=$(echo "$INGESTION_JOB" | jq -r '.ingestionJob.ingestionJobId')
echo "  Ingestion Job ID:  $JOB_ID"
echo ""
echo "Waiting for ingestion to complete..."

while true; do
  STATUS=$(aws bedrock-agent get-ingestion-job \
    --knowledge-base-id "$KB_ID" \
    --data-source-id "$DS_ID" \
    --ingestion-job-id "$JOB_ID" \
    --query 'ingestionJob.status' \
    --output text)

  echo "  Status: $STATUS"

  if [[ "$STATUS" == "COMPLETE" ]]; then
    echo ""
    echo "Ingestion complete! KB is ready to use."
    echo "KB_ID=$KB_ID"
    break
  elif [[ "$STATUS" == "FAILED" ]]; then
    echo "ERROR: Ingestion failed!"
    aws bedrock-agent get-ingestion-job \
      --knowledge-base-id "$KB_ID" \
      --data-source-id "$DS_ID" \
      --ingestion-job-id "$JOB_ID"
    exit 1
  fi

  sleep 10
done
