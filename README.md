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
            --version 4.0.0 \
            --namespace dev \
            -f ./values.yaml
```

## Prometheus source

```
http://prometheus-server.prometheus.svc.cluster.local:80
```

## Port forward and access EKS

```
aws eks update-kubeconfig --region us-east-1 --name demo-eks-cluster
aws ssm start-session --target i-02736c1f071f9031b --document-name AWS-StartPortForwardingSession --parameters '{"portNumber":["3128"],"localPortNumber":["3128"]}'
export HTTPS_PROXY=http://localhost:3128
export HTTP_PROXY=http://localhost:3128
kubectl get nodes
```
