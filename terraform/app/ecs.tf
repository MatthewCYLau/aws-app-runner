resource "aws_ecs_express_gateway_service" "example" {
  execution_role_arn      = aws_iam_role.ecs_task_execution_role.arn
  infrastructure_role_arn = aws_iam_role.ecs_express_gateway_infrastructure_role.arn
  task_role_arn           = aws_iam_role.ecs_express_gateway_task_role.arn

  primary_container {
    image = "${aws_ecr_repository.this.repository_url}:latest"
    container_port = 8080

    environment {
      name  = "DB_HOST"
      value = aws_db_instance.postgres.address
    }
  }
}