data "aws_iam_policy_document" "rds_iam_auth" {
  statement {
    actions = ["rds-db:connect"]
    effect  = "Allow"
    resources = [
      "${aws_db_instance.postgres.arn}/iam_user"
    ]
  }
}

resource "aws_iam_policy" "rds_policy" {
  name   = "RDS_IAM_Auth_Policy"
  policy = data.aws_iam_policy_document.rds_iam_auth.json
}

resource "aws_iam_role" "apprunner_ecr_access" {
  name = "apprunner-ecr-access-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "build.apprunner.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "apprunner_ecr_access_policy" {
  role       = aws_iam_role.apprunner_ecr_access.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}