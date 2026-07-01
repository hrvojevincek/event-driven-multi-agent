# EventForge CI/CD

GitHub Actions deploys EventForge to AWS **eu-west-2** on merge to `main`. Lint and unit tests run on every PR.

## Workflows

| Workflow                                                          | Trigger                                                | Purpose                                           |
| ----------------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------- |
| [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)         | PR + push `main`                                       | Ruff, ESLint, pytest (`-m "not integration"`)     |
| [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) | PR (terraform paths), push `main`, `workflow_dispatch` | ECR build/push, ECS rollout, Terraform plan/apply |

### Path filters (push to `main`)

| Paths                | Job                                                          |
| -------------------- | ------------------------------------------------------------ |
| `backend/**`         | Build backend image → roll out API + 6 workers               |
| `frontend/**`        | Build frontend (SSM `NEXT_PUBLIC_*`) → roll out frontend     |
| `infra/terraform/**` | `terraform fmt` / `validate` / `plan` (PR) or `apply` (main) |

Manual deploy: **Actions → Deploy → Run workflow** → choose `backend`, `frontend`, `terraform`, or `all`.

## One-time AWS setup

### 1. Apply Terraform (adds OIDC role + SSM build params)

After your first successful deploy, apply again to create the GitHub OIDC role and SSM parameters for frontend builds:

```bash
cd infra/terraform/environments/dev
terraform apply
```

If the GitHub OIDC provider already exists in your AWS account:

```hcl
# terraform.tfvars
create_github_oidc_provider = false
```

### 2. GitHub repository configuration

**Repository variable** (Settings → Secrets and variables → Actions → Variables):

| Name                  | Example                                                        | Required |
| --------------------- | -------------------------------------------------------------- | -------- |
| `AWS_DEPLOY_ROLE_ARN` | `arn:aws:iam::123456789012:role/eventforge-dev-github-actions` | Yes      |

Get the ARN:

```bash
terraform output -raw github_actions_role_arn
```

**Optional variables** (defaults work for standard dev naming):

| Name                      | Default                          |
| ------------------------- | -------------------------------- |
| `AWS_REGION`              | `eu-west-2`                      |
| `ECS_CLUSTER_NAME`        | `eventforge-dev-cluster`         |
| `ECS_NAME_PREFIX`         | `eventforge-dev`                 |
| `FRONTEND_BUILD_SSM_PATH` | `/eventforge/dev/frontend-build` |
| `ECR_BACKEND_REPOSITORY`  | auto-discovered                  |
| `ECR_FRONTEND_REPOSITORY` | auto-discovered                  |

**Repository secret** (for Terraform plan/apply in CI):

| Name         | Content                                               |
| ------------ | ----------------------------------------------------- |
| `TFVARS_DEV` | Full contents of your `terraform.tfvars` (gitignored) |

Without `TFVARS_DEV`, the Terraform job still runs `fmt`, `validate`, and `init`, but skips `plan`/`apply`.

### 3. Remote Terraform state (recommended)

Uncomment the `backend "s3"` block in `environments/dev/main.tf`, create the bucket and lock table, then set in `terraform.tfvars`:

```hcl
terraform_state_bucket_name = "eventforge-terraform-state"
terraform_lock_table_name   = "eventforge-terraform-locks"
```

Re-apply locally once, then add the same bucket/table names to `TFVARS_DEV` so CI can use remote state.

## How deploy works

1. **OIDC** — workflow assumes `eventforge-dev-github-actions` (no static AWS keys).
2. **ECR** — images tagged with `${{ github.sha }}` and `latest`.
3. **ECS** — [`scripts/ci/ecs-deploy-service.sh`](../scripts/ci/ecs-deploy-service.sh) registers a new task definition revision with the new image and waits for service stability.
4. **Frontend build args** — read from SSM (`/eventforge/dev/frontend-build/NEXT_PUBLIC_*`), synced from Terraform on each apply.

## Local scripts

```bash
# Roll out one service
ECS_CLUSTER_NAME=eventforge-dev-cluster \
  ./scripts/ci/ecs-deploy-service.sh eventforge-dev-cluster eventforge-dev-api IMAGE_URI

# Roll out API + all workers
ECS_CLUSTER_NAME=eventforge-dev-cluster BACKEND_IMAGE=IMAGE_URI \
  ./scripts/ci/ecs-deploy-backend.sh

# Print docker --build-arg flags from SSM
./scripts/ci/frontend-build-args.sh
```

## Troubleshooting

| Symptom                             | Fix                                                                                                                                  |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Deploy jobs skipped                 | Set `AWS_DEPLOY_ROLE_ARN` repository variable (full IAM role ARN)                                                                    |
| `Source Account ID is needed...`    | `AWS_DEPLOY_ROLE_ARN` must be full ARN, e.g. `arn:aws:iam::123456789012:role/eventforge-dev-github-actions` — not just the role name |
| `AccessDenied` on ECR/ECS           | Re-apply Terraform (`github_oidc` module)                                                                                            |
| Frontend build missing Cognito vars | `terraform apply` (writes SSM) or check `frontend_build_ssm_path` output                                                             |
| Terraform apply fails in CI         | Add `TFVARS_DEV` secret; enable S3 remote backend                                                                                    |
| OIDC provider already exists        | `create_github_oidc_provider = false`                                                                                                |
