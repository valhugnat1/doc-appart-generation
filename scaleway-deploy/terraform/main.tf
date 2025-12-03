# =============================================================================
# Scaleway Serverless Containers Deployment
# =============================================================================

# -----------------------------------------------------------------------------
# Data Sources - Registry Images
# -----------------------------------------------------------------------------

# Get registry namespace information
data "scaleway_registry_namespace" "main" {
  name = var.registry_namespace
}

# -----------------------------------------------------------------------------
# Container Namespace
# -----------------------------------------------------------------------------

# Option 1: Create a new container namespace
resource "scaleway_container_namespace" "main" {
  count       = var.create_container_namespace ? 1 : 0
  name        = var.container_namespace_name
  description = "Serverless container namespace for bail application"
  project_id  = var.project_id
  region      = var.region
}

locals {
  # Use created or existing namespace
  container_namespace_id = var.create_container_namespace ? scaleway_container_namespace.main[0].id : data.scaleway_container_namespace.existing[0].id
  
  # Build image URLs
  image_base = "${var.registry_endpoint}/${var.registry_namespace}"
  
  # Filter containers that should be deployed
  containers_to_deploy = {
    for name, config in var.containers : name => config if config.deploy
  }
}

# -----------------------------------------------------------------------------
# Serverless Containers
# -----------------------------------------------------------------------------

resource "scaleway_container" "services" {
  for_each = local.containers_to_deploy

  name         = each.key
  namespace_id = local.container_namespace_id
  description  = each.value.description

  # Image configuration
  registry_image = "${local.image_base}/${each.key}:${var.image_tag}"
  
  # Use deploy flag to trigger redeployment
  # Change this value to force a new deployment
  deploy = true

  # Port configuration
  port = each.value.port

  # Scaling configuration
  min_scale = each.value.min_scale
  max_scale = each.value.max_scale

  # Resource limits
  memory_limit = each.value.memory_limit
  cpu_limit    = each.value.cpu_limit

  # Runtime configuration
  timeout         = each.value.timeout
  max_concurrency = each.value.max_concurrency

  # Privacy setting
  privacy = each.value.privacy

  # Environment variables
  environment_variables = merge(
    each.value.environment_variables,
    each.key == "backend" ? var.backend_env_vars : {}
  )

  secret_environment_variables = merge(
    each.value.secret_environment_variables,
    each.key == "backend" ? var.backend_secret_env_vars : {}
  )

  # Health check configuration (optional)
  # http_option = "enabled"

  lifecycle {
    # Ignore changes to registry_sha256 to avoid unnecessary redeployments
    ignore_changes = [
      # Uncomment the following line if you want to manage deployments manually
      # registry_sha256,
    ]
  }
}

# -----------------------------------------------------------------------------
# Container Domains (Custom domains - optional)
# -----------------------------------------------------------------------------

# Uncomment and configure if you want to add custom domains
# resource "scaleway_container_domain" "landing" {
#   container_id = scaleway_container.services["landing"].id
#   hostname     = "www.yourdomain.com"
# }

# resource "scaleway_container_domain" "backend" {
#   container_id = scaleway_container.services["backend"].id
#   hostname     = "api.yourdomain.com"
# }

# resource "scaleway_container_domain" "frontend" {
#   container_id = scaleway_container.services["frontend"].id
#   hostname     = "app.yourdomain.com"
# }
