# Optional Glue Crawler.
# Keep disabled while the AWS account returns CreateCrawler AccessDenied.
# Enable only after AWS confirms crawler access: -var="enable_glue_crawler=true"

variable "enable_glue_crawler" {
  description = "Create the optional Glue crawler when AWS account access is available."
  type        = bool
  default     = false
}

resource "aws_glue_crawler" "validated_data_crawler" {
  count         = var.enable_glue_crawler ? 1 : 0
  name          = "${var.project_name}-validated-crawler"
  database_name = aws_glue_catalog_database.dq_database.name
  role          = aws_iam_role.glue_crawler_role.arn
  description   = "Discovers customer JSON schema in the validated S3 zone"

  s3_target {
    path = "s3://${module.s3_buckets["validated"].bucket_name}/processed/"
  }

  recrawl_policy {
    recrawl_behavior = "CRAWL_EVERYTHING"
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "DEPRECATE_IN_DATABASE"
  }

  depends_on = [
    aws_iam_role_policy_attachment.glue_service_role,
    aws_iam_role_policy.glue_s3_read
  ]

  tags = {
    Project = var.project_name
    Dataset = "customer"
  }
}

output "optional_glue_crawler_name" {
  description = "Crawler name when enable_glue_crawler is true; otherwise null."
  value       = var.enable_glue_crawler ? aws_glue_crawler.validated_data_crawler[0].name : null
}
