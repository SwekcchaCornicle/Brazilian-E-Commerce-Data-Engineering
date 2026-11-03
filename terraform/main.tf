
# Generate a unique suffix for globally unique bucket names
resource "random_id" "suffix" {
  byte_length = 4
}

locals {
  bucket_purposes = {
    raw        = "incoming"
    schemas    = "schema-registry"
    validated  = "validated-data"
    quarantine = "invalid-data"
    reports    = "quality-reports"
  }
}

module "s3_buckets" {
  source   = "./modules/s3"
  for_each = local.bucket_purposes

  bucket_name = "${var.project_name}-${each.key}-${random_id.suffix.hex}"

  tags = {
    Project  = var.project_name
    DataZone = each.value
  }
}
