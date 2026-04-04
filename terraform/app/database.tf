resource "aws_db_instance" "postgres" {
  allocated_storage                   = 20
  engine                              = "postgres"
  engine_version                      = "18.3"
  instance_class                      = "db.t3.micro"
  db_name                             = "apprunnerdb"
  username                            = "postgres_admin"
  password                            = var.db_password
  iam_database_authentication_enabled = true
  skip_final_snapshot                 = true

  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
}

resource "aws_db_subnet_group" "postgres" {
  name       = "postgres-private-subnets-group"
  subnet_ids = aws_subnet.rds.*.id

  tags = {
    Name = "PostgreSQL DB private subnet group"
  }
}
