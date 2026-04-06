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
