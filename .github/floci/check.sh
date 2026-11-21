#!/usr/bin/env bash
# Asserts that what the AWS Terraform built in Floci has the controls the code
# promises. Runs after both stacks are applied. AWS_ENDPOINT_URL points the CLI at Floci.
set -euo pipefail

fail=0
expect() { # description, expected, actual
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected '$2', got '$3'"; fail=1; fi
}

for bucket in "$@"; do
  expect "$bucket versioning" "Enabled" \
    "$(aws s3api get-bucket-versioning --bucket "$bucket" --query Status --output text)"
  expect "$bucket blocks all public access" "True True True True" \
    "$(aws s3api get-public-access-block --bucket "$bucket" --output text \
       --query 'PublicAccessBlockConfiguration.[BlockPublicAcls,IgnorePublicAcls,BlockPublicPolicy,RestrictPublicBuckets]' | tr '\t' ' ')"
  expect "$bucket encryption" "AES256" \
    "$(aws s3api get-bucket-encryption --bucket "$bucket" --output text \
       --query 'ServerSideEncryptionConfiguration.Rules[0].ApplyServerSideEncryptionByDefault.SSEAlgorithm')"
  expect "$bucket ownership" "BucketOwnerEnforced" \
    "$(aws s3api get-bucket-ownership-controls --bucket "$bucket" --output text \
       --query 'OwnershipControls.Rules[0].ObjectOwnership')"
  expect "$bucket denies plain HTTP" "Deny false" \
    "$(aws s3api get-bucket-policy --bucket "$bucket" --query Policy --output text \
       | jq -r '.Statement[] | select(.Sid == "DenyInsecureTransport") | "\(.Effect) \(.Condition.Bool["aws:SecureTransport"])"')"
done

# The CI roles trust GitHub OIDC for exact subjects only: no wildcards.
for role in dwellwise-gha-plan dwellwise-gha-apply; do
  subjects=$(aws iam get-role --role-name "$role" --query Role.AssumeRolePolicyDocument --output json \
    | jq -r '[.Statement[].Condition.StringEquals["token.actions.githubusercontent.com:sub"]] | flatten | join(",")')
  case "$subjects" in
    *'*'*|'') echo "FAIL $role trust: '$subjects'"; fail=1 ;;
    *) echo "ok   $role trusts only $subjects" ;;
  esac
done
expect "apply role trusts only the production environment" "repo:Neel09apr/DwellWise:environment:production" \
  "$(aws iam get-role --role-name dwellwise-gha-apply --query Role.AssumeRolePolicyDocument --output json \
     | jq -r '[.Statement[].Condition.StringEquals["token.actions.githubusercontent.com:sub"]] | flatten | join(",")')"

# The state lock is an object next to the state (S3-native locking, no DynamoDB).
expect "data stack state is in the state bucket" "data/terraform.tfstate" \
  "$(aws s3api list-objects-v2 --bucket "$1" --prefix data/ --query 'Contents[0].Key' --output text)"

exit "$fail"
