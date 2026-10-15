# Terraform bootstrap

Creates the remote state backend (S3 with native lockfile support).

Wired in Milestone 8. Uses S3 native locking — **no DynamoDB** solely for
locking.
