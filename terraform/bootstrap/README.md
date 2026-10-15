# Terraform bootstrap

Creates the remote state backend (S3 with native lockfile support).

Wired in Milestone 8. Uses S3 native locking — **no DynamoDB** solely for
locking.

Creating a real bucket is **optional** and not required for Definition of Done.
Environment roots currently use local backends for zero-cost static validation.
