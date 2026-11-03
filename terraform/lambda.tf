
data "archive_file" "lambda_package" {
  type        = "zip"
  source_file = "${path.module}/lambda/app.py"
  output_path = "${path.module}/lambda.zip"
}

resource "aws_iam_role" "lambda_execution_role" {
  name = "${var.project_name}-lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "lambda_execution_policy" {
  name = "${var.project_name}-lambda-execution-policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadRawS3Objects"
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "${module.s3_buckets["raw"].bucket_arn}/*"
      },
      {
        Sid    = "WriteProcessedS3Objects"
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = [
          "${module.s3_buckets["validated"].bucket_arn}/*",
          "${module.s3_buckets["quarantine"].bucket_arn}/*"
        ]
      },
      {
        Sid    = "ConsumeIngestionQueue"
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ChangeMessageVisibility"
        ]
        Resource = aws_sqs_queue.ingestion_queue.arn
      },
      {
        Sid    = "WriteLambdaLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:*:log-group:/aws/lambda/${var.project_name}-ingestion:*"
      }
    ]
  })
}

resource "aws_lambda_function" "ingestion" {
  function_name = "${var.project_name}-ingestion"
  role          = aws_iam_role.lambda_execution_role.arn

  runtime = "python3.12"
  handler = "app.lambda_handler"

  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256

  timeout     = 60
  memory_size = 256

  environment {
    variables = {
      VALIDATED_BUCKET  = module.s3_buckets["validated"].bucket_name
      QUARANTINE_BUCKET = module.s3_buckets["quarantine"].bucket_name
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_execution_policy
  ]

  tags = {
    Purpose = "SQS-triggered data quality ingestion"
  }
}

resource "aws_lambda_event_source_mapping" "ingestion_sqs" {
  event_source_arn = aws_sqs_queue.ingestion_queue.arn
  function_name    = aws_lambda_function.ingestion.arn

  enabled                            = true
  batch_size                         = 5
  function_response_types            = ["ReportBatchItemFailures"]
  maximum_batching_window_in_seconds = 5
}
