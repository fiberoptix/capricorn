# Capricorn Terraform Variables

variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "voltaic-cirrus-476620-h5"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-east1"
}

variable "cluster_name" {
  description = "GKE Cluster Name"
  type        = string
  default     = "capricorn-cluster"
}

