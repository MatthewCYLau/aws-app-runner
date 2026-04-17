resource "aws_s3_bucket" "assets" {
  bucket = "aws-app-runner-assets"

  tags = merge(
    local.common_tags,
    { Name = "AWS App assets" }
  )
}

resource "aws_s3_bucket_public_access_block" "assets_access" {
  bucket                  = aws_s3_bucket.assets.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "assets_encryption" {
  bucket = aws_s3_bucket.assets.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}