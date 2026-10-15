variable "zone_id" {
  type        = string
  description = "Route 53 hosted zone id. Provided by environment binding — this module never creates hosted zones."

  validation {
    condition     = can(regex("^Z[A-Z0-9]+$", var.zone_id))
    error_message = "zone_id must look like a Route 53 hosted zone id (Z...)."
  }
}

variable "record_name" {
  type        = string
  description = "DNS record name (relative label or FQDN accepted by Route 53)."

  validation {
    condition     = length(trimspace(var.record_name)) > 0 && length(var.record_name) <= 253
    error_message = "record_name must be a non-empty DNS name up to 253 characters."
  }
}

variable "record_type" {
  type        = string
  description = "DNS record type."

  validation {
    condition     = contains(["A", "AAAA", "CNAME", "TXT"], var.record_type)
    error_message = "record_type must be one of A, AAAA, CNAME, TXT."
  }
}

variable "ttl_seconds" {
  type        = number
  description = "Record TTL in seconds."

  validation {
    condition     = var.ttl_seconds >= 60 && var.ttl_seconds <= 172800
    error_message = "ttl_seconds must be between 60 and 172800."
  }
}

variable "records" {
  type        = list(string)
  description = "Record values."

  validation {
    condition     = length(var.records) >= 1
    error_message = "records must contain at least one value."
  }
}

variable "allow_overwrite" {
  type        = bool
  description = "Allow overwriting an existing record (update semantics)."
  default     = true
}

variable "tags" {
  type        = map(string)
  description = "Additional tags for the record set."
  default     = {}
}

check "cname_single_value" {
  assert {
    condition     = var.record_type != "CNAME" || length(var.records) == 1
    error_message = "CNAME records must have exactly one value."
  }
}
