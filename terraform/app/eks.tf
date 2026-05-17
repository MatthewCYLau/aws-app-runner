/*
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

  eks_managed_node_groups = {
    general = {
      min_size     = 1
      max_size     = 3
      desired_size = 2

      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"
    }
  }
  # enable_irsa = true
  cluster_addons = {
    eks-pod-identity-agent = {}
  }
}
*/
