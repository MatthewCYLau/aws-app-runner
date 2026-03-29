terraform {
  backend "s3" {
    bucket = "aws-app-runner-security-tf-state"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}
