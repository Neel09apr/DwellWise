provider "grafana" {
  url  = var.grafana_url
  auth = var.grafana_auth

  # The Connections API manages the hosted scrape job that reads /metrics.
  connections_api_url          = var.connections_api_url
  connections_api_access_token = var.cloud_access_policy_token
}

# Synthetic Monitoring has its own API and token (created in the Grafana UI when
# Synthetic Monitoring is switched on; stored in the observability environment).
provider "grafana" {
  alias           = "sm"
  sm_access_token = var.sm_access_token
  sm_url          = var.sm_url
}
