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
    each.key == "backend" ? var.backend_env_vars : {},
    { "FORCE_REDEPLOY" = var.force_redeploy }
  )

  secret_environment_variables = merge(
    each.value.secret_environment_variables,
    each.key == "backend" ? var.backend_secret_env_vars : {}
  )
}

# -----------------------------------------------------------------------------
# Container Domains (Custom domains)
# -----------------------------------------------------------------------------

# Landing page domain: outil-immo.fr (root domain)
resource "scaleway_container_domain" "landing" {
  count        = var.enable_custom_domains && var.domains.landing != "" ? 1 : 0
  container_id = scaleway_container.services["landing"].id
  hostname     = var.domains.landing
}

# Backend API domain: api.outil-immo.fr
resource "scaleway_container_domain" "backend" {
  count        = var.enable_custom_domains && var.domains.backend != "" ? 1 : 0
  container_id = scaleway_container.services["backend"].id
  hostname     = var.domains.backend
}

# Frontend app domain: app.outil-immo.fr
resource "scaleway_container_domain" "frontend" {
  count        = var.enable_custom_domains && var.domains.frontend != "" ? 1 : 0
  container_id = scaleway_container.services["frontend"].id
  hostname     = var.domains.frontend
}
