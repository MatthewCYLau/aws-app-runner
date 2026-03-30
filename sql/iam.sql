-- Create a user that matches the name in your IAM policy
CREATE USER iam_user;

-- Grant the special AWS role that allows IAM token login
GRANT rds_iam TO iam_user;