terraform {
  backend "s3" {
    bucket = "aws-app-runner-emr-tf-state"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}
