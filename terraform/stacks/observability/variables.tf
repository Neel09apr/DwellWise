variable "grafana_url" {
  description = "The Grafana Cloud stack, for example https://dwellwise.grafana.net."
  type        = string
}

variable "grafana_auth" {
  description = "Service account token for the stack (Editor role is enough)."
  type        = string
  sensitive   = true
}

variable "stack_id" {
  description = "Numeric Grafana Cloud stack id (Grafana Cloud portal, stack details)."
  type        = string
}

variable "connections_api_url" {
  description = "Connections API for the stack's region (Grafana Cloud portal, stack details)."
  type        = string
}

variable "cloud_access_policy_token" {
  description = "Access policy token with integration-management and stacks:read scopes."
  type        = string
  sensitive   = true
}

variable "metrics_token" {
  description = "The METRICS_TOKEN Render generated; the scraper sends it as a bearer token."
  type        = string
  sensitive   = true
}

variable "alert_email" {
  description = "Where alerts are emailed. Kept out of the repository."
  type        = string
  sensitive   = true
}

variable "prometheus_uid" {
  description = "UID of the stack's built-in Prometheus data source."
  type        = string
  default     = "grafanacloud-prom"
}

variable "service_url" {
  description = "The live service."
  type        = string
  default     = "https://dwellwise.onrender.com"
}
