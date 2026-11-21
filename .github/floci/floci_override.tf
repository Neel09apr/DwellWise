# Copied into each AWS root by the "AWS Terraform on Floci" CI job, never
# committed there. Terraform merges *_override.tf into the provider block, so
# region and default tags stay as written; only the endpoint and the checks a
# real account needs change. Floci accepts any non-empty credentials.
provider "aws" {
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  s3_use_path_style           = true

  endpoints {
    budgets = "http://localhost:4566"
    iam     = "http://localhost:4566"
    s3      = "http://localhost:4566"
    sts     = "http://localhost:4566"
  }
}
