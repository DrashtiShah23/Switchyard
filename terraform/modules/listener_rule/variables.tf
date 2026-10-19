variable "listener_arn" {
  type        = string
  description = "ARN of an existing ALB listener (from alb.listener_arns_by_port or RenderContext)."

  validation {
    condition     = can(regex("^arn:aws:elasticloadbalancing:[a-z0-9-]+:\\d{12}:listener/.+$", var.listener_arn))
    error_message = "listener_arn must be a valid ELB listener ARN."
  }
}

variable "priority" {
  type        = number
  description = "Rule priority (1-50000)."

  validation {
    condition     = var.priority >= 1 && var.priority <= 50000
    error_message = "priority must be between 1 and 50000."
  }
}

variable "path_pattern" {
  type        = string
  description = "Optional path-pattern condition (must start with /)."
  default     = null
}

variable "host_header" {
  type        = string
  description = "Optional host-header condition."
  default     = null
}

variable "action" {
  type = object({
    type             = string
    status_code      = optional(string)
    content_type     = optional(string)
    message_body     = optional(string)
    target_group_arn = optional(string)
  })
  description = "Rule action: fixed-response or forward."
}

variable "tags" {
  type        = map(string)
  description = "Additional tags."
  default     = {}
}

check "at_least_one_condition" {
  assert {
    condition     = var.path_pattern != null || var.host_header != null
    error_message = "at least one of path_pattern or host_header is required."
  }
}

check "path_pattern_shape" {
  assert {
    condition     = var.path_pattern == null || startswith(var.path_pattern, "/")
    error_message = "path_pattern must start with '/'."
  }
}

check "action_type_supported" {
  assert {
    condition     = contains(["fixed-response", "forward"], var.action.type)
    error_message = "action.type must be fixed-response or forward."
  }
}

check "forward_needs_target" {
  assert {
    condition     = var.action.type != "forward" || try(var.action.target_group_arn, null) != null
    error_message = "forward actions require target_group_arn."
  }
}

check "fixed_response_needs_status" {
  assert {
    condition     = var.action.type != "fixed-response" || try(var.action.status_code, null) != null
    error_message = "fixed-response actions require status_code."
  }
}
