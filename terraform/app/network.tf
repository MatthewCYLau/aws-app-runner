resource "aws_vpc" "this" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = merge(
    local.common_tags,
    { Name = "aws-ecs-app-vpc-network-1" }
  )
}

resource "aws_subnet" "public" {
  count = 2
  # index 0 -> 10.0.0.0/24 | index 1 -> 10.0.1.0/24
  cidr_block              = cidrsubnet(aws_vpc.this.cidr_block, 8, count.index)
  availability_zone       = data.aws_availability_zones.available_zones.names[count.index]
  vpc_id                  = aws_vpc.this.id
  map_public_ip_on_launch = true

  tags = {
    Name                     = "AWS ECS App Public Subnet ${count.index + 1}"
    "kubernetes.io/role/elb" = "1"
  }
}

resource "aws_subnet" "private" {
  count = 4
  # index 10 -> 10.0.10.0/24
  # index 11 -> 10.0.11.0/24
  # index 12 -> 10.0.12.0/24
  # index 13 -> 10.0.13.0/24
  cidr_block              = cidrsubnet(aws_vpc.this.cidr_block, 8, count.index + 10)
  availability_zone       = data.aws_availability_zones.available_zones.names[count.index % 2]
  vpc_id                  = aws_vpc.this.id
  map_public_ip_on_launch = true

  tags = {
    Name                              = "AWS ECS App Private Subnet ${count.index + 1}"
    "kubernetes.io/role/internal-elb" = 1
  }
}

resource "aws_subnet" "rds" {
  count             = 2
  cidr_block        = cidrsubnet(aws_vpc.this.cidr_block, 8, count.index + 4)
  availability_zone = data.aws_availability_zones.available_zones.names[count.index]
  vpc_id            = aws_vpc.this.id

  tags = {
    Name = "AWS ECS App RDS Private Subnet ${count.index + 1}"
  }
}

resource "aws_subnet" "rds_public" {
  count             = 2
  cidr_block        = cidrsubnet(aws_vpc.this.cidr_block, 8, count.index + 6)
  availability_zone = data.aws_availability_zones.available_zones.names[count.index]
  vpc_id            = aws_vpc.this.id

  tags = {
    Name = "AWS ECS App RDS read replica public subnet ${count.index + 1}"
  }
}

resource "aws_internet_gateway" "gateway" {
  vpc_id = aws_vpc.this.id
}

/*
resource "aws_route" "internet_access" {
  route_table_id         = aws_vpc.this.main_route_table_id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.gateway.id
}
*/

resource "aws_route_table" "public" {
  count  = 2
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gateway.id
  }

  tags = {
    Name = "AWS ECS Public Route Table ${count.index + 1}"
  }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = element(aws_subnet.public.*.id, count.index)
  route_table_id = element(aws_route_table.public.*.id, count.index)
}

resource "aws_route_table_association" "rds_public" {
  count          = 2
  subnet_id      = element(aws_subnet.rds_public.*.id, count.index)
  route_table_id = element(aws_route_table.public.*.id, count.index)
}

resource "aws_eip" "gateway" {
  count      = 2
  domain     = "vpc"
  depends_on = [aws_internet_gateway.gateway]
}

resource "aws_nat_gateway" "gateway" {
  count         = 2
  subnet_id     = element(aws_subnet.public.*.id, count.index)
  allocation_id = element(aws_eip.gateway.*.id, count.index)
}

resource "aws_route_table" "private" {
  count  = 4
  vpc_id = aws_vpc.this.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = element(aws_nat_gateway.gateway.*.id, count.index)
  }

  tags = {
    Name = "AWS ECS Private Route Table ${count.index + 1}"
  }
}

resource "aws_route_table_association" "private" {
  count          = 4
  subnet_id      = element(aws_subnet.private.*.id, count.index)
  route_table_id = element(aws_route_table.private.*.id, count.index)
}

resource "aws_route_table" "rds" {
  count  = 2
  vpc_id = aws_vpc.this.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = element(aws_nat_gateway.gateway.*.id, count.index)
  }

  tags = {
    Name = "AWS ECS Private Route Table ${count.index + 1}"
  }
}

resource "aws_route_table_association" "rds" {
  count          = 2
  subnet_id      = element(aws_subnet.rds.*.id, count.index)
  route_table_id = element(aws_route_table.rds.*.id, count.index)
}

data "aws_region" "current" {}

resource "aws_vpc_endpoint" "s3_gateway" {
  vpc_id            = aws_vpc.this.id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"

  tags = merge(
    local.common_tags,
    { Name = "S3 gateway endpoint" }
  )
}

resource "aws_vpc_endpoint_route_table_association" "private_s3" {
  count           = 2
  vpc_endpoint_id = aws_vpc_endpoint.s3_gateway.id
  route_table_id  = element(aws_route_table.private.*.id, count.index)
}
