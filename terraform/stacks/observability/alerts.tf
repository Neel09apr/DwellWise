# Each alert: one Prometheus query (A) and a threshold on it (B). Rules route to
# the owner's email directly, so the stack-wide notification policy is untouched.
locals {
  alerts = {
    slow = {
      name      = "Slow responses"
      expr      = "histogram_quantile(0.95, sum by (le) (rate(dwellwise_http_request_duration_seconds_bucket{route=~\"/v1/.*\"}[10m])))"
      threshold = 0.8
      for       = "10m"
      summary   = "p95 latency of /v1 routes is above the 800 ms SLO."
      runbook   = "docs/runbooks/slow-responses.md"
      no_data   = "OK" # no /v1 traffic is not slowness
    }
    errors = {
      name = "Server errors"
      # /ready answers 503 when data is stale; that has its own alert.
      expr      = "sum(rate(dwellwise_http_requests_total{status=~\"5..\",route!=\"/ready\"}[10m])) / sum(rate(dwellwise_http_requests_total{route!=\"/ready\"}[10m]))"
      threshold = 0.05
      for       = "10m"
      summary   = "More than 5% of requests fail with a server error."
      runbook   = "docs/runbooks/api-down.md"
      no_data   = "OK"
    }
    stale = {
      name      = "Data stale"
      expr      = "max(dwellwise_data_age_hours)"
      threshold = 48
      for       = "15m"
      summary   = "A data source has not loaded for more than 48 hours."
      runbook   = "docs/runbooks/data-stale.md"
      no_data   = "OK" # covered by "Metrics missing"
    }
    missing = {
      name      = "Metrics missing"
      expr      = "absent_over_time(dwellwise_http_requests_total[20m])"
      threshold = 0
      for       = "5m"
      summary   = "No metrics from the API for 20 minutes: the service or the scrape is down."
      runbook   = "docs/runbooks/api-down.md"
      no_data   = "OK" # the query is empty while metrics arrive
    }
  }
}

resource "grafana_rule_group" "service" {
  name             = "DwellWise service"
  folder_uid       = grafana_folder.dwellwise.uid
  interval_seconds = 60

  dynamic "rule" {
    for_each = local.alerts
    content {
      name           = rule.value.name
      condition      = "B"
      for            = rule.value.for
      no_data_state  = rule.value.no_data
      exec_err_state = "Error"
      labels         = { service = "dwellwise" }
      annotations = {
        summary     = rule.value.summary
        runbook_url = "${local.repo_blob}/${rule.value.runbook}"
      }

      data {
        ref_id         = "A"
        datasource_uid = var.prometheus_uid
        relative_time_range {
          from = 1800
          to   = 0
        }
        model = jsonencode({
          refId   = "A"
          expr    = rule.value.expr
          instant = true
        })
      }

      data {
        ref_id         = "B"
        datasource_uid = "__expr__"
        relative_time_range {
          from = 0
          to   = 0
        }
        model = jsonencode({
          refId      = "B"
          type       = "threshold"
          expression = "A"
          datasource = { type = "__expr__", uid = "__expr__" }
          conditions = [{ evaluator = { type = "gt", params = [rule.value.threshold] } }]
        })
      }

      notification_settings {
        contact_point = grafana_contact_point.owner.name
      }
    }
  }
}
