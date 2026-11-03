# --------------------------------------------------
# AWS Glue Data Catalog
# --------------------------------------------------

resource "aws_glue_catalog_database" "dq_database" {
  name        = "dq_platform"
  description = "Data quality platform metadata catalog"
}

# --------------------------------------------------
# IAM Role for AWS Glue Crawler
# --------------------------------------------------

resource "aws_iam_role" "glue_crawler_role" {
  name = "${var.project_name}-glue-crawler-role"

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
    Service = "AWSGlue"
  }
}

resource "aws_iam_role_policy_attachment" "glue_service_role" {
  role       = aws_iam_role.glue_crawler_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy" "glue_s3_read" {
  name = "${var.project_name}-glue-s3-read"
  role = aws_iam_role.glue_crawler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          module.s3_buckets["validated"].bucket_arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = [
          "${module.s3_buckets["validated"].bucket_arn}/processed/*"
        ]
      }
    ]
  })
}
