resource "aws_dynamodb_table" "stock_positions" {
  name         = "stock_trading_positions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "StockSymbol"
  range_key    = "Timestamp"

  attribute {
    name = "StockSymbol"
    type = "S"
  }

  attribute {
    name = "Timestamp"
    type = "N"
  }

  tags = merge(
    local.common_tags,
    { Name = "AWS App Dynamo DB" }
  )
}