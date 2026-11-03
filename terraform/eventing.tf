
# ==========================================
# 1. SQS Dead Letter Queue
# ==========================================

resource "aws_sqs_queue" "ingestion_dlq" {
  name                      = "${var.project_name}-ingestion-dlq"
  message_retention_seconds = 1209600

  sqs_managed_sse_enabled = true

  tags = {
    Purpose = "Failed ingestion messages"
  }
}

# ==========================================
# 2. Main Ingestion Queue
# ==========================================

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

# ==========================================
# 3. Enable S3 EventBridge Notifications
# ==========================================

resource "aws_s3_bucket_notification" "raw_eventbridge" {
  bucket = module.s3_buckets["raw"].bucket_name

  eventbridge = true
}

# ==========================================
# 4. EventBridge Rule
# ==========================================

resource "aws_cloudwatch_event_rule" "s3_object_created" {
  name = "${var.project_name}-s3-object-created"

  event_pattern = jsonencode({
    source = ["aws.s3"]

    detail-type = ["Object Created"]

    detail = {
      bucket = {
        name = [
          module.s3_buckets["raw"].bucket_name
        ]
      }
    }
  })
}

# ==========================================
# 5. EventBridge Target - SQS
# ==========================================

resource "aws_cloudwatch_event_target" "sqs_target" {
  rule      = aws_cloudwatch_event_rule.s3_object_created.name
  target_id = "SendToIngestionQueue"
  arn       = aws_sqs_queue.ingestion_queue.arn
}

# ==========================================
# 6. Allow EventBridge to Send SQS Messages
# ==========================================

resource "aws_sqs_queue_policy" "allow_eventbridge" {
  queue_url = aws_sqs_queue.ingestion_queue.url

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Effect = "Allow"

      Principal = {
        Service = "events.amazonaws.com"
      }

      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.ingestion_queue.arn

      Condition = {
        ArnEquals = {
          "aws:SourceArn" = aws_cloudwatch_event_rule.s3_object_created.arn
        }
      }
    }]
  })
}
