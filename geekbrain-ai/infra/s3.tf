locals {
  kb_docs = fileset(var.knowledge_base_docs_path, "*.md")
}

resource "aws_s3_bucket" "knowledge_base" {
  bucket = "${var.project_name}-kb-docs"
}

resource "aws_s3_bucket_versioning" "knowledge_base" {
  bucket = aws_s3_bucket.knowledge_base.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "knowledge_base" {
  bucket = aws_s3_bucket.knowledge_base.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "knowledge_base" {
  bucket = aws_s3_bucket.knowledge_base.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_object" "kb_docs" {
  for_each = local.kb_docs

  bucket       = aws_s3_bucket.knowledge_base.id
  key          = "knowledge_base/${each.value}"
  source       = "${var.knowledge_base_docs_path}/${each.value}"
  etag         = filemd5("${var.knowledge_base_docs_path}/${each.value}")
  content_type = "text/markdown"
}
