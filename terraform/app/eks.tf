module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "demo-eks-cluster"
  cluster_version = "1.32"

  vpc_id     = aws_vpc.this.id
  subnet_ids = [aws_subnet.private[2].id, aws_subnet.private[3].id]

  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  enable_cluster_creator_admin_permissions = true

  access_entries = {
    admin_user = {
      kubernetes_groups = []
      principal_arn     = "arn:aws:iam::830663695860:role/github-actions-terraform-role"

      policy_associations = {
        admin = {
          policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
          access_scope = {
            type = "cluster"
          }
        }
      }
    }
  }

  eks_managed_node_groups = {
    general = {
      min_size     = 1
      max_size     = 3
      desired_size = 2

      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"
    }

    dev_nodes = {
      min_size       = 1
      max_size       = 3
      desired_size   = 1
      instance_types = ["t3.medium"]

      labels = {
        np = "dev"
      }

      taints = [
        {
          key    = "np"
          value  = "dev"
          effect = "NO_SCHEDULE"
        }
      ]
    }

  }
  # enable_irsa = true
  cluster_addons = {
    eks-pod-identity-agent = {}
    amazon-cloudwatch-observability = {
      most_recent = true
    }
  }
}
