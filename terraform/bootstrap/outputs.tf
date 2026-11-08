# Not secrets: these become GitHub repository variables for the CI workflows.

output "aws_region" {
  description = "Region every stack uses."
  value       = var.aws_region
}

output "state_bucket" {
  description = "Backend bucket for every other stack."
  value       = module.state_bucket.id
}

output "plan_role_arn" {
  description = "AWS_PLAN_ROLE_ARN: read-only, assumed on pull requests and main."
  value       = aws_iam_role.ci["plan"].arn
}

output "apply_role_arn" {
  description = "AWS_APPLY_ROLE_ARN: assumed only from the approved production environment."
  value       = aws_iam_role.ci["apply"].arn
}

output "workload_boundary_arn" {
  description = "Permissions boundary every CI-created role must carry."
  value       = aws_iam_policy.workload_boundary.arn
}
