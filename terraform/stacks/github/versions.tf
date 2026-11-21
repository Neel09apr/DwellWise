terraform {
  required_version = ">= 1.10"

  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.13"
    }
  }

  # State in the project's Postgres (Supabase), its own schema, with locking.
  # PG_CONN_STR is set at init time by .github/workflows/github-settings.yml.
  backend "pg" {
    schema_name = "terraform_github"
  }
}
