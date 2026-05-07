resource "aws_ecr_repository" "api" {
  name                 = "${var.project_name}-api"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = false
  }
}

resource "aws_ecr_repository" "monitoring" {
  name                 = "${var.project_name}-monitoring"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = false
  }
}

output "ecr_api_url" {
  value = aws_ecr_repository.api.repository_url
}

output "ecr_monitoring_url" {
  value = aws_ecr_repository.monitoring.repository_url
}
