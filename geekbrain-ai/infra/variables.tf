variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "dinh-geekbrain-ai-w4"
}

variable "embedding_model_id" {
  description = "Bedrock embedding model ARN"
  type        = string
  default     = "amazon.titan-embed-text-v2:0"
}

variable "knowledge_base_docs_path" {
  description = "Local path to knowledge base .md files"
  type        = string
  default     = "../data_package/knowledge_base"
}

variable "chunking_max_tokens" {
  description = "Max tokens per chunk for KB ingestion"
  type        = number
  default     = 512
}

variable "chunking_overlap_percentage" {
  description = "Overlap percentage between chunks"
  type        = number
  default     = 20
}
