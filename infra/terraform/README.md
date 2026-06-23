# Terraform Infrastructure

> **Cursor agents:** Infra conventions in `.cursor/rules/infra-aws.mdc`. Bootstrap in Phase 5.

IaC for AWS resources. Structure:

```
terraform/
├── environments/
│   ├── dev/
│   └── prod/
└── modules/
    ├── networking/
    ├── rds/
    ├── eventbridge/
    ├── sqs/
    ├── step-functions/
    ├── ecs/          # or lambda/
    └── observability/
```

Bootstrap in Phase 5. See `docs/TECH_DECISIONS.md` ADR-006.
