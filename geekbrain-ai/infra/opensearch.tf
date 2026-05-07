resource "aws_opensearchserverless_security_policy" "kb_encryption" {
  name = "${var.project_name}-enc"
  type = "encryption"

  policy = jsonencode({
    Rules = [
      {
        Resource     = ["collection/${var.project_name}-kb"]
        ResourceType = "collection"
      }
    ]
    AWSOwnedKey = true
  })
}

resource "aws_opensearchserverless_security_policy" "kb_network" {
  name = "${var.project_name}-net"
  type = "network"

  policy = jsonencode([
    {
      Rules = [
        {
          Resource     = ["collection/${var.project_name}-kb"]
          ResourceType = "collection"
        }
      ]
      AllowFromPublic = true
    }
  ])
}

resource "aws_opensearchserverless_access_policy" "kb_data" {
  name = "${var.project_name}-data"
  type = "data"

  policy = jsonencode([
    {
      Rules = [
        {
          Resource     = ["collection/${var.project_name}-kb"]
          ResourceType = "collection"
          Permission = [
            "aoss:CreateCollectionItems",
            "aoss:DeleteCollectionItems",
            "aoss:UpdateCollectionItems",
            "aoss:DescribeCollectionItems"
          ]
        },
        {
          Resource     = ["index/${var.project_name}-kb/*"]
          ResourceType = "index"
          Permission = [
            "aoss:CreateIndex",
            "aoss:DeleteIndex",
            "aoss:UpdateIndex",
            "aoss:DescribeIndex",
            "aoss:ReadDocument",
            "aoss:WriteDocument"
          ]
        }
      ]
      Principal = [
        aws_iam_role.bedrock_kb.arn,
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/dinh-geekbrain-ai-w4-github-deploy",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:user/dinh"
      ]
    }
  ])
}

resource "aws_opensearchserverless_collection" "kb" {
  name = "${var.project_name}-kb"
  type = "VECTORSEARCH"

  depends_on = [
    aws_opensearchserverless_security_policy.kb_encryption,
    aws_opensearchserverless_security_policy.kb_network,
    aws_opensearchserverless_access_policy.kb_data
  ]
}
