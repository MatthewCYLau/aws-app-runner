resource "aws_cloudwatch_log_group" "this" {
  name = "/aws/ecs/aws-app-service"

  tags = merge(
    local.common_tags,
    { Name = "aws-app-cloudwatch-logs" }
  )
}

resource "aws_cloudwatch_log_group" "dashboard" {
  name = "/aws/ecs/streamlit-dashboard"

  tags = merge(
    local.common_tags,
    { Name = "streamlit-dashboard-cloudwatch-logs" }
  )
}

resource "aws_cloudwatch_log_metric_filter" "transaction_filter" {
  name           = "NewProductCreationFilter"
  pattern        = "\"registering_product\""
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
      },
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["EKS/ApplicationMetrics", "DevPodSpecificLogMessageCount"]
          ]
          period = 300
          stat   = "Sum"
          region = "us-east-1"
          title  = "Position inserted to DynamoDB over time"
        }
      }
    ]
  })
}

resource "aws_cloudwatch_log_metric_filter" "eks_app" {
  name           = "position-inserted-dynamodb"
  log_group_name = "/aws/containerinsights/${module.eks.cluster_name}/application"

  # Clean, multiline pattern definition
  pattern = <<-EOT
    { 
      ($.kubernetes.namespace_name = "dev") && 
      ($.kubernetes.pod_name = "aws-app-deployment-*") && 
      ($.log_processed.event = "Successfully inserted*")
    }
  EOT

  metric_transformation {
    name          = "DevPodSpecificLogMessageCount"
    namespace     = "EKS/ApplicationMetrics"
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "eks_app_error" {
  name           = "app-error"
  log_group_name = "/aws/containerinsights/${module.eks.cluster_name}/application"

  # Clean, multiline pattern definition
  pattern = <<-EOT
    { 
      ($.kubernetes.namespace_name = "dev") && 
      ($.kubernetes.pod_name = "aws-app-deployment-*") && 
      ($.log_processed.level = "error")
    }
  EOT

  metric_transformation {
    name          = "DevPodErrorLogMessageCount"
    namespace     = "EKS/ApplicationMetrics"
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_query_definition" "error_logs_query" {
  name = "application/errors"

  log_group_names = [
    "/aws/containerinsights/${module.eks.cluster_name}/application",
  ]

  query_string = <<EOF
fields @timestamp, @message
| sort @timestamp desc
| filter kubernetes.namespace_name == 'dev'
| filter log_processed.level == 'error'
EOF
}
