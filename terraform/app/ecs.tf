resource "aws_ecs_cluster" "main" {
  name = "aws-app-cluster"
}

resource "aws_ecs_task_definition" "service" {
  family                   = "aws-app-task-definition"
  network_mode             = "awsvpc"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn
  cpu                      = 256
  memory                   = 2048
  requires_compatibilities = ["FARGATE"]
  container_definitions = templatefile("task-definitions/service.json.tpl", {
    aws_ecr_repository            = aws_ecr_repository.this.repository_url
    tag                           = "latest"
    container_name                = "aws-app"
    aws_cloudwatch_log_group_name = aws_cloudwatch_log_group.this.name
    db_host                       = aws_db_instance.postgres.address
  })
  tags = merge(
    local.common_tags,
    { Name = "aws-app-task-definition" }
  )
}

resource "aws_ecs_service" "this" {
  name                       = "aws-app-service"
  cluster                    = aws_ecs_cluster.main.id
  task_definition            = aws_ecs_task_definition.service.arn
  desired_count              = 1
  deployment_maximum_percent = 250
  launch_type                = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets          = aws_subnet.private.*.id
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.this.arn
    container_name   = "aws-app"
    container_port   = 8080
  }

  depends_on = [aws_lb_listener.https_forward, aws_iam_role.ecs_task_execution_role]

  tags = merge(
    local.common_tags,
    { Name = "aws-app-service" }
  )
}
