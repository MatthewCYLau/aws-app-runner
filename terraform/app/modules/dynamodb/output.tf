output "dynamodb_table_arn" {
  value = aws_dynamodb_table.this.arn
}

output "dynamodb_table_stream_arn" {
  value = aws_dynamodb_table.this.stream_arn
}