# What the apply role may change: only resources named dwellwise-*, in this
# account and region. Any role it creates must carry the workload permissions
# boundary, so CI can never mint a role more powerful than the boundary.

locals {
  region = var.aws_region
  acct   = local.account_id
}

data "aws_iam_policy_document" "workload_boundary" {
  statement {
    sid       = "Logs"
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:${local.region}:${local.acct}:log-group:/aws/lambda/${local.prefix}-*"]
  }

  statement {
    sid       = "DataBuckets"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
    resources = ["arn:aws:s3:::${local.prefix}-data-*", "arn:aws:s3:::${local.prefix}-data-*/*"]
  }

  statement {
    sid       = "ReadOwnParameters"
    actions   = ["ssm:GetParameter", "ssm:GetParameters"]
    resources = ["arn:aws:ssm:${local.region}:${local.acct}:parameter/${local.prefix}/*"]
  }

  statement {
    sid       = "InvokeOwnFunctions"
    actions   = ["lambda:InvokeFunction"]
    resources = ["arn:aws:lambda:${local.region}:${local.acct}:function:${local.prefix}-*"]
  }

  statement {
    sid       = "OwnMetrics"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"] # PutMetricData has no resource ARN; the namespace condition scopes it.

    condition {
      test     = "StringEquals"
      variable = "cloudwatch:namespace"
      values   = ["DwellWise"]
    }
  }
}

resource "aws_iam_policy" "workload_boundary" {
  name        = "${local.prefix}-workload-boundary"
  description = "Ceiling for every role CI creates."
  policy      = data.aws_iam_policy_document.workload_boundary.json
}

data "aws_iam_policy_document" "apply" {
  statement {
    sid = "WorkloadBuckets"
    actions = [
      "s3:CreateBucket", "s3:DeleteBucket", "s3:PutBucketPolicy", "s3:DeleteBucketPolicy",
      "s3:PutBucketVersioning", "s3:PutEncryptionConfiguration", "s3:PutLifecycleConfiguration",
      "s3:PutBucketOwnershipControls", "s3:PutBucketPublicAccessBlock", "s3:PutBucketTagging",
      "s3:PutObject", "s3:DeleteObject",
    ]
    resources = ["arn:aws:s3:::${local.prefix}-data-*", "arn:aws:s3:::${local.prefix}-data-*/*"]
  }

  statement {
    sid = "Functions"
    actions = [
      "lambda:CreateFunction", "lambda:DeleteFunction", "lambda:UpdateFunctionCode",
      "lambda:UpdateFunctionConfiguration", "lambda:AddPermission", "lambda:RemovePermission",
      "lambda:TagResource", "lambda:UntagResource", "lambda:PutFunctionConcurrency",
    ]
    resources = ["arn:aws:lambda:${local.region}:${local.acct}:function:${local.prefix}-*"]
  }

  statement {
    sid = "Schedules"
    actions = [
      "scheduler:CreateSchedule", "scheduler:UpdateSchedule", "scheduler:DeleteSchedule",
      "scheduler:TagResource", "scheduler:UntagResource",
    ]
    resources = ["arn:aws:scheduler:${local.region}:${local.acct}:schedule/default/${local.prefix}-*"]
  }

  statement {
    sid = "LogGroups"
    actions = [
      "logs:CreateLogGroup", "logs:DeleteLogGroup", "logs:PutRetentionPolicy",
      "logs:TagResource", "logs:UntagResource",
    ]
    resources = ["arn:aws:logs:${local.region}:${local.acct}:log-group:/aws/lambda/${local.prefix}-*"]
  }

  statement {
    sid       = "Parameters"
    actions   = ["ssm:PutParameter", "ssm:DeleteParameter", "ssm:AddTagsToResource", "ssm:RemoveTagsFromResource"]
    resources = ["arn:aws:ssm:${local.region}:${local.acct}:parameter/${local.prefix}/*"]
  }

  statement {
    sid = "AlarmsAndTopics"
    actions = [
      "cloudwatch:PutMetricAlarm", "cloudwatch:DeleteAlarms", "cloudwatch:TagResource",
      "sns:CreateTopic", "sns:DeleteTopic", "sns:Subscribe", "sns:Unsubscribe",
      "sns:SetTopicAttributes", "sns:TagResource",
    ]
    resources = [
      "arn:aws:cloudwatch:${local.region}:${local.acct}:alarm:${local.prefix}-*",
      "arn:aws:sns:${local.region}:${local.acct}:${local.prefix}-*",
    ]
  }

  statement {
    sid = "RolesOnlyWithBoundary"
    actions = [
      "iam:CreateRole", "iam:PutRolePermissionsBoundary", "iam:PutRolePolicy",
      "iam:AttachRolePolicy", "iam:DetachRolePolicy", "iam:DeleteRolePolicy",
    ]
    resources = ["arn:aws:iam::${local.acct}:role/${local.prefix}/*"]

    condition {
      test     = "StringEquals"
      variable = "iam:PermissionsBoundary"
      values   = [aws_iam_policy.workload_boundary.arn]
    }
  }

  statement {
    sid       = "ManageOwnRoles"
    actions   = ["iam:DeleteRole", "iam:TagRole", "iam:UntagRole", "iam:UpdateRole", "iam:UpdateAssumeRolePolicy"]
    resources = ["arn:aws:iam::${local.acct}:role/${local.prefix}/*"]
  }

  statement {
    sid       = "PassOwnRolesToServices"
    actions   = ["iam:PassRole"]
    resources = ["arn:aws:iam::${local.acct}:role/${local.prefix}/*"]

    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["lambda.amazonaws.com", "scheduler.amazonaws.com"]
    }
  }

  # Belt and braces: the boundary and its versions are off limits.
  statement {
    sid    = "NeverWeakenTheBoundary"
    effect = "Deny"
    actions = [
      "iam:DeleteRolePermissionsBoundary", "iam:CreatePolicyVersion", "iam:DeletePolicy",
      "iam:DeletePolicyVersion", "iam:SetDefaultPolicyVersion",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "apply" {
  name   = "workloads"
  role   = aws_iam_role.ci["apply"].id
  policy = data.aws_iam_policy_document.apply.json
}
