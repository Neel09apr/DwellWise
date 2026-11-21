locals {
  repo_blob = "https://github.com/Neel09apr/DwellWise/blob/main"
}

resource "grafana_folder" "dwellwise" {
  title = "DwellWise"
}

# Grafana Cloud's hosted scraper reads the API's Prometheus endpoint every minute.
resource "grafana_connections_metrics_endpoint_scrape_job" "api" {
  stack_id                    = var.stack_id
  name                        = "dwellwise-api"
  enabled                     = true
  url                         = "${var.service_url}/metrics"
  authentication_method       = "bearer"
  authentication_bearer_token = var.metrics_token
  scrape_interval_seconds     = 60
}

resource "grafana_dashboard" "service" {
  folder = grafana_folder.dwellwise.uid
  config_json = templatefile("${path.module}/dashboard.json.tftpl", {
    prometheus_uid = var.prometheus_uid
  })
}

resource "grafana_contact_point" "owner" {
  name = "DwellWise owner"

  email {
    addresses               = [var.alert_email]
    subject                 = "DwellWise alert: {{ .CommonLabels.alertname }}"
    disable_resolve_message = false
  }
}
