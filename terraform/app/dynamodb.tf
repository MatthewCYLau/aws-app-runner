resource "aws_dynamodb_table" "stock_positions" {
  name         = "stock_trading_positions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PositionId" # partition key
  range_key    = "CreatedAt"  # sort key

  attribute {
    name = "PositionId"
    type = "S"
  }

  attribute {
    name = "CreatedAt"
    type = "S"
  }

  tags = merge(
    local.common_tags,
    { Name = "AWS App Dynamo DB" }
  )
}

resource "aws_dynamodb_table" "positions_pnl" {
  name         = "positions_pnl"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PositionId" # partition key
  range_key    = "CreatedAt"  # sort key

  attribute {
    name = "PositionId"
    type = "S"
  }

  attribute {
    name = "CreatedAt"
    type = "S"
  }

  tags = merge(
    local.common_tags,
    { Name = "AWS App Dynamo DB" }
  )
}
