resource "aws_lambda_function" "pnl_aggregator" {
  filename      = "lambda/pnl_aggregator_lambda.zip"
  function_name = "pnl_aggregator"
  role          = aws_iam_role.lambda_pnl_role.arn
  handler       = "pnl_aggregator_lambda.lambda_handler"
  runtime       = "python3.12"
}

resource "aws_lambda_event_source_mapping" "trigger" {
  event_source_arn  = aws_dynamodb_table.positions_pnl.stream_arn
  function_name     = aws_lambda_function.pnl_aggregator.arn
  starting_position = "LATEST"
  batch_size        = 100
}