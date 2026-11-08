output "snapshots_bucket" {
  description = "Bucket the nightly refresh writes raw snapshots to."
  value       = module.snapshots.id
}
