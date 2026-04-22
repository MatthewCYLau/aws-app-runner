data "aws_iam_policy_document" "ecs_task_execution_trust_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_task_execution_role" {
  name               = "ecs-task-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_execution_trust_policy.json
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task_role" {
  name = "ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      },
    ]
  })
}

data "aws_iam_policy_document" "rds_iam_auth" {
  statement {
    actions = ["rds-db:connect"]
    effect  = "Allow"
    resources = [
      "arn:aws:rds-db:us-east-1:${data.aws_caller_identity.current.account_id}:dbuser:${aws_db_instance.postgres.resource_id}/iam_user"
    ]
  }
}

resource "aws_iam_policy" "rds_policy" {
  name   = "rds-iam-auth-policy"
  policy = data.aws_iam_policy_document.rds_iam_auth.json
}


resource "aws_iam_role_policy_attachment" "rds_auth_attach_ecs_task_role" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.rds_policy.arn
}

resource "aws_iam_policy" "s3_write_policy" {
  name        = "AssetsS3WriteAccess"
  description = "Allows ECS task to write to the assets bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:PutObject",
        "s3:GetObject"
      ]
      Resource = "${aws_s3_bucket.assets.arn}/*"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "task_s3_attach" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.s3_write_policy.arn
}

resource "aws_iam_policy" "aws_app_sqs_policy" {
  name = "aws-app-sqs-permissions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.app_queue.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "task_sqs_attach" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.aws_app_sqs_policy.arn
}
