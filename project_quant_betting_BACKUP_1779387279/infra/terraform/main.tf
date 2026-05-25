# Basic Terraform configuration for deploying the betting bot infrastructure
# Assumes AWS as the cloud provider for demonstration

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-west-1" # Ideal for lowest latency to European betting exchanges
}

# Network
resource "aws_vpc" "vbq_vpc" {
  cidr_block = "10.0.0.0/16"
  enable_dns_hostnames = true
  
  tags = {
    Name = "VBQ-VPC"
    Environment = "Production"
  }
}

# ECS Cluster for API and Workers
resource "aws_ecs_cluster" "vbq_cluster" {
  name = "vbq-cluster"
}

# ElastiCache Redis for feature caching and latency-critical state
resource "aws_elasticache_cluster" "vbq_redis" {
  cluster_id           = "vbq-redis"
  engine               = "redis"
  node_type            = "cache.t4g.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6379
}

# RDS PostgreSQL for historical data and ledger
resource "aws_db_instance" "vbq_db" {
  identifier           = "vbq-postgres"
  allocated_storage    = 50
  engine               = "postgres"
  engine_version       = "15.3"
  instance_class       = "db.t4g.micro"
  username             = "postgres"
  password             = "changeme_in_secrets_manager"
  skip_final_snapshot  = true
}

# S3 for Feature Store Parquet files and ML Models
resource "aws_s3_bucket" "vbq_data_lake" {
  bucket = "vbq-quant-data-lake-eu-west-1"
}
