variable "db_password" {
  type = string
}

variable "public_key_path" {
  description = "Public key path"
  default     = "~/.ssh/aws_app.pub"
}

variable "private_key_path" {
  description = "Private key path"
  default     = "~/.ssh/aws_app"
}

variable "instance_type" {
  description = "type for aws EC2 instance"
  default     = "t2.micro"
}
