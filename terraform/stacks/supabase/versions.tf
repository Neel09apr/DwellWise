terraform {
  required_version = ">= 1.10"

  required_providers {
    supabase = {
      source  = "supabase/supabase"
      version = "~> 1.11"
    }
  }

  # State in the project's own Postgres, its own schema, with locking.
  # PG_CONN_STR is set at init time by .github/workflows/supabase-settings.yml.
  backend "pg" {
    schema_name = "terraform_supabase"
  }
}
