terraform {
  backend "s3" {
    bucket         = "dinh-geekbrain-ai-w4-tfstate"
    key            = "infra/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "dinh-geekbrain-ai-w4-tflock"
    encrypt        = true
  }
}
