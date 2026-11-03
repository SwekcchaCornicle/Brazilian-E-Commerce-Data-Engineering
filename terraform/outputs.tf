output "s3_bucket_names" {
  description = "All project S3 buckets"

  value = {
    for name, bucket in module.s3_buckets :
    name => bucket.bucket_name
  }
}

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