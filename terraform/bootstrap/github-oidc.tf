# Keyless CI: GitHub Actions exchanges a short-lived OIDC token for AWS
# credentials. No AWS access keys exist anywhere, so none can leak.

resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

data "aws_iam_policy_document" "trust" {
  for_each = {
    # Plans run on pull requests and on main.
    plan = ["repo:${local.repo}:pull_request", "repo:${local.repo}:ref:refs/heads/main"]
    # Applies only run in the "production" environment, which needs approval.
    apply = ["repo:${local.repo}:environment:production"]
  }

  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # Exact subjects, no wildcards: a fork or another branch gets nothing.
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = each.value
    }
  }
}

resource "aws_iam_role" "ci" {
  for_each = data.aws_iam_policy_document.trust

  name                 = "${local.prefix}-gha-${each.key}"
  assume_role_policy   = each.value.json
  max_session_duration = 3600
}

# Both roles read everything so plans can refresh state.
resource "aws_iam_role_policy_attachment" "read_only" {
  for_each   = aws_iam_role.ci
  role       = each.value.name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}

# Both roles read and lock state (the lock is an object in the same bucket).
data "aws_iam_policy_document" "state" {
  statement {
    sid       = "ListState"
    actions   = ["s3:ListBucket"]
    resources = [module.state_bucket.arn]
  }

  statement {
    sid       = "ReadWriteStateAndLock"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${module.state_bucket.arn}/*"]
  }
}

resource "aws_iam_role_policy" "state" {
  for_each = aws_iam_role.ci
  name     = "terraform-state"
  role     = each.value.id
  policy   = data.aws_iam_policy_document.state.json
}
