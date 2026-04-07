resource "aws_cloudwatch_log_group" "this" {
  name = "/aws/ecs/aws-app-service"

  tags = merge(
    local.common_tags,
    { Name = "aws-app-cloudwatch-logs" }
  )
}
