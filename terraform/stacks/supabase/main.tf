# The Supabase project's security settings as code.
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

  # Every client (API, pipeline, Terraform state) connects over TLS already;
  # enforce it so a misconfigured client fails instead of falling back to plain text.
  ssl_enforcement = true

  # DwellWise has no user accounts (DESIGN.md, out of scope). Nobody should be
  # able to sign up through the project's public auth endpoint.
  auth = jsonencode({
    disable_signup = true
  })
}
