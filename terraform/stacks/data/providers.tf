provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "dwellwise"
      ManagedBy = "terraform"
      Stack     = "data"
    }
  }
}
