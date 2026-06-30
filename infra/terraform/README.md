# Terraform Infrastructure

> **ADR:** [ADR-012](../../docs/TECH_DECISIONS.md#adr-012-all-in-aws-deployment-on-ecs-fargate) — all-in-AWS ECS Fargate deployment.  
> **Cursor agents:** Infra conventions in `.cursor/rules/infra-aws.mdc`.

IaC for AWS resources. Default region: **`eu-west-2` (London)**.

## Structure

```
terraform/
├── environments/
│   └── dev/                 # Compose modules for dev (networking + ecs today)
└── modules/
    ├── networking/          # VPC, subnets, NAT, security groups ✅
    ├── ecs/                 # ECR, cluster, ALB, Fargate services ✅
    ├── rds/                 # Postgres + pgvector (next)
    ├── sqs/                 # Queues + DLQ (next)
    ├── eventbridge/         # Bus + rules (next)
    ├── cognito/             # User pool (next)
    ├── step-functions/      # Research fan-out (next)
    └── observability/       # ADOT, alarms (next)
```

## What exists today

| Module         | Resources                                                                                              |
| -------------- | ------------------------------------------------------------------------------------------------------ |
| **networking** | VPC `/16`, 2 AZs, public + private subnets, NAT (single for dev), SGs for ALB/API/frontend/workers/RDS |
| **ecs**        | ECR repos, ECS cluster, ALB (SSE idle timeout 300s), API + frontend + 6 worker services                |

`environments/dev` wires networking → ecs. RDS, SQS, EventBridge, and Cognito are **variables** until their modules land (see `terraform.tfvars.example`).

## Prerequisites

- Terraform >= 1.5
- AWS CLI configured (`aws sts get-caller-identity`)
- IAM permissions for VPC, ECS, ECR, ALB, IAM, CloudWatch Logs, Secrets Manager read

## Git / secrets

Do **not** commit `terraform.tfvars`, `*.tfstate`, or `*.tfplan` (see root `.gitignore`).  
**Do** commit `.terraform.lock.hcl` under `environments/dev/` for reproducible provider versions.

## Quick start (dev)

```bash
cd infra/terraform/environments/dev

cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars — at minimum images, postgres_host, secrets, event_bus_arn

terraform init
terraform plan
terraform apply
```

### First deploy order

1. `terraform apply` with placeholders only for **networking + ECR** — or apply networking first by temporarily commenting the ecs module
2. Build and push images:

```bash
# From repo root — use ECR URLs from terraform output
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.eu-west-2.amazonaws.com

docker build -t eventforge-dev-backend backend/
docker tag eventforge-dev-backend:latest $(terraform output -raw backend_ecr_repository_url):latest
docker push $(terraform output -raw backend_ecr_repository_url):latest

docker build -t eventforge-dev-frontend \
  --build-arg NEXT_PUBLIC_API_URL=http://$(terraform output -raw alb_dns_name) \
  frontend/
docker tag eventforge-dev-frontend:latest $(terraform output -raw frontend_ecr_repository_url):latest
docker push $(terraform output -raw frontend_ecr_repository_url):latest
```

3. Update `terraform.tfvars` with image URIs + RDS/SQS/Cognito ARNs when those modules exist
4. Re-apply to start ECS services

## Remote state (recommended before team use)

Uncomment the `backend "s3"` block in `environments/dev/main.tf` and create:

- S3 bucket `eventforge-terraform-state` (versioning + encryption)
- DynamoDB table `eventforge-terraform-locks`

## Next modules

1. `rds` — Postgres 16 + `vector` extension; use `networking.rds_security_group_id`
2. `sqs` + `eventbridge` — mirror LocalStack names (`eventforge-*`)
3. `cognito` — user pool; callback URLs → ALB DNS
4. `step-functions` — research Map state
5. CI/CD — GitHub Actions path filters → ECR → ECS rolling deploy

See `docs/TASKS.md` Phase 5 and `docs/TECH_DECISIONS.md` ADR-012.
