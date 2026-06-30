variable "project_name" {
  description = "Project name used for resource naming and tags."
  type        = string
  default     = "eventforge"
}

variable "environment" {
  description = "Deployment environment (dev, prod)."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "single_nat_gateway" {
  description = "Use one NAT gateway for all private subnets (lower cost for dev)."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Additional tags applied to all networking resources."
  type        = map(string)
  default     = {}
}
