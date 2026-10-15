# network module

Reusable VPC foundation for Switchyard edge workloads.

## Guarantees

- Typed variables with validation blocks
- No environment-specific constants (`dev` / `staging` / `prod` belong in callers)
- **No NAT Gateway / NAT EIP resources**
- Outputs suitable for later security group and load balancer modules

## ALB note

AWS Application Load Balancers require subnets in **at least two** Availability
Zones. Pass two or more `public_subnets` when composing an ALB. Creating an ALB
is an optional cloud action and is not part of the zero-cost Definition of Done.

## Example

See `examples/public_two_az/` for a local-backend composition used by static
validation.
