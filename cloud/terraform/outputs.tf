# Capricorn Terraform Outputs

output "cluster_name" {
  description = "GKE Cluster Name"
  value       = google_container_cluster.capricorn.name
}

output "cluster_endpoint" {
  description = "GKE Cluster Endpoint"
  value       = google_container_cluster.capricorn.endpoint
  sensitive   = true
}

output "cluster_location" {
  description = "GKE Cluster Location"
  value       = google_container_cluster.capricorn.location
}

output "kubectl_command" {
  description = "Command to configure kubectl"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.capricorn.name} --region ${google_container_cluster.capricorn.location} --project ${var.project_id}"
}

