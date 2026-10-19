# listener_rule module

Manages a single Application Load Balancer listener rule.

`listener_arn` is an explicit input (from `alb.listener_arns_by_port` or
environment render context). This module never looks up live AWS inventory.
