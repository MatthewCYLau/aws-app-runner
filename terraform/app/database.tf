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
  multi_az                            = true
  db_subnet_group_name                = aws_db_subnet_group.postgres.name
  vpc_security_group_ids              = [aws_security_group.rds_sg.id]

  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_enhanced_monitoring.arn

  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  tags = merge(
    local.common_tags,
    { Name = "AWS ECS App PostgreSQL DB" }
  )
}

resource "aws_db_subnet_group" "postgres" {
  name       = "postgres-private-subnets-group"
  subnet_ids = aws_subnet.rds.*.id

  tags = merge(
    local.common_tags,
    { Name = "PostgreSQL DB private subnet group" }
  )
}


output "db_hostname" {
  value       = aws_db_instance.postgres.address
  description = "PostgreSQL database hostname"
}
