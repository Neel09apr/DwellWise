# Security policy

## Reporting a vulnerability

Please report security issues privately through GitHub:
**Security → Report a vulnerability** on this repository. Do not open a public
issue for anything that could be exploited.

You can expect an acknowledgement within a few days. This is a personal
portfolio project, so there is no bounty, but every report is read and fixed
or answered.

## What this repository does to stay safe

- **No long-lived cloud credentials.** GitHub Actions reaches AWS through OIDC
  federation and short-lived role sessions. No AWS access keys exist.
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
