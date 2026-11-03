# --------------------------------------------------
# Upload Glue ETL script to S3
# --------------------------------------------------

resource "aws_s3_object" "customer_etl_script" {
  bucket       = module.s3_buckets["curated"].bucket_name
  key          = "scripts/customer_etl.py"
  source       = "${path.module}/scripts/customer_etl.py"
  etag         = filemd5("${path.module}/scripts/customer_etl.py")
  content_type = "text/x-python"
}

# --------------------------------------------------
# Dedicated Glue ETL IAM Role
# --------------------------------------------------

resource "aws_iam_role" "glue_etl_role" {
  name = "${var.project_name}-glue-etl-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Project = var.project_name
    Service = "AWSGlueETL"
  }
}

resource "aws_iam_role_policy_attachment" "glue_etl_service_role" {
  role       = aws_iam_role.glue_etl_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# --------------------------------------------------
# S3 Permissions for Glue ETL
# --------------------------------------------------

resource "aws_iam_role_policy" "glue_etl_s3_access" {
  name = "${var.project_name}-glue-etl-s3-access"
  role = aws_iam_role.glue_etl_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadValidatedData"
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          module.s3_buckets["validated"].bucket_arn
        ]
        Condition = {
          StringLike = {
            "s3:prefix" = ["processed", "processed/*"]
          }
        }
      },
      {
        Sid    = "ReadValidatedObjects"
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = [
          "${module.s3_buckets["validated"].bucket_arn}/processed/*"
        ]
      },
      {
        Sid    = "AccessCuratedBucket"
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          module.s3_buckets["curated"].bucket_arn
        ]
      },
      {
        Sid    = "ReadETLScript"
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = [
          "${module.s3_buckets["curated"].bucket_arn}/scripts/customer_etl.py"
        ]
      },
      {
        Sid    = "WriteCuratedData"
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:AbortMultipartUpload",
          "s3:ListMultipartUploadParts"
        ]
        Resource = [
          "${module.s3_buckets["curated"].bucket_arn}/customer/*"
        ]
      }
    ]
  })
}

# --------------------------------------------------
# AWS Glue Spark ETL Job
# --------------------------------------------------

resource "aws_glue_job" "customer_etl" {
  name     = "${var.project_name}-customer-etl"
  role_arn = aws_iam_role.glue_etl_role.arn

  glue_version = "4.0"

  command {
    name            = "glueetl"
    script_location = "s3://${module.s3_buckets["curated"].bucket_name}/${aws_s3_object.customer_etl_script.key}"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--INPUT_PATH"                       = "s3://${module.s3_buckets["validated"].bucket_name}/processed/"
    "--OUTPUT_PATH"                      = "s3://${module.s3_buckets["curated"].bucket_name}/customer/"
    "--enable-metrics"                   = "true"
    "--enable-continuous-cloudwatch-log" = "true"
  }

  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 30
  max_retries       = 0

  tags = {
    Project = var.project_name
    Dataset = "customer"
  }

  depends_on = [
    aws_iam_role_policy_attachment.glue_etl_service_role,
    aws_iam_role_policy.glue_etl_s3_access,
    aws_s3_object.customer_etl_script
  ]
}
