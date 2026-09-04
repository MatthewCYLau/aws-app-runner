resource "aws_kinesis_stream" "trade_stream" {
  name             = "trades-stream"
  retention_period = 24

  stream_mode_details {
    stream_mode = "ON_DEMAND"
  }

  tags = merge(
    local.common_tags,
    { Name = "AWS App assets" }
  )
}
