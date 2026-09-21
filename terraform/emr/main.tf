data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.environment}-emr-vpc"
  }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.environment}-emr-private-subnet-${count.index + 1}"
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.environment}-emr-private-rt"
  }
}

resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

resource "aws_security_group" "emr_serverless_sg" {
  name        = "${var.environment}-emr-serverless-sg"
  description = "Security group for EMR Serverless workers and VPC Endpoints"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port = 443
    to_port   = 443
    protocol  = "tcp"
    self      = true
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.environment}-emr-serverless-sg"
  }
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private.id]
  tags = {
    Name = "${var.environment}-emr-s3-vpc-endpoint"
  }
}

resource "aws_vpc_endpoint" "cloudwatch_logs" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.logs"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true

  subnet_ids         = aws_subnet.private[*].id
  security_group_ids = [aws_security_group.emr_serverless_sg.id]

  tags = {
    Name = "${var.environment}-emr-cw-logs-vpc-endpoint"
  }
}

resource "aws_s3_bucket" "emr_data_lake" {
  bucket        = "${var.environment}-pyspark-emr-data-lake-${var.aws_region}"
  force_destroy = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "emr_s3_encryption" {
  bucket = aws_s3_bucket.emr_data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_object" "pyspark_script" {
  bucket = aws_s3_bucket.emr_data_lake.id
  key    = "scripts/risk_pnl_job.py"
  source = "${path.module}/scripts/risk_pnl_job.py"
  etag   = filemd5("${path.module}/scripts/risk_pnl_job.py")
}


resource "aws_iam_role" "emr_serverless_job_role" {
  name = "${var.environment}-emr-serverless-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "emr-serverless.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "emr_serverless_s3_policy" {
  name        = "${var.environment}-emr-s3-access"
  description = "Allows EMR Serverless job access to specific S3 Data Lake"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3ReadAndList"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.emr_data_lake.arn,
          "${aws_s3_bucket.emr_data_lake.arn}/*"
        ]
      },
      {
        Sid    = "S3WriteAndMultipart"
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:AbortMultipartUpload",
          "s3:ListMultipartUploadParts"
        ]
        Resource = [
          # Captures object writes within subdirectories
          "${aws_s3_bucket.emr_data_lake.arn}/output/*",
          "${aws_s3_bucket.emr_data_lake.arn}/logs/*",
          # Captures Hadoop directory marker objects (e.g. output_$folder$)
          "${aws_s3_bucket.emr_data_lake.arn}/output*",
          "${aws_s3_bucket.emr_data_lake.arn}/logs*"
        ]
      },
      {
        Sid    = "GlueCatalogAccess"
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:GetTable",
          "glue:GetTables",
          "glue:CreateTable",
          "glue:UpdateTable",
          "glue:BatchCreatePartition"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_policy" "emr_serverless_cw_policy" {
  name        = "${var.environment}-emr-cw-access"
  description = "Allows EMR Serverless job to manage log streams in CloudWatch"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        # Describe operations require wildcard or log-group prefix permissions
        Resource = [
          "arn:aws:logs:${var.aws_region}:830663695860:log-group:*",
          "arn:aws:logs:${var.aws_region}:830663695860:log-group::log-stream:*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "${aws_cloudwatch_log_group.emr_serverless_logs.arn}:log-stream:*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_s3_policy" {
  role       = aws_iam_role.emr_serverless_job_role.name
  policy_arn = aws_iam_policy.emr_serverless_s3_policy.arn
}

resource "aws_iam_role_policy_attachment" "attach_cw_policy" {
  role       = aws_iam_role.emr_serverless_job_role.name
  policy_arn = aws_iam_policy.emr_serverless_cw_policy.arn
}

resource "aws_cloudwatch_log_group" "emr_serverless_logs" {
  name              = "/aws/emr-serverless/${var.environment}-pyspark-app"
  retention_in_days = 14
}

resource "aws_emrserverless_application" "spark_app" {
  name          = "${var.environment}-risk-engine"
  release_label = var.emr_release_label
  type          = "spark"
  architecture  = "ARM64"

  network_configuration {
    subnet_ids         = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.emr_serverless_sg.id]
  }

  auto_start_configuration {
    enabled = true
  }

  auto_stop_configuration {
    enabled              = true
    idle_timeout_minutes = 15
  }

  initial_capacity {
    initial_capacity_type = "Driver"
    initial_capacity_config {
      worker_count = 1
      worker_configuration {
        cpu    = "4 vCPU"
        memory = "16 GB"
      }
    }
  }

  maximum_capacity {
    cpu    = "64 vCPU"
    memory = "256 GB"
    disk   = "1000 GB"
  }

  monitoring_configuration {
    cloudwatch_logging_configuration {
      enabled        = true
      log_group_name = aws_cloudwatch_log_group.emr_serverless_logs.name
      log_types {
        name   = "SPARK_DRIVER"
        values = ["STDOUT", "STDERR"]
      }

      log_types {
        name   = "SPARK_EXECUTOR"
        values = ["STDOUT"]
      }
    }

    s3_monitoring_configuration {
      log_uri = "s3://${aws_s3_bucket.emr_data_lake.bucket}/logs/"
    }
  }

  tags = {
    Environment = var.environment
    Engine      = "PySpark"
  }
}
