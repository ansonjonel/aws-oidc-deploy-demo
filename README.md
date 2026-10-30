# aws-oidc-deploy-demo

[![pipeline](https://github.com/ansonjonel/aws-oidc-deploy-demo/actions/workflows/pipeline.yml/badge.svg)](https://github.com/ansonjonel/aws-oidc-deploy-demo/actions/workflows/pipeline.yml)

End-to-end example of a **keyless CI/CD pipeline**: GitHub Actions tests a containerized service, builds a hardened image and pushes it to Amazon ECR using short-lived OIDC credentials. No AWS access keys are stored anywhere.

The infrastructure uses [`terraform-aws-github-oidc`](https://github.com/ansonjonel/terraform-aws-github-oidc).

```
push to main
   │
   ├─ test    unit + HTTP tests (Python stdlib)
   ├─ image   docker build → run read-only, no capabilities → wait for /health
   ├─ infra   terraform fmt / validate
   │
   └─ deploy  (main only, once AWS is configured)
        GitHub OIDC token ──► sts:AssumeRoleWithWebIdentity ──► temporary credentials
        └─ build & push image to ECR, tagged with the commit SHA
```

## What it shows

- **No static credentials.** The IAM role trusts only `repo:<owner>/aws-oidc-deploy-demo:ref:refs/heads/main`, so forks, other branches and pull requests cannot assume it.
- **Least privilege.** The role can push to one ECR repository and nothing else.
- **Hardened container.** Non-root user, read-only filesystem, all Linux capabilities dropped, `no-new-privileges`, health check, and a clean exit on `SIGTERM` so rolling deployments aren't delayed by the kill timeout.
- **Safe registry defaults.** Immutable tags, scan on push, and a lifecycle policy that keeps the last 20 images.
- **Green by default.** The deploy job is skipped until AWS is configured, so the pipeline passes on forks and pull requests.

## Run locally

```bash
python -m unittest discover -v   # tests
docker compose up --build        # http://localhost:8080/health
```

## Enable deployment to your AWS account

```bash
cd infra
terraform init
terraform apply -var github_repository=<owner>/aws-oidc-deploy-demo
# If the account already has the GitHub OIDC provider:
#   -var create_oidc_provider=false -var oidc_provider_arn=<arn>
```

Then add two repository variables (Settings → Secrets and variables → Actions → Variables) from the Terraform outputs:

| Variable | Value |
|---|---|
| `AWS_ROLE_ARN` | `role_arn` output |
| `ECR_REPOSITORY` | `ecr_repository` output |
| `AWS_REGION` | optional, defaults to `eu-west-1` |

The next push to `main` runs the deploy job.

## Layout

```
app/        HTTP service (standard library only)
tests/      unit and HTTP tests
infra/      ECR repository + OIDC role (Terraform)
Dockerfile  hardened runtime image
compose.yaml
.github/workflows/pipeline.yml
```

## License

MIT
