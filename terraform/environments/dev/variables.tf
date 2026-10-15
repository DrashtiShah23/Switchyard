variable "aws_region" {
  type        = string
  description = "AWS region for this environment root."
}

variable "name" {
  type        = string
  description = "Network name prefix for this environment."
}

variable "vpc_cidr" {
  type        = string
  description = "VPC CIDR for this environment."
}

variable "public_subnets" {
  type = list(object({
    availability_zone = string
    cidr_block        = string
  }))
  description = "Public subnets for this environment."
}

variable "private_subnets" {
  type = list(object({
    availability_zone = string
    cidr_block        = string
  }))
  description = "Optional private subnets (no NAT)."
  default     = []
}

variable "tags" {
  type        = map(string)
  description = "Extra resource tags."
  default     = {}
}
