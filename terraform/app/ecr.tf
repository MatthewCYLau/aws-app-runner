resource "aws_ecr_repository" "this" {
  name                 = "aws-app-runner"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = false
  }
  tags = merge(
    local.common_tags,
    { Name = "AWS ECS App private ECR" }
  )
}

resource "aws_ecr_repository" "client" {
  name                 = "streamlit-dashboard"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = false
  }
  tags = merge(
    local.common_tags,
    { Name = "Streamlit Dashboard private ECR" }
  )
}

resource "aws_ecr_repository" "helm_chart" {
  name                 = "helm-chart"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = false
  }
  tags = merge(
    local.common_tags,
    { Name = "App helm chart private ECR" }
  )
}
