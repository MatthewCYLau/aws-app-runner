resource "aws_vpc" "this" {
  cidr_block = "10.0.0.0/16"
  tags = merge(
    local.common_tags,
    Name = "app-runner-vpc-network-1"
  )
}