# =============================================================================
# Variables Configuration
# =============================================================================

variable "region" {
  description = "Scaleway region"
  type        = string
  default     = "fr-par"
}

variable "zone" {
  description = "Scaleway zone"
  type        = string
  default     = "fr-par-1"
}

variable "project_id" {
  description = "Scaleway project ID"
  type        = string
}

# Container Registry Configuration
variable "registry_namespace" {
  description = "Name of the container registry namespace"
  type        = string
  default     = "perso"
}

variable "registry_endpoint" {
  description = "Scaleway container registry endpoint"
  type        = string
  default     = "rg.fr-par.scw.cloud"
}

# Serverless Container Namespace
variable "container_namespace_id" {
  description = "Existing serverless container namespace ID"
  type        = string
  default     = "e10c8558-99b7-4f45-a136-554d47120af0"
}

variable "create_container_namespace" {
  description = "Whether to create a new container namespace or use existing one"
  type        = bool
  default     = false
}

variable "container_namespace_name" {
  description = "Name of the serverless container namespace (if creating new)"
  type        = string
  default     = "bail-app"
}

# Image Configuration
variable "image_tag" {
  description = "Docker image tag"
  type        = string
  default     = "latest"
}

# Container Resources Configuration
variable "containers" {
  description = "Container configurations"
  type = map(object({
    description     = string
    port            = number
    min_scale       = number
    max_scale       = number
    memory_limit    = number
    cpu_limit       = number
    timeout         = number
    max_concurrency = number
    privacy         = string
    deploy          = bool
    environment_variables = map(string)
    secret_environment_variables = map(string)
  }))
  default = {
    landing = {
      description     = "Landing page service"
      port            = 80
      min_scale       = 0
      max_scale       = 5
      memory_limit    = 256
      cpu_limit       = 140
      timeout         = 300
      max_concurrency = 50
      privacy         = "public"
      deploy          = true
      environment_variables        = {}
      secret_environment_variables = {}
    }
    backend = {
      description     = "FastAPI Backend service"
      port            = 8000
      min_scale       = 0
      max_scale       = 10
      memory_limit    = 512
      cpu_limit       = 280
      timeout         = 300
      max_concurrency = 50
      privacy         = "public"
      deploy          = true
      environment_variables        = {}
      secret_environment_variables = {}
    }
    frontend = {
      description     = "Vue.js Frontend service"
      port            = 80
      min_scale       = 0
      max_scale       = 5
      memory_limit    = 256
      cpu_limit       = 140
      timeout         = 300
      max_concurrency = 50
      privacy         = "public"
      deploy          = true
      environment_variables        = {}
      secret_environment_variables = {}
    }
  }
}

# Environment Variables (passed to containers)
variable "backend_env_vars" {
  description = "Environment variables for the backend container"
  type        = map(string)
  default     = {}
  sensitive   = false
}

variable "backend_secret_env_vars" {
  description = "Secret environment variables for the backend container"
  type        = map(string)
  default     = {}
  sensitive   = true
}

# =============================================================================
# Custom Domains Configuration
# =============================================================================

variable "enable_custom_domains" {
  description = "Enable custom domain configuration"
  type        = bool
  default     = false
}

variable "domains" {
  description = "Custom domain names for each service"
  type = object({
    landing  = string
    backend  = string
    frontend = string
  })
  default = {
    landing  = ""
    backend  = ""
    frontend = ""
  }
}

# =============================================================================
# Deployment Configuration
# =============================================================================

variable "force_redeploy" {
  description = "Change this value to force container redeployment (e.g., timestamp or version)"
  type        = string
  default     = "0"
}
