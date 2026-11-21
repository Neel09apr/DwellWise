# The availability and freshness SLIs (DESIGN.md §9, docs/slo.md): Grafana's
# public probes request the live service from outside, on a fixed schedule.
# GitHub's cron, which ran the first probe, fired no scheduled run at all in its
# first five hours, so it cannot carry an SLO.
#
# Free tier: 100k test executions a month. /health every 2 minutes from two
# locations is 43,200; /ready every 10 minutes from two is 8,640.

data "grafana_synthetic_monitoring_probes" "all" {
  provider = grafana.sm
}

locals {
  probe_ids = [for name in var.probe_locations : data.grafana_synthetic_monitoring_probes.all.probes[name]]
}

resource "grafana_synthetic_monitoring_check" "health" {
  provider  = grafana.sm
  job       = "dwellwise-health"
  target    = "${var.service_url}/health"
  probes    = local.probe_ids
  frequency = 120000 # 2 minutes; also keeps Render's free service from sleeping
  timeout   = 10000
  labels    = { service = "dwellwise", sli = "availability" }

  settings {
    http {
      method                          = "GET"
      valid_status_codes              = [200]
      fail_if_not_ssl                 = true
      fail_if_body_not_matches_regexp = ["\"status\":[ ]*\"ok\""]
    }
  }
}

resource "grafana_synthetic_monitoring_check" "ready" {
  provider  = grafana.sm
  job       = "dwellwise-ready"
  target    = "${var.service_url}/ready"
  probes    = local.probe_ids
  frequency = 600000 # 10 minutes: data age moves in hours
  timeout   = 10000
  labels    = { service = "dwellwise", sli = "freshness" }

  settings {
    http {
      method             = "GET"
      valid_status_codes = [200] # 503 means a source is older than 48 h or the database is down
      fail_if_not_ssl    = true
    }
  }
}
