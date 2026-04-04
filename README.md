# AWS App Runner

Deploy a containerised application to AWS App Runner

## Generate SSH key pair

```bash
ssh-keygen -t ed25519 -f ~/.ssh/aws_app -C aws_app
```

## Connect to public EC2 instance

```
chmod 600 ~/.ssh/aws_app
ssh -i ~/.ssh/aws_app ec2-user@44.212.24.112
```

## Connect to RDS database

```
psql "host=$RDSHOST port=5432 dbname=apprunnerdb user=postgres_admin password=<PASSWORD>"
```
