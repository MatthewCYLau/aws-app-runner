
data "archive_file" "pnl_aggregator" {
  type        = "zip"
  source_file = "lambda/pnl_aggregator.py"
  output_path = "lambda/pnl_aggregator_lambda.zip"
}

resource "aws_lambda_function" "pnl_aggregator" {
  filename         = data.archive_file.pnl_aggregator.output_path
  source_code_hash = data.archive_file.pnl_aggregator.output_base64sha256
  function_name    = "pnl_aggregator"
  role             = aws_iam_role.lambda_pnl_role.arn
  handler          = "pnl_aggregator.main"
  runtime          = "python3.12"
  layers           = ["arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python312:24"]
}

resource "aws_lambda_event_source_mapping" "trigger" {
  event_source_arn  = module.positions_pnl.dynamodb_table_stream_arn
  function_name     = aws_lambda_function.pnl_aggregator.arn
  starting_position = "LATEST"
  batch_size        = 100
}