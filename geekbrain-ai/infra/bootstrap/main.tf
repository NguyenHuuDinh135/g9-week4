terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
  }
}

provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Project   = "dinh-geekbrain-ai-w4"
      ManagedBy = "terraform-bootstrap"
    }
  }
}

variable "github_repo" {
  default = "NguyenHuuDinh135/g9-week4"
}

# --- Terraform State Backend ---

resource "aws_s3_bucket" "tfstate" {
  bucket = "dinh-geekbrain-ai-w4-tfstate"
}

resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket                  = aws_s3_bucket.tfstate.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "tflock" {
  name         = "dinh-geekbrain-ai-w4-tflock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}

# --- GitHub OIDC Provider ---

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

# --- GitHub Actions Deploy Role ---

resource "aws_iam_role" "github_deploy" {
  name = "dinh-geekbrain-ai-w4-github-deploy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_repo}:*"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "github_deploy" {
  name = "deploy-permissions"
  role = aws_iam_role.github_deploy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Terraform"
        Effect = "Allow"
        Action = [
          "s3:*",
          "dynamodb:*",
          "iam:*",
          "bedrock:*",
          "bedrock-agent:*",
          "aoss:*",
          "lambda:*",
          "apigateway:*",
          "ecr:*",
          "logs:*",
          "cloudfront:*",
          "acm:*",
          "sts:GetCallerIdentity"
        ]
        Resource = "*"
      }
    ]
  })
}

# --- Outputs ---

output "deploy_role_arn" {
  description = "Set this as GitHub secret AWS_DEPLOY_ROLE_ARN"
  value       = aws_iam_role.github_deploy.arn
}

output "tfstate_bucket" {
  value = aws_s3_bucket.tfstate.id
}

output "tflock_table" {
  value = aws_dynamodb_table.tflock.name
}
