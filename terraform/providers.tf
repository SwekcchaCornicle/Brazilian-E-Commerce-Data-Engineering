provider "aws" {
  region  = var.aws_region
  profile = "admin"

  default_tags {
    tags = {
      Project     = "EventDrivenDataQuality"
      Environment = "Development"
      ManagedBy   = "Terraform"
    }
  }
}