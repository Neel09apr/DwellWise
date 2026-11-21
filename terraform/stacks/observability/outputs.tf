output "dashboard_url" {
  description = "The service dashboard."
  value       = grafana_dashboard.service.url
}
