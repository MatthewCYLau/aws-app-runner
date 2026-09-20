output "emr_serverless_application_id" {
  value       = aws_emrserverless_application.spark_app.id
  description = "The ID of the created EMR Serverless Application"
}

output "emr_serverless_application_arn" {
  value       = aws_emrserverless_application.spark_app.arn
  description = "The ARN of the created EMR Serverless Application"
}

output "emr_execution_role_arn" {
  value       = aws_iam_role.emr_serverless_job_role.arn
  description = "IAM Role ARN to execute EMR jobs"
}

output "s3_bucket_name" {
  value       = aws_s3_bucket.emr_data_lake.bucket
  description = "Data Lake bucket created for PySpark scripts and data"
}
