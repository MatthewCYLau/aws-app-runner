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