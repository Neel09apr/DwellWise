variable "owner" {
  description = "Account that owns the repository."
  type        = string
  default     = "Neel09apr"
}

variable "repository" {
  description = "Repository managed by this stack."
  type        = string
  default     = "DwellWise"
}

variable "required_checks" {
  description = "CI jobs that must pass before anything merges to main. Workflows with path filters are left out: a check that never runs would block the merge."
  type        = list(string)
  default = [
    "Terraform fmt, validate, lint",
    "Pipeline lint, test, image build",
    "App API, web and image",
    "Trivy IaC scan",
    "Secret scan",
    "AWS Terraform on the Floci emulator",
    "Helm chart on a throwaway kind cluster",
  ]
}
