output "knowledge_base_id" {
  description = "Bedrock Knowledge Base ID (use in retriever.py)"
  value       = aws_bedrockagent_knowledge_base.main.id
}

output "data_source_id" {
  description = "Bedrock data source ID (for sync/ingestion)"
  value       = aws_bedrockagent_data_source.s3.data_source_id
}

output "s3_bucket_name" {
  description = "S3 bucket containing KB documents"
  value       = aws_s3_bucket.knowledge_base.id
}

output "opensearch_collection_endpoint" {
  description = "OpenSearch Serverless collection endpoint"
  value       = aws_opensearchserverless_collection.kb.collection_endpoint
}

output "bedrock_kb_role_arn" {
  description = "IAM role ARN used by Bedrock KB"
  value       = aws_iam_role.bedrock_kb.arn
}
