resource "aws_cloudwatch_log_group" "this" {
  name = "/aws/ecs/aws-app-service"

  tags = merge(
    local.common_tags,
    { Name = "aws-app-cloudwatch-logs" }
  )
}

resource "aws_cloudwatch_log_metric_filter" "transaction_filter" {
  name           = "NewProductCreationFilter"
  pattern        = "\"Registering product\""
  log_group_name = aws_cloudwatch_log_group.this.name

  metric_transformation {
    name      = "NewProductCreationCount"
    namespace = "LogMetrics"
    value     = "1"
  }
}

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "application-performance"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["LogMetrics", "NewProductCreationCount"]
          ]
          period = 300
          stat   = "Sum"
          region = "us-east-1"
          title  = "New product creation over time"
        }
      }
    ]
  })
}