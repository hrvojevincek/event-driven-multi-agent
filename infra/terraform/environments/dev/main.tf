terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }

  # Uncomment after creating the S3 bucket and DynamoDB lock table:
  # backend "s3" {
  #   bucket         = "eventforge-terraform-state"
  #   key            = "dev/terraform.tfstate"
  #   region         = "eu-west-2"
  #   encrypt        = true
  #   dynamodb_table = "eventforge-terraform-locks"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

variable "enable_observability" {
  description = "Enable ADOT sidecar on ECS tasks, X-Ray export, and CloudWatch alarms."
  type        = bool
  default     = true
}

module "networking" {
  source = "../../modules/networking"

  project_name       = var.project_name
  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  single_nat_gateway = var.single_nat_gateway
  tags               = var.tags
}

module "observability" {
  source = "../../modules/observability"

  project_name   = var.project_name
  environment    = var.environment
  aws_region     = var.aws_region
  dlq_queue_name = "${module.sqs.queue_prefix}-dlq"
  enable_alarms  = var.enable_observability
  tags           = var.tags
}

module "ecs" {
  source = "../../modules/ecs"

  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region

  vpc_id             = module.networking.vpc_id
  public_subnet_ids  = module.networking.public_subnet_ids
  private_subnet_ids = module.networking.private_subnet_ids

  alb_security_group_id      = module.networking.alb_security_group_id
  api_security_group_id      = module.networking.api_security_group_id
  frontend_security_group_id = module.networking.frontend_security_group_id
  worker_security_group_id   = module.networking.worker_security_group_id

  backend_image  = var.backend_image
  frontend_image = var.frontend_image

  event_bus_arn                = module.eventbridge.bus_arn
  worker_queue_arns            = module.sqs.worker_queue_arns
  postgres_host                = module.rds.address
  postgres_port                = module.rds.port
  postgres_db                  = module.rds.database_name
  postgres_user                = module.rds.master_username
  postgres_password_secret_arn = module.rds.password_secret_arn
  openai_api_key_secret_arn    = var.openai_api_key_secret_arn
  anthropic_api_key_secret_arn = var.anthropic_api_key_secret_arn
  tavily_api_key_secret_arn    = var.tavily_api_key_secret_arn

  cors_origins          = var.cors_origins
  acm_certificate_arn   = var.acm_certificate_arn
  otel_enabled          = var.enable_observability
  adot_collector_image  = module.observability.adot_collector_image
  adot_config_content   = var.enable_observability ? module.observability.adot_config_content : ""

  create_ecr_repositories = var.create_ecr_repositories
  tags                    = var.tags

  step_functions_research_enabled = var.enable_step_functions_research
}
