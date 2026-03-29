resource "aws_vpc" "this" {
  name = "app-runner-vpc-network-1"
  cidr_block = "10.0.0.0/16"
  tags = merge(
    local.common_tags,
  )
}