variable "name" {
  type        = string
  description = "Name tag / prefix for a created security group. Ignored when attaching rules to an existing group."
  default     = null

  validation {
    condition     = var.name == null || can(regex("^[a-z0-9]([a-z0-9-]{0,30}[a-z0-9])?$", var.name))
    error_message = "name must be null or 1-32 chars lowercase alphanumeric/hyphen."
  }
}

variable "description" {
  type        = string
  description = "Security group description when creating a group."
  default     = "Managed by Switchyard"
}

variable "vpc_id" {
  type        = string
  description = "VPC id required when create_security_group is true (from network module output)."
  default     = null
}

variable "create_security_group" {
  type        = bool
  description = "When true, create a new security group. When false, only manage rules on existing_security_group_id."
  default     = true
}

variable "existing_security_group_id" {
  type        = string
  description = "Existing security group id used when create_security_group is false."
  default     = null

  validation {
    condition     = var.existing_security_group_id == null || can(regex("^sg-[0-9a-f]{8,17}$", var.existing_security_group_id))
    error_message = "existing_security_group_id must be null or look like sg-xxxxxxxx."
  }
}

variable "ingress_rules" {
  type = list(object({
    description                  = string
    protocol                     = string
    from_port                    = optional(number)
    to_port                      = optional(number)
    cidr_ipv4                    = optional(string)
    referenced_security_group_id = optional(string)
  }))
  description = "Ingress rules to manage. Exactly one of cidr_ipv4 or referenced_security_group_id per rule."
  default     = []
}

variable "egress_rules" {
  type = list(object({
    description                  = string
    protocol                     = string
    from_port                    = optional(number)
    to_port                      = optional(number)
    cidr_ipv4                    = optional(string)
    referenced_security_group_id = optional(string)
  }))
  description = "Egress rules to manage. Exactly one of cidr_ipv4 or referenced_security_group_id per rule."
  default     = []
}

variable "tags" {
  type        = map(string)
  description = "Additional tags."
  default     = {}
}

locals {
  _rule_lists = concat(var.ingress_rules, var.egress_rules)
}

check "create_xor_existing" {
  assert {
    condition = (
      var.create_security_group && var.vpc_id != null && var.name != null && var.existing_security_group_id == null
      ) || (
      !var.create_security_group && var.existing_security_group_id != null
    )
    error_message = "create_security_group=true requires vpc_id+name and no existing id; false requires existing_security_group_id."
  }
}

check "no_open_admin_ingress" {
  assert {
    condition = alltrue([
      for rule in var.ingress_rules :
      !(
        try(rule.cidr_ipv4, null) == "0.0.0.0/0"
        && contains(["tcp", "udp", "all", "-1"], lower(rule.protocol))
        && (
          lower(rule.protocol) == "all" || lower(rule.protocol) == "-1"
          || (try(rule.from_port, null) != null && try(rule.to_port, null) != null && rule.from_port <= 22 && rule.to_port >= 22)
          || (try(rule.from_port, null) != null && try(rule.to_port, null) != null && rule.from_port <= 3389 && rule.to_port >= 3389)
        )
      )
    ])
    error_message = "ingress rules must not expose administrative ports 22/3389 to 0.0.0.0/0."
  }
}

check "rules_have_exactly_one_source" {
  assert {
    condition = alltrue([
      for rule in local._rule_lists :
      (try(rule.cidr_ipv4, null) != null) != (try(rule.referenced_security_group_id, null) != null)
    ])
    error_message = "each rule must set exactly one of cidr_ipv4 or referenced_security_group_id."
  }
}
