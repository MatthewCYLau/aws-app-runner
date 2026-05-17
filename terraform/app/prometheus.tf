/*
resource "aws_prometheus_workspace" "this" {
  alias = "eks-amp-workspace"
}

resource "aws_prometheus_scraper" "eks_scraper" {
  source {
    eks {
      cluster_arn = module.eks.cluster_arn
      subnet_ids  = [aws_subnet.private[2].id, aws_subnet.private[3].id]
    }
  }

  destination {
    amp {
      workspace_arn = aws_prometheus_workspace.this.arn
    }
  }

  scrape_configuration = <<EOF
global:
  scrape_interval: 30s
scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
EOF

  depends_on = [module.eks]
}
*/
