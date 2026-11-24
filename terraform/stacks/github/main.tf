# The repository's settings as code. Applied by CI on merge, planned on pull requests.

resource "github_repository" "this" {
  name         = var.repository
  description  = "Evidence-backed pre-planning briefs for small housing schemes in Ireland, run like a production service: Terraform, keyless signed delivery, a tested data pipeline, monitoring. $0 a month."
  homepage_url = "https://dwellwise.onrender.com"
  topics       = ["terraform", "devsecops", "sre", "platform-engineering", "fastapi", "react", "postgis", "github-actions", "sigstore", "ireland"]
  visibility   = "public"

  has_issues   = true # incidents from the uptime probe are issues
  has_wiki     = false
  has_projects = false

  allow_merge_commit     = true
  allow_squash_merge     = true
  allow_rebase_merge     = true
  delete_branch_on_merge = true # merged branches do not pile up


  security_and_analysis {
    secret_scanning {
      status = "enabled"
    }
    secret_scanning_push_protection {
      status = "enabled"
    }
  }

  archive_on_destroy = true # a destroy archives the repository instead of deleting it

  lifecycle {
    prevent_destroy = true
    # GitHub omits the merge settings when a GitHub App token reads the repository,
    # even with administration: write, so every plan read them as unset and showed
    # changes. The repository already has the values above (checked with an owner
    # token, 24 Nov 2026). Drift in these eight is not detected. Revisit if the
    # provider reads them for App tokens.
    ignore_changes = [
      allow_merge_commit, allow_squash_merge, allow_rebase_merge, delete_branch_on_merge,
      merge_commit_title, merge_commit_message, squash_merge_commit_title, squash_merge_commit_message,
    ]
  }
}

resource "github_repository_vulnerability_alerts" "this" {
  repository = github_repository.this.name
  enabled    = true # Dependabot alerts
}

resource "github_repository_dependabot_security_updates" "this" {
  repository = github_repository.this.name
  enabled    = true
  depends_on = [github_repository_vulnerability_alerts.this] # security updates need alerts on
}

# main only changes through a pull request whose required checks pass. No
# approving review is required: this is a one-person project and GitHub does
# not let an author approve their own pull request. Nobody can bypass it.
resource "github_repository_ruleset" "main" {
  name        = "main"
  repository  = github_repository.this.name
  target      = "branch"
  enforcement = "active"

  conditions {
    ref_name {
      include = ["~DEFAULT_BRANCH"]
      exclude = []
    }
  }

  rules {
    deletion         = true
    non_fast_forward = true

    pull_request {
      required_approving_review_count   = 0
      dismiss_stale_reviews_on_push     = true
      required_review_thread_resolution = true
    }

    required_status_checks {
      strict_required_status_checks_policy = false

      dynamic "required_check" {
        for_each = var.required_checks
        content {
          context        = required_check.value
          integration_id = 15368 # GitHub Actions
        }
      }
    }
  }
}

# Environments hold the secrets. nightly may only run from main; observability
# and github-settings also run plans on pull requests, so they allow any branch
# of this repository (forks never receive secrets).
resource "github_repository_environment" "this" {
  for_each    = toset(["nightly", "observability", "github-settings"])
  repository  = github_repository.this.name
  environment = each.key

  dynamic "deployment_branch_policy" {
    for_each = each.key == "nightly" ? [1] : []
    content {
      protected_branches     = false
      custom_branch_policies = true
    }
  }
}

resource "github_repository_environment_deployment_policy" "nightly_main" {
  repository     = github_repository.this.name
  environment    = github_repository_environment.this["nightly"].environment
  branch_pattern = "main"
}
