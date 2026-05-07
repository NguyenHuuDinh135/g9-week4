# --- Lambda Execution Role ---

resource "aws_iam_role" "lambda_exec" {
  name = "${var.project_name}-lambda-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_bedrock" {
  name = "bedrock-access"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock-agent:Retrieve"
        ]
        Resource = "*"
      }
    ]
  })
}

# --- Main API Lambda ---

resource "aws_lambda_function" "api" {
  function_name = "${var.project_name}-api"
  role          = aws_iam_role.lambda_exec.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.api.repository_url}:latest"
  timeout       = 60
  memory_size   = 512

  environment {
    variables = {
      BEDROCK_KB_ID      = aws_bedrockagent_knowledge_base.main.id
      AWS_REGION_NAME    = var.region
      BEDROCK_MODEL_ID   = "anthropic.claude-sonnet-4-20250514"
      DATABASE_PATH      = "/var/task/geekbrain.db"
      MONITORING_API_URL = aws_lambda_function_url.monitoring.function_url
    }
  }

  depends_on = [aws_ecr_repository.api]
}

resource "aws_lambda_function_url" "api" {
  function_name      = aws_lambda_function.api.function_name
  authorization_type = "NONE"

  cors {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
    max_age       = 3600
  }
}

# --- Monitoring API Lambda ---

resource "aws_lambda_function" "monitoring" {
  function_name = "${var.project_name}-monitoring"
  role          = aws_iam_role.lambda_exec.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.monitoring.repository_url}:latest"
  timeout       = 30
  memory_size   = 256

  environment {
    variables = {
      ENVIRONMENT = "production"
    }
  }

  depends_on = [aws_ecr_repository.monitoring]
}

resource "aws_lambda_function_url" "monitoring" {
  function_name      = aws_lambda_function.monitoring.function_name
  authorization_type = "NONE"

  cors {
    allow_origins = ["*"]
    allow_methods = ["GET", "OPTIONS"]
    allow_headers = ["Content-Type"]
    max_age       = 3600
  }
}

# --- Outputs ---

output "api_url" {
  description = "Main API Lambda Function URL"
  value       = aws_lambda_function_url.api.function_url
}

output "monitoring_api_url" {
  description = "Monitoring API Lambda Function URL"
  value       = aws_lambda_function_url.monitoring.function_url
}
