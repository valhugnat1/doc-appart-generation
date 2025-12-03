# =============================================================================
# Data Sources
# =============================================================================

# Fetch container namespace information (when using existing namespace)
data "scaleway_container_namespace" "existing" {
  count        = var.create_container_namespace ? 0 : 1
  namespace_id = var.container_namespace_id
  region       = var.region
}

# Optional: Fetch registry image information for each service
# This can be used to verify images exist before deployment

# data "scaleway_registry_image" "landing" {
#   name         = "landing"
#   namespace_id = data.scaleway_registry_namespace.main.id
#   tag          = var.image_tag
# }

# data "scaleway_registry_image" "backend" {
#   name         = "backend"
#   namespace_id = data.scaleway_registry_namespace.main.id
#   tag          = var.image_tag
# }

# data "scaleway_registry_image" "frontend" {
#   name         = "frontend"
#   namespace_id = data.scaleway_registry_namespace.main.id
#   tag          = var.image_tag
# }
