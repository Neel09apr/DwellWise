# The Supabase project's database security settings as code.
#
# Only supabase_settings is managed. The project resource is left alone on
# purpose: the provider resets the database password whenever the configured
# value differs from state, and an imported project has none in state, so
# adopting it could rotate the live password and break every connection.
#
# Settings are partial: the provider writes only the keys given here and leaves
# every other setting as it is.

import {
  to = supabase_settings.this
  id = var.project_ref
}

resource "supabase_settings" "this" {
  project_ref = var.project_ref

  # Refuse plain-text connections. The API and pipeline negotiate TLS (psycopg's
  # default); the Terraform state backend is given sslmode=require by ops/dburl.py.
  ssl_enforcement = true

  # Auth settings (such as disabling sign-ups) are not managed here: the API
  # requires project_admin_write for them, far wider than this stack's token.
  # Sign-ups were switched off once in the dashboard; see DESIGN.md.
}
