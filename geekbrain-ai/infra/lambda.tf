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
      BEDROCK_MODEL_ID   = "anthropic.claude-3-sonnet-20240229-v1:0"
      DATABASE_PATH      = "/var/task/geekbrain.db"
      MONITORING_API_URL = "${aws_apigatewayv2_stage.monitoring.invoke_url}"
    }
  }

  depends_on = [aws_ecr_repository.api]
}

# --- API Gateway: Monitoring API ---

resource "aws_apigatewayv2_api" "monitoring" {
  name          = "${var.project_name}-monitoring-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "OPTIONS"]
    allow_headers = ["Content-Type"]
    max_age       = 3600
  }
}

resource "aws_apigatewayv2_integration" "monitoring" {
  api_id                 = aws_apigatewayv2_api.monitoring.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.monitoring.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "monitoring_default" {
  api_id    = aws_apigatewayv2_api.monitoring.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.monitoring.id}"
}

resource "aws_apigatewayv2_stage" "monitoring" {
  api_id      = aws_apigatewayv2_api.monitoring.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "monitoring_apigw" {
  statement_id  = "AllowAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.monitoring.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.monitoring.execution_arn}/*/*"
}

# --- API Gateway: Main API ---

resource "aws_apigatewayv2_api" "api" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
    max_age       = 3600
  }
}

resource "aws_apigatewayv2_integration" "api" {
  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "api_default" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.api.id}"
}

resource "aws_apigatewayv2_stage" "api" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "api_apigw" {
  statement_id  = "AllowAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}

# --- Outputs ---

output "api_url" {
  description = "Main API Gateway URL"
  value       = aws_apigatewayv2_stage.api.invoke_url
}

output "monitoring_api_url" {
  description = "Monitoring API Gateway URL"
  value       = aws_apigatewayv2_stage.monitoring.invoke_url
}
