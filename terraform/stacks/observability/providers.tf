provider "grafana" {
  url  = var.grafana_url
  auth = var.grafana_auth

  # The Connections API manages the hosted scrape job that reads /metrics.
  connections_api_url          = var.connections_api_url
  connections_api_access_token = var.cloud_access_policy_token
}
