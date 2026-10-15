variable "aws_region" {
  type        = string
  description = "AWS region used by the provider configuration."
  default     = "us-west-2"
}

variable "name" {
  type        = string
  description = "Network name prefix."
  default     = "switchyard"
}

variable "vpc_cidr" {
  type        = string
  description = "VPC CIDR."
  default     = "10.10.0.0/16"
}

variable "public_subnets" {
  type = list(object({
    availability_zone = string
    cidr_block        = string
  }))
  description = "Two public subnets across AZs (ALB-capable later; no NAT)."
  default = [
    {
      availability_zone = "us-west-2a"
      cidr_block        = "10.10.1.0/24"
    },
    {
      availability_zone = "us-west-2b"
      cidr_block        = "10.10.2.0/24"
    },
  ]
}

variable "tags" {
  type        = map(string)
  description = "Extra tags."
  default = {
    Owner = "switchyard-local"
  }
}
