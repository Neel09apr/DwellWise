# Bootstrap: the pieces that must exist before CI can manage anything else.
# Applied once by a human with admin credentials, then its state moves into
# the bucket it creates (see README, "Bootstrap").

data "aws_caller_identity" "current" {}

locals {
  repo       = "${var.github_owner}/${var.github_repo}"
  account_id = data.aws_caller_identity.current.account_id
  # Workload resources CI may manage all start with this prefix.
  prefix = "dwellwise"
}

module "state_bucket" {
  source = "../modules/secure-bucket"
  name   = "${local.prefix}-tfstate-${local.account_id}"
  # State history is the undo button; keep it longer than workload data.
  noncurrent_version_days = 90
}

# Cost guardrail: email at half the budget, at the budget, and when AWS
# forecasts the month will exceed it. The first two budgets are free.
resource "aws_budgets_budget" "monthly" {
  name         = "${local.prefix}-monthly-cost"
  budget_type  = "COST"
  limit_amount = var.monthly_budget_usd
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 50
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.alert_email]
  }
}
