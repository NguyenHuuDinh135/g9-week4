resource "time_sleep" "wait_for_opensearch" {
  depends_on      = [aws_opensearchserverless_collection.kb]
  create_duration = "120s"
}

resource "null_resource" "create_opensearch_index" {
  depends_on = [time_sleep.wait_for_opensearch]

  provisioner "local-exec" {
    command = "python3 ${path.module}/scripts/create_index.py ${aws_opensearchserverless_collection.kb.collection_endpoint}"
  }
}

resource "aws_bedrockagent_knowledge_base" "main" {
  name     = "${var.project_name}-kb"
  role_arn = aws_iam_role.bedrock_kb.arn

  depends_on = [
    null_resource.create_opensearch_index,
    aws_iam_role_policy.bedrock_kb_opensearch
  ]

  knowledge_base_configuration {
    type = "VECTOR"

    vector_knowledge_base_configuration {
      embedding_model_arn = "arn:${data.aws_partition.current.partition}:bedrock:${var.region}::foundation-model/${var.embedding_model_id}"
    }
  }

  storage_configuration {
    type = "OPENSEARCH_SERVERLESS"

    opensearch_serverless_configuration {
      collection_arn    = aws_opensearchserverless_collection.kb.arn
      vector_index_name = "bedrock-knowledge-base-default-index"

      field_mapping {
        vector_field   = "bedrock-knowledge-base-default-vector"
        text_field     = "AMAZON_BEDROCK_TEXT_CHUNK"
        metadata_field = "AMAZON_BEDROCK_METADATA"
      }
    }
  }
}

resource "aws_bedrockagent_data_source" "s3" {
  name              = "${var.project_name}-s3-source"
  knowledge_base_id = aws_bedrockagent_knowledge_base.main.id

  data_source_configuration {
    type = "S3"

    s3_configuration {
      bucket_arn = aws_s3_bucket.knowledge_base.arn
    }
  }

  vector_ingestion_configuration {
    chunking_configuration {
      chunking_strategy = "FIXED_SIZE"

      fixed_size_chunking_configuration {
        max_tokens         = var.chunking_max_tokens
        overlap_percentage = var.chunking_overlap_percentage
      }
    }
  }
}
