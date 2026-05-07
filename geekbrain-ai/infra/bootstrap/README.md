# Bootstrap (One-time setup)

Run this once locally to create:
- S3 bucket for Terraform state
- DynamoDB table for Terraform lock
- GitHub OIDC provider + deploy role

## Prerequisites

- AWS CLI configured with admin access
- Terraform >= 1.5

## Steps

```bash
cd infra/bootstrap
terraform init
terraform apply
```

## After apply

1. Copy the `deploy_role_arn` output
2. Go to GitHub repo Settings > Secrets and variables > Actions
3. Create secret: `AWS_DEPLOY_ROLE_ARN` = the ARN from step 1

That is the ONLY secret needed. GitHub Actions uses OIDC to assume this role.

## Then initialize main infra

```bash
cd ../
terraform init    # connects to S3 backend
terraform plan    # verify
terraform apply   # create KB, OpenSearch, Lambda, ECR, CloudFront
```
