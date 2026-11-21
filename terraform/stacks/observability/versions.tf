terraform {
  required_version = ">= 1.10"

  required_providers {
    grafana = {
      source  = "grafana/grafana"
      version = "~> 4.55"
    }
  }

  # State lives in the project's own Postgres (Supabase), in its own schema, with
  # locking. The connection string comes from PG_CONN_STR at init time (see
  # .github/workflows/observability.yml). No extra state service or account.
  backend "pg" {
    schema_name = "terraform_observability"
  }
}
