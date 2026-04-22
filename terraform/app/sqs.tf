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