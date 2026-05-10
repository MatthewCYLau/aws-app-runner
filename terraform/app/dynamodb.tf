/*
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

  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

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

resource "aws_dynamodb_table" "stocks_pnl" {
  name         = "stocks_pnl"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "StockSymbol" # partition key

  attribute {
    name = "StockSymbol"
    type = "S"
  }

  tags = merge(
    local.common_tags,
    { Name = "AWS App Dynamo DB" }
  )
}
*/

module "stock_positions" {
  source     = "./modules/dynamodb"
  table_name = "stock_trading_positions"
  hash_key   = "PositionId"
  range_key  = "CreatedAt"
  attributes = [
    { name = "PositionId", type = "S" },
    { name = "CreatedAt", type = "S" }
  ]
  common_tags = local.common_tags
}

module "positions_pnl" {
  source         = "./modules/dynamodb"
  table_name     = "positions_pnl"
  hash_key       = "PositionId"
  range_key      = "CreatedAt"
  stream_enabled = true
  attributes = [
    { name = "PositionId", type = "S" },
    { name = "CreatedAt", type = "S" }
  ]
  common_tags = local.common_tags
}

module "stocks_pnl" {
  source     = "./modules/dynamodb"
  table_name = "stocks_pnl"
  hash_key   = "StockSymbol"
  attributes = [
    { name = "StockSymbol", type = "S" }
  ]
  common_tags = local.common_tags
}
