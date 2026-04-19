[
  {
    "name": "${container_name}",
    "image": "${aws_ecr_repository}:${tag}",
    "essential": true,
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "${aws_cloudwatch_log_group_name}-service",
        "awslogs-group": "${aws_cloudwatch_log_group_name}"
      }
    },
    "portMappings": [
      {
        "containerPort": 8080,
        "hostPort": 8080,
        "protocol": "tcp"
      }
    ],
    "cpu": 1,
    "environment": [
      {
        "name": "DB_HOST",
        "value": "${db_host}"
      },
      {
        "name": "S3_BUCKET_NAME",
        "value": "${s3_bucket_name}"
      }
    ],
    "ulimits": [
      {
        "name": "nofile",
        "softLimit": 65536,
        "hardLimit": 65536
      }
    ],
    "mountPoints": [],
    "memory": 2048,
    "volumesFrom": []
  }
]