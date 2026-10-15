# Environment: dev

Isolated Terraform state root for development (not a workspace).

- Composes the reusable `network` module
- Local backend for zero-cost static validation (`terraform.tfstate`)
- Example values in `terraform.tfvars.example` (copy to `terraform.tfvars` locally)
- No NAT Gateway; public subnets across two AZs so a later ALB composition remains possible
- Real AWS `plan`/`apply` is optional and never required for Definition of Done

```bash
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform validate
```
