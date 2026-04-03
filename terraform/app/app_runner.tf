/*
resource "aws_apprunner_service" "this" {
  service_name = "aws-app-runner-service"
  instance_configuration {
    instance_role_arn = aws_iam_role.app_runner_instance_role.arn

  }
  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_ecr_access.arn
    }

    image_repository {
      image_configuration {
        port = "8080"
      }
      image_identifier      = "${aws_ecr_repository.this.repository_url}:latest"
      image_repository_type = "ECR"
    }
    auto_deployments_enabled = false
  }

  tags = merge(
    local.common_tags,
    { Name = "aws-app-runne-service" }
  )
}
*/
