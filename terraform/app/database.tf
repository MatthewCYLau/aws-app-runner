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

  db_subnet_group_name   = aws_db_subnet_group.public_group.name
  vpc_security_group_ids = [aws_security_group.rds_public_sg.id]

  publicly_accessible = true
}