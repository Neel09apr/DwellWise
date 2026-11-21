# Everything below already existed before this stack; adopt it rather than create it.
# Import blocks are idempotent: once in state they are no-ops.

import {
  to = github_repository.this
  id = var.repository
}

import {
  to = github_repository_dependabot_security_updates.this
  id = var.repository
}

import {
  for_each = toset(["nightly", "observability", "github-settings"])
  to       = github_repository_environment.this[each.key]
  id       = "${var.repository}:${each.key}"
}

import {
  to = github_repository_environment_deployment_policy.nightly_main
  id = "${var.repository}:nightly:67109015"
}
