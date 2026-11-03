resource "aws_sqs_queue" "ingestion_dlq" {
  name                      = "${var.project_name}-ingestion-dlq"
  message_retention_seconds = 1209600

  sqs_managed_sse_enabled = true

  tags = {
    Purpose = "Failed ingestion messages"
  }
}

resource "aws_sqs_queue" "ingestion_queue" {
  name = "${var.project_name}-ingestion-queue"

  visibility_timeout_seconds = 120
  message_retention_seconds  = 345600

  receive_wait_time_seconds = 20
  sqs_managed_sse_enabled   = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.ingestion_dlq.arn
    maxReceiveCount     = 5
  })

  tags = {
    Purpose = "Incoming dataset events"
  }
}

resource "aws_s3_bucket_notification" "raw_eventbridge" {
  bucket = module.s3_buckets["raw"].bucket_name

  eventbridge = true
}