# AWS App Runner

Deploy a containerised application to AWS App Runner

## Generate SSH key pair

```bash
ssh-keygen -t ed25519 -f ~/.ssh/aws_app -C aws_app
```

## Connect to public EC2 instance

```
chmod 600 ~/.ssh/aws_app
ssh -i ~/.ssh/aws_app ec2-user@98.82.2.241
```

## Connect to RDS database

```
psql "host=$RDSHOST port=5432 dbname=apprunnerdb user=postgres_admin password=password"
```

## Install helm release

```
aws ecr get-login-password --region us-east-1 | helm registry login --username AWS --password-stdin 830663695860.dkr.ecr.us-east-1.amazonaws.com
helm upgrade --install aws-app-release \
            oci://830663695860.dkr.ecr.us-east-1.amazonaws.com/helm-chart \
            --namespace dev
```
