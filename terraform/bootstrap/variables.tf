variable "aws_region" {
  description = "Region for everything this platform creates. Ireland, next to the app database."
  type        = string
  default     = "eu-west-1"
}

variable "github_owner" {
  description = "GitHub user or organisation that owns the platform repo."
  type        = string
  default     = "Neel09apr"
}

variable "github_repo" {
  description = "Repository allowed to assume the CI roles."
  type        = string
  default     = "dwellwise-platform"
}

variable "alert_email" {
  description = "Where budget alerts go. Kept out of git in terraform.tfvars."
  type        = string
}

variable "monthly_budget_usd" {
  description = "Monthly spend that triggers alerts. The platform is designed to cost $0."
  type        = string
  default     = "1"
}
