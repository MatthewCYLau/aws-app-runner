locals {
  common_tags = {
    environment = "Production"
    managed_by  = "Terraform"
    app_name    = "aws-ecs-app"
  }
}

locals {
  instance_ami = data.aws_ami.amazon-linux-2.id
}