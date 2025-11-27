# Capricorn GCP Infrastructure
# Terraform configuration for GKE Autopilot cluster

terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Remote state in GCS (create bucket first, then uncomment)
  # backend "gcs" {
  #   bucket = "capricorn-terraform-state"
  #   prefix = "terraform/state"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# GKE Autopilot Cluster
resource "google_container_cluster" "capricorn" {
  name     = var.cluster_name
  location = var.region

  # Autopilot mode - Google manages nodes
  enable_autopilot = true

  # Network config (using default VPC)
  network    = "default"
  subnetwork = "default"

  # Release channel for auto-updates
  release_channel {
    channel = "REGULAR"
  }

  # Deletion protection (set to false for easy teardown during dev)
  deletion_protection = false
}

