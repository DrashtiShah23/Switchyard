# Environment: staging

Isolated Terraform state root for staging (not a workspace).

Configuration and state design exist for environment separation. **Provisioning
this environment in AWS is not required** for Definition of Done.

```bash
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform validate
```
