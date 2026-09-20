variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "Target AWS region"
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Environment identifier"
}

variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "VPC CIDR for isolated EMR compute"
}

variable "emr_release_label" {
  type        = string
  default     = "emr-7.1.0"
  description = "EMR release version (Spark 3.5+)"
}