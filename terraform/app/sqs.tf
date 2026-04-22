resource "aws_sqs_queue" "app_queue_dlq" {
  name = "aws-app-task-queue-dlq"
}

resource "aws_sqs_queue" "app_queue" {
  name                      = "aws-app-task-queue"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 86400
  receive_wait_time_seconds = 20 # Enables Long Polling

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.app_queue_dlq.arn
    maxReceiveCount     = 5 # Retry 5 times before moving to DLQ
  })
}

output "sqs_url" {
  value = aws_sqs_queue.app_queue.id
}

resource "aws_sqs_queue_policy" "restrict_to_app" {
  queue_url = aws_sqs_queue.app_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowOnlySpecificTaskRole"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.ecs_task_role.arn
        }
        Action   = "sqs:*"
        Resource = aws_sqs_queue.app_queue.arn
      }
    ]
  })
}
