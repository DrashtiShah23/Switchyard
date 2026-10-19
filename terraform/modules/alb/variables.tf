variable "name" {
  type        = string
  description = "Application Load Balancer name (1-32 chars)."

  validation {
    condition     = can(regex("^[a-zA-Z0-9][a-zA-Z0-9-]{0,30}[a-zA-Z0-9]$", var.name)) || can(regex("^[a-zA-Z0-9]$", var.name))
    error_message = "name must be 1-32 alphanumeric/hyphen characters."
  }
}

variable "subnet_ids" {
  type        = list(string)
  description = "Public subnet IDs from the network module (AWS requires at least two AZs)."

  validation {
    condition     = length(var.subnet_ids) >= 2
    error_message = "subnet_ids must include at least two subnets (ALB multi-AZ requirement)."
  }
}

variable "security_group_ids" {
  type        = list(string)
  description = "Security group IDs attached to the ALB (explicit ownership; typically from security_group module)."

  validation {
    condition     = length(var.security_group_ids) >= 1
    error_message = "security_group_ids must contain at least one security group."
  }
}

variable "internal" {
  type        = bool
  description = "Whether the load balancer is internal."
  default     = false
}

variable "idle_timeout_seconds" {
  type        = number
  description = "Connection idle timeout in seconds."
  default     = 60

  validation {
    condition     = var.idle_timeout_seconds >= 1 && var.idle_timeout_seconds <= 4000
    error_message = "idle_timeout_seconds must be between 1 and 4000."
  }
}

variable "listeners" {
  type = list(object({
    port            = number
    protocol        = string
    certificate_arn = optional(string)
    ssl_policy      = optional(string)
    default_action = object({
      type             = string
      status_code      = optional(string)
      content_type     = optional(string)
      message_body     = optional(string)
      target_group_arn = optional(string)
    })
  }))
  description = <<-EOT
    Listeners to create on this ALB. HTTPS listeners must set certificate_arn
    (ACM certificate reference only — this module never issues certificates).
    default_action.type is fixed-response or forward.
  EOT

  validation {
    condition = alltrue([
      for listener in var.listeners :
      contains(["HTTP", "HTTPS", "TCP", "TLS"], listener.protocol)
    ])
    error_message = "listener protocol must be one of HTTP, HTTPS, TCP, TLS."
  }

  validation {
    condition = alltrue([
      for listener in var.listeners :
      listener.port >= 1 && listener.port <= 65535
    ])
    error_message = "listener port must be between 1 and 65535."
  }

  validation {
    condition = alltrue([
      for listener in var.listeners :
      contains(["fixed-response", "forward"], listener.default_action.type)
    ])
    error_message = "default_action.type must be fixed-response or forward."
  }
}

variable "tags" {
  type        = map(string)
  description = "Additional tags."
  default     = {}
}

check "https_requires_certificate" {
  assert {
    condition = alltrue([
      for listener in var.listeners :
      listener.protocol != "HTTPS" && listener.protocol != "TLS"
      || try(listener.certificate_arn, null) != null
    ])
    error_message = "HTTPS/TLS listeners require certificate_arn (reference only; no ACM issuance)."
  }
}

check "http_should_not_use_443" {
  assert {
    condition = alltrue([
      for listener in var.listeners :
      !(listener.protocol == "HTTP" && listener.port == 443)
    ])
    error_message = "HTTP listeners should not use port 443; use HTTPS."
  }
}

check "https_should_not_use_80" {
  assert {
    condition = alltrue([
      for listener in var.listeners :
      !(listener.protocol == "HTTPS" && listener.port == 80)
    ])
    error_message = "HTTPS listeners should not use port 80; use HTTP."
  }
}

check "forward_requires_target_group" {
  assert {
    condition = alltrue([
      for listener in var.listeners :
      listener.default_action.type != "forward"
      || try(listener.default_action.target_group_arn, null) != null
    ])
    error_message = "forward default actions require target_group_arn."
  }
}

check "fixed_response_requires_status" {
  assert {
    condition = alltrue([
      for listener in var.listeners :
      listener.default_action.type != "fixed-response"
      || try(listener.default_action.status_code, null) != null
    ])
    error_message = "fixed-response default actions require status_code."
  }
}
