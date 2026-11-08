# Workload storage, managed only through CI: pull requests plan with the
# read-only role, merges apply with the production role after approval.

data "aws_caller_identity" "current" {}

# Raw public-data snapshots written by the nightly refresh job (next PR).
# The dwellwise-data-* prefix is what the apply role is allowed to manage.
module "snapshots" {
  source = "../../modules/secure-bucket"
  name   = "dwellwise-data-snapshots-${data.aws_caller_identity.current.account_id}"
}
