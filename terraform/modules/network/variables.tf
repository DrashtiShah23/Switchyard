variable "name" {
  type        = string
  description = "Short name prefix for network resources (no environment hardcoding)."

  validation {
    condition     = can(regex("^[a-z0-9]([a-z0-9-]{0,30}[a-z0-9])?$", var.name))
    error_message = "name must be 1-32 chars, lowercase alphanumeric and hyphens, and must not start/end with a hyphen."
  }
}

variable "vpc_cidr" {
  type        = string
  description = "IPv4 CIDR block for the VPC."

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "vpc_cidr must be a valid IPv4 CIDR block."
  }
}

variable "public_subnets" {
  type = list(object({
    availability_zone = string
    cidr_block        = string
  }))
  description = <<-EOT
    Public subnets with Internet Gateway routes. Provide at least one.
    For an Application Load Balancer (later milestone), AWS requires subnets
    in at least two Availability Zones — pass two or more entries when that
    path is used. This module never creates NAT Gateways.
  EOT

  validation {
    condition     = length(var.public_subnets) >= 1
    error_message = "public_subnets must contain at least one subnet."
  }

  validation {
    condition = alltrue([
      for s in var.public_subnets : can(cidrhost(s.cidr_block, 0))
    ])
    error_message = "each public subnet cidr_block must be a valid IPv4 CIDR."
  }

  validation {
    condition = alltrue([
      for s in var.public_subnets : length(trimspace(s.availability_zone)) > 0
    ])
    error_message = "each public subnet must set a non-empty availability_zone."
  }
}

variable "private_subnets" {
  type = list(object({
    availability_zone = string
    cidr_block        = string
  }))
  description = <<-EOT
    Optional private subnets. These have no NAT Gateway and no default route
    to the Internet Gateway. Leave empty when private subnets are not needed.
  EOT
  default     = []

  validation {
    condition = alltrue([
      for s in var.private_subnets : can(cidrhost(s.cidr_block, 0))
    ])
    error_message = "each private subnet cidr_block must be a valid IPv4 CIDR."
  }
}

variable "enable_dns_support" {
  type        = bool
  description = "Enable DNS support in the VPC."
  default     = true
}

variable "enable_dns_hostnames" {
  type        = bool
  description = "Enable DNS hostnames in the VPC."
  default     = true
}

variable "tags" {
  type        = map(string)
  description = "Additional tags merged onto all network resources."
  default     = {}
}
