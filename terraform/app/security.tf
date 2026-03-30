resource "aws_db_subnet_group" "public_group" {
  name       = "postgres-public-subnets-group"
  subnet_ids = aws_subnet.public.*.id

  tags = {
    Name = "PostgreSQL DB subnet group"
  }
}

resource "aws_security_group" "rds_public_sg" {
  name        = "rds-public-sg"
  vpc_id      = aws_vpc.this.id
  description = "Allow inbound access from internet"

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}