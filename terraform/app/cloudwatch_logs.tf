resource "aws_cloudwatch_log_group" "this" {
  name = "aws-app"

  tags = merge(
    local.common_tags,
    { Name = "aws-app-cloudwatch-logs" }
  )
}