# =============================================================================
# Outputs
# =============================================================================

output "container_namespace_id" {
  description = "The ID of the container namespace"
  value       = local.container_namespace_id
}

output "registry_namespace_endpoint" {
  description = "The registry namespace endpoint"
  value       = data.scaleway_registry_namespace.main.endpoint
}

output "containers" {
  description = "Information about deployed containers"
  value = {
    for name, container in scaleway_container.services : name => {
      id             = container.id
      name           = container.name
      domain_name    = container.domain_name
      registry_image = container.registry_image
      status         = container.status
      region         = container.region
      privacy        = container.privacy
      port           = container.port
      min_scale      = container.min_scale
      max_scale      = container.max_scale
      memory_limit   = container.memory_limit
      cpu_limit      = container.cpu_limit
    }
  }
}

output "container_urls" {
  description = "URLs for accessing the deployed containers"
  value = {
    for name, container in scaleway_container.services : name => "https://${container.domain_name}"
  }
}

output "landing_url" {
  description = "URL for the landing page"
  value       = try("https://${scaleway_container.services["landing"].domain_name}", null)
}

output "backend_url" {
  description = "URL for the backend API"
  value       = try("https://${scaleway_container.services["backend"].domain_name}", null)
}

output "frontend_url" {
  description = "URL for the frontend application"
  value       = try("https://${scaleway_container.services["frontend"].domain_name}", null)
}

output "image_urls" {
  description = "Docker image URLs in the registry"
  value = {
    for name in keys(local.containers_to_deploy) : name => "${local.image_base}/${name}:${var.image_tag}"
  }
}
