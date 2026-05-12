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
