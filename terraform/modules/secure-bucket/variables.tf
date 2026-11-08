variable "name" {
  description = "Globally unique bucket name."
  type        = string
}

variable "noncurrent_version_days" {
  description = "Days to keep old object versions before they expire."
  type        = number
  default     = 30
}

variable "force_destroy" {
  description = "Allow terraform destroy to delete a bucket that still holds objects. Keep false for state."
  type        = bool
  default     = false
}
