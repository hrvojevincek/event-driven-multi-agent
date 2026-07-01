# EventForge — Issues & Solutions

> Personal log of production-style problems hit while building EventForge, how they were diagnosed, and what we changed. Useful for interviews, postmortems, and not repeating mistakes.

**Where this lives:** `docs/ISSUES.md` — project documentation, **not** a Cursor skill or always-on rule. Skills = reusable workflows; rules = coding conventions. This file is a growing postmortem log you append to after fixing something hard.

**Safe to commit:** use placeholders only — `123456789012` for AWS account IDs, `eventforge-dev-github-actions` for role names, `sk-...` for keys. Never paste real ARNs, tokens, `terraform.tfvars`, or GitHub secret values. Get real values from `terraform output` or the AWS/GitHub console locally.

**Format:** each entry uses **STAR** (Situation → Task → Action → Result) plus a one-line **lesson**.

When you add a new entry, copy the [template](#template) at the bottom.

---

## 2026-06 — Step Functions apply hung on research SQS queue policy

**Area:** Terraform · AWS SQS · Step Functions  
**Symptom:** `terraform apply` stuck 13+ minutes on `module.eventbridge.aws_sqs_queue_policy.eventbridge["research"]: Still modifying...`

### Situation

Rolling out the Step Functions research fan-out module. Plan looked correct (state machine, EventBridge rule, ECS env). Apply created most resources, then one SQS queue policy never finished.

### Task

Get apply to complete reliably and allow **both** EventBridge (`research.task.dispatched`) and Step Functions (Map fan-out) to send messages to `eventforge-research`.

### Action

Traced every resource touching the research queue URL. Found **two** Terraform resources each managing `aws_sqs_queue_policy` on the **same queue**:

| Resource                                       | Module         | Intent                          |
| ---------------------------------------------- | -------------- | ------------------------------- |
| `aws_sqs_queue_policy.eventbridge["research"]` | eventbridge    | EventBridge → research queue    |
| `aws_sqs_queue_policy.research_step_functions` | step-functions | Step Functions → research queue |

SQS allows **one policy document per queue**. Each apply overwrote the other → Terraform thrashed (“Still modifying…”).

**Fix:**

1. Single combined policy in `infra/terraform/environments/dev/research_queue_policy.tf` (EventBridge + Step Functions statements).
2. Eventbridge module **skips** research queue policy when Step Functions is enabled.
3. Removed duplicate policy from the step-functions module.

### Result

One owner for the research queue policy; apply completes in minutes. Pattern documented for future queues.

**Lesson:** One queue → one `aws_sqs_queue_policy`. Extra principals = **statements in one JSON document**, not a second Terraform resource. Grep for duplicate `queue_url` before merge.

**Files:** `research_queue_policy.tf`, `modules/eventbridge/routes.tf`, `modules/step-functions/main.tf`

---

## 2026-06 — CI/CD bootstrap chicken-and-egg

**Area:** Terraform · GitHub Actions · IAM  
**Symptom:** CI cannot deploy until the OIDC role exists; the role is created by Terraform.

### Situation

GitHub Actions needs `AWS_DEPLOY_ROLE_ARN` to run deploy and (optionally) `terraform apply`. That role is **created by Terraform** (`github_oidc` module).

### Task

Establish a sane bootstrap order for a new AWS dev environment.

### Action

1. **Local** `terraform apply` (human AWS creds) — creates OIDC role, infra, Step Functions, etc.
2. Copy `terraform output -raw github_actions_role_arn` → GitHub variable `AWS_DEPLOY_ROLE_ARN`.
3. (Optional) Set `TFVARS_DEV` secret for CI Terraform plan/apply.
4. Push to `main` — CI builds images and rolls ECS.

### Result

One-time local bootstrap; ongoing deploys via CI.

**Lesson:** First deploy is always manual for OIDC-backed pipelines unless the role is pre-provisioned elsewhere.

---

## 2026-06 — Terraform IDE errors vs real validation

**Area:** Terraform · Editor tooling  
**Symptom:** IDE reported `No declaration found for "var.*"` and `Unexpected attribute` on module blocks; `terraform validate` passed.

### Situation

Split dev config across `events.tf`, `step_functions.tf`, and `variables.tf`. Language server did not link root variables or module inputs across files.

### Task

Remove false-positive noise without changing runtime behavior.

### Action

Consolidated SQS + EventBridge + Step Functions into `infra/terraform/environments/dev/event_pipeline.tf` with co-located variables used by those modules. Kept shared flags (e.g. `enable_step_functions_research`) in `variables.tf` where multiple files reference them. Renamed eventbridge module input to `enable_step_functions_research` for consistency.

### Result

`terraform validate` unchanged (always green); IDE squiggles gone after consolidation and `terraform init`.

**Lesson:** Validate/apply is source of truth. If only the IDE complains, check cross-file variable/module layout or reload the Terraform language server.

---

## Template

```markdown
## YYYY-MM — Short title

**Area:** Terraform | CI/CD | Backend | …  
**Symptom:** What you saw (error message, metric, behavior)

### Situation

Context — what you were trying to ship.

### Task

What “fixed” looks like.

### Action

How you diagnosed (tools, grep, AWS console) and what you changed.

### Result

Outcome — metrics, time saved, validate/CI green.

**Lesson:** One sentence rule for next time.

**Files:** paths touched
```
