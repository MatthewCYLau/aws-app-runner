resource "aws_s3_bucket" "raw_data" {
  bucket_prefix = "pnl-raw-data-"
  force_destroy = true
}

resource "aws_s3_bucket" "processed_data" {
  bucket_prefix = "pnl-processed-data-"
  force_destroy = true
}

resource "aws_iam_role" "lambda_exec" {
  name = "pnl_etl_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_policy" "s3_access" {
  name = "pnl_etl_s3_policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = "${aws_s3_bucket.raw_data.arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "${aws_s3_bucket.processed_data.arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_s3" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.s3_access.arn
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/src/etl.py"
  output_path = "${path.module}/lambda.zip"
}

resource "aws_lambda_function" "pnl_etl" {
  filename      = data.archive_file.lambda_zip.output_path
  function_name = "risk_pnl_etl"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "etl.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 512

  layers = [
    "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python311:12"
  ]

  environment {
    variables = {
      PROCESSED_BUCKET = aws_s3_bucket.processed_data.id
    }
  }
}

resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.pnl_etl.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.raw_data.arn
}

resource "aws_s3_bucket_notification" "raw_upload_trigger" {
  bucket = aws_s3_bucket.raw_data.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.pnl_etl.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".csv"
  }

  depends_on = [aws_lambda_permission.allow_s3]
}

resource "aws_s3_bucket" "athena_results" {
  bucket_prefix = "pnl-athena-results-"
  force_destroy = true
}

resource "aws_glue_catalog_database" "risk_db" {
  name        = "risk_pnl_db"
  description = "Glue database for Risk PnL ETL outputs"
}

resource "aws_glue_catalog_table" "risk_summary_table" {
  name          = "desk_risk_summaries"
  database_name = aws_glue_catalog_database.risk_db.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification" = "parquet"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.processed_data.id}/risk_summaries/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      name                  = "ParquetHiveSerDe"
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
      parameters = {
        "serialization.format" = "1"
      }
    }

    # Matches the Pandas aggregated output schema
    columns {
      name = "desk_id"
      type = "string"
    }
    columns {
      name = "total_net_pnl"
      type = "double"
    }
    columns {
      name = "total_exposure"
      type = "double"
    }
    columns {
      name = "var_95"
      type = "double"
    }
    columns {
      name = "trade_count"
      type = "bigint"
    }
    columns {
      name = "risk_flag"
      type = "boolean"
    }
  }
}

resource "aws_athena_workgroup" "risk_workgroup" {
  name = "risk_analytics_workgroup"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.id}/query_results/"
    }
  }
}
