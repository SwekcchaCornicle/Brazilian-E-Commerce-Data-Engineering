output "ingestion_queue_url" {
  value = aws_sqs_queue.ingestion_queue.url
}

output "ingestion_queue_arn" {
  value = aws_sqs_queue.ingestion_queue.arn
}

output "ingestion_dlq_url" {
  value = aws_sqs_queue.ingestion_dlq.url
}

output "eventbridge_rule_arn" {
  value = aws_cloudwatch_event_rule.s3_object_created.arn
}

output "glue_database_name" {
  value = aws_glue_catalog_database.dq_database.name
}

output "glue_crawler_role_arn" {
  value = aws_iam_role.glue_crawler_role.arn
}

output "glue_etl_job_name" {
  value = aws_glue_job.customer_etl.name
}

output "glue_etl_role_arn" {
  value = aws_iam_role.glue_etl_role.arn
}

output "curated_bucket_name" {
  value = module.s3_buckets["curated"].bucket_name
}