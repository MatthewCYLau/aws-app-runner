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
  backup_retention_period             = 7
  backup_window                       = "03:00-04:00"
  monitoring_interval                 = 60
  monitoring_role_arn                 = aws_iam_role.rds_enhanced_monitoring.arn

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

resource "null_resource" "db_setup" {

  triggers = {
    rds_endpoint = aws_db_instance.postgres.endpoint
  }

  connection {
    type        = "ssh"
    user        = "ec2-user"
    private_key = file(var.private_key_path)
    host        = aws_instance.compute_instance.public_ip
  }

  provisioner "remote-exec" {
    inline = [
      "export PGPASSWORD='${var.db_password}'",
      <<-EOT
      psql -h ${aws_db_instance.postgres.address} \
           -U ${aws_db_instance.postgres.username} \
           -d ${aws_db_instance.postgres.db_name} <<EOF
      CREATE USER iam_user;
      GRANT rds_iam TO iam_user;
      GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO iam_user;
      GRANT USAGE, CREATE ON SCHEMA public TO iam_user;
      EOF
      EOT
    ]
  }

  depends_on = [aws_db_instance.postgres, aws_instance.compute_instance]
}
output "db_hostname" {
  value       = aws_db_instance.postgres.address
  description = "PostgreSQL database hostname"
}

resource "aws_db_instance" "read_replica" {
  identifier          = "postgres-read-replica"
  replicate_source_db = aws_db_instance.postgres.arn
  instance_class      = "db.t3.micro"

  db_subnet_group_name   = aws_db_subnet_group.public_read_replica.name
  vpc_security_group_ids = [aws_security_group.replica_sg.id]
  publicly_accessible    = true
  skip_final_snapshot    = true

  tags = merge(
    local.common_tags,
    { Name = "AWS ECS App PostgreSQL DB public read replica" }
  )
}

resource "aws_db_subnet_group" "public_read_replica" {
  name        = "rds-public-read-replica-subnets-group"
  description = "Public subnet group for RDS read replica"
  subnet_ids  = aws_subnet.rds_public.*.id

  tags = {
    Name = "RDS Public Replica Subnets Group"
  }
}

output "read_only_db_hostname" {
  value       = aws_db_instance.read_replica.address
  description = "PostgreSQL read-only database hostname"
}
