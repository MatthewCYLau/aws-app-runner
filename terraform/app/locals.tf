locals {
  common_tags = {
    environment = "Production"
    managed_by  = "Terraform"
    app_name    = "aws-app-runner"
  }
}