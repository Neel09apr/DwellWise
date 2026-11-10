# Security policy

## Reporting a vulnerability

Please report security issues privately through GitHub:
**Security → Report a vulnerability** on this repository. Do not open a public
issue for anything that could be exploited.

You can expect an acknowledgement within a few days. This is a personal
portfolio project, so there is no bounty, but every report is read and fixed
or answered.

## What this repository does to stay safe

- **No long-lived cloud credentials.** No cloud account is used. Service
  credentials live only in GitHub Actions and Render secrets. The AWS modules
  (not deployed) are written for OIDC federation with short-lived role sessions.
- **Least privilege.** The plan role is read-only. The apply role can only
  change resources named `dwellwise-*`, only from the approved `production`
  environment, and any role it creates must carry a permissions boundary it
  cannot modify.
- **Scanning on every pull request.** Trivy checks the Terraform for
  misconfigurations (HIGH and CRITICAL fail the build), gitleaks scans the
  full history for secrets, and TFLint enforces provider-aware rules.
- **Pinned supply chain.** Every GitHub Action is pinned to a commit SHA and
  updated by Dependabot. Terraform providers are locked with checksums.
- **Secure defaults for storage.** Buckets are private, encrypted, versioned
  and reject plain HTTP.
