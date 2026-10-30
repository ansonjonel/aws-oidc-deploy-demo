terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0"
    }
  }
}

provider "aws" {
  region = var.region
}

variable "region" {
  type    = string
  default = "eu-west-1"
}

variable "github_repository" {
  description = "owner/repo allowed to deploy, e.g. ansonjonel/aws-oidc-deploy-demo."
  type        = string
}

variable "create_oidc_provider" {
  description = "Set to false if the account already has the GitHub OIDC provider."
  type        = bool
  default     = true
}

variable "oidc_provider_arn" {
  type    = string
  default = null
}

resource "aws_ecr_repository" "app" {
  name                 = "aws-oidc-deploy-demo"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Keep the registry from growing forever.
resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep the last 20 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 20
      }
      action = { type = "expire" }
    }]
  })
}

# Only pushes to main may assume the role, and it can only push to this repository.
module "github_oidc" {
  source = "github.com/ansonjonel/terraform-aws-github-oidc?ref=v1.0.0"

  role_name            = "github-actions-aws-oidc-deploy-demo"
  subjects             = ["repo:${var.github_repository}:ref:refs/heads/main"]
  create_oidc_provider = var.create_oidc_provider
  oidc_provider_arn    = var.oidc_provider_arn

  inline_policy_json = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "ecr:GetAuthorizationToken"
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:BatchGetImage",
          "ecr:CompleteLayerUpload",
          "ecr:InitiateLayerUpload",
          "ecr:PutImage",
          "ecr:UploadLayerPart",
        ]
        Resource = aws_ecr_repository.app.arn
      },
    ]
  })
}

output "role_arn" {
  description = "Set as the AWS_ROLE_ARN repository variable."
  value       = module.github_oidc.role_arn
}

output "ecr_repository" {
  description = "Set as the ECR_REPOSITORY repository variable."
  value       = aws_ecr_repository.app.name
}
