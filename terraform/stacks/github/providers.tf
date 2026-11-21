# The token is a GitHub App installation token minted per run (GITHUB_TOKEN in
# the environment): read-only for plans on pull requests, write for the apply.
provider "github" {
  owner = var.owner
}
